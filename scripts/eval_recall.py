"""Golden-set evaluation for retrieval recall, the scope gate, and intent routing.

Uses only embeddings and deterministic rules (no answer model), so it runs in
seconds and is safe as a regression gate.  Chapter labels live in
scripts/golden_set.json and were verified against the real textbook TOC.

Usage:
    python -X utf8 scripts/eval_recall.py [--library data/library/textbooks.sqlite3]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core import config
from core.engine_v2 import StructuredQAEngine, classify_route

GOLDEN_PATH = Path(__file__).resolve().parent / "golden_set.json"

# 回归门槛：超过任何一项即退出码 1。
THRESHOLDS = {
    "false_refusal_max": 0.10,   # 库内问题被误判离题的比例
    "false_accept_max": 0.15,    # 离题问题被放行的比例
    "top1_chapter_min": 0.60,    # 首个片段落在标注章节的比例
    "top3_chapter_min": 0.80,    # 前三个片段覆盖标注章节的比例
    "compare_pair_min": 0.60,    # 对比题双边材料齐备的比例
}


def chapter_number(chunk) -> int | None:
    text = f"{chunk.chapter or ''}"
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None


def top_chapters(contexts, count: int) -> list[int | None]:
    return [chapter_number(chunk) for chunk in contexts[:count]]


def main() -> int:
    parser = argparse.ArgumentParser(description="黄金集检索评测（不需要回答模型）")
    parser.add_argument("--library", type=Path, default=config.LIBRARY_DB)
    parser.add_argument("--json", action="store_true", help="只输出 JSON 摘要")
    args = parser.parse_args()

    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    engine = StructuredQAEngine(library_path=args.library)
    store = engine.library
    print(f"[INFO] 教材库：{args.library}")
    print(f"[INFO] 向量模型：{store.embedding_model or '(无向量)'}  片段：{len(store.chunks)}")

    rows: list[dict] = []

    def record(group: str, question: str, passed: bool, detail: str) -> None:
        rows.append({"group": group, "q": question, "ok": passed, "detail": detail})
        mark = "PASS" if passed else "FAIL"
        if not args.json:
            print(f"[{mark}] {group:8s} {question}  {detail}")

    # 1) 普通知识点问答：不应拒答，且片段应落在标注章节
    for case in golden["qa"]:
        prepared = engine.prepare(case["q"])
        refused = bool(prepared.out_of_scope or not prepared.contexts)
        if refused:
            record("qa", case["q"], False, "被误拒答")
            continue
        chapters = top_chapters(prepared.contexts, 3)
        top1 = chapters[0] in case["chapters"]
        top3 = any(value in case["chapters"] for value in chapters)
        record("qa", case["q"], top1, f"top1={chapters[:1]} top3={chapters} 期望={case['chapters']}")
        rows[-1]["top1"] = top1
        rows[-1]["top3"] = top3

    # 2) 定位类：不应拒答，首个位置应在标注章节
    for case in golden["locate"]:
        prepared = engine.prepare(case["q"])
        refused = bool(prepared.out_of_scope or not prepared.contexts)
        if refused:
            record("locate", case["q"], False, "被误拒答")
            continue
        chapters = top_chapters(prepared.contexts, 1)
        passed = chapters[0] in case["chapters"]
        record("locate", case["q"], passed, f"top1={chapters} 期望={case['chapters']}")

    # 3) 对比类：不应拒答，且双边章节材料都要进入候选
    for case in golden["compare"]:
        prepared = engine.prepare(case["q"])
        refused = bool(prepared.out_of_scope or not prepared.contexts)
        if refused:
            record("compare", case["q"], False, "被误拒答")
            continue
        present = set(top_chapters(prepared.contexts, 7))
        missing = [value for value in case["pair"] if value not in present]
        passed = not missing
        record("compare", case["q"], passed,
               f"候选章节={sorted(v for v in present if v is not None)} 缺失={missing}")

    # 4) 离题类：必须拒答
    for question in golden["oos"]:
        prepared = engine.prepare(question)
        passed = bool(prepared.out_of_scope or not prepared.contexts)
        record("oos", question, passed,
               "正确拒答" if passed else f"被误放行(route={prepared.route}, conf={prepared.confidence})")

    # 5) 路由与确定性入口
    for case in golden["routes"]:
        route = classify_route(case["q"])
        if route != case["route"]:
            record("routes", case["q"], False, f"路由={route} 期望={case['route']}")
            continue
        prepared = engine.prepare(case["q"])
        ok = bool(prepared.contexts or prepared.chapters) and not prepared.out_of_scope
        record("routes", case["q"], ok, f"路由={route} 材料数={len(prepared.contexts)}")

    # 汇总
    def rate(group: str, key: str | None = None) -> float:
        subset = [row for row in rows if row["group"] == group]
        if key:
            subset = [row for row in subset if key in row]
        if not subset:
            return 1.0
        return sum(1 for row in subset if row["ok"]) / len(subset)

    qa_rows = [row for row in rows if row["group"] in {"qa", "locate"}]
    in_scope_total = len(qa_rows) + len(golden["compare"])
    in_scope_refused = sum(1 for row in rows if row["group"] in {"qa", "locate", "compare"} and row["detail"] == "被误拒答")
    false_refusal = in_scope_refused / max(1, in_scope_total)
    oos_rows = [row for row in rows if row["group"] == "oos"]
    false_accept = sum(1 for row in oos_rows if not row["ok"]) / max(1, len(oos_rows))
    top1 = sum(1 for row in rows if row["group"] in {"qa", "locate"} and row.get("top1")) / max(1, len([r for r in rows if r["group"] in {"qa", "locate"}]))
    top3 = sum(1 for row in rows if row["group"] == "qa" and row.get("top3")) / max(1, len([r for r in rows if r["group"] == "qa"]))
    pair = rate("compare")

    summary = {
        "library": str(args.library),
        "embedding_model": store.embedding_model,
        "chunks": len(store.chunks),
        "false_refusal": round(false_refusal, 3),
        "false_accept": round(false_accept, 3),
        "top1_chapter_hit": round(top1, 3),
        "top3_chapter_hit": round(top3, 3),
        "compare_pair_covered": round(pair, 3),
        "thresholds": THRESHOLDS,
        "failed_cases": [row for row in rows if not row["ok"]],
    }
    ok = (
        false_refusal <= THRESHOLDS["false_refusal_max"]
        and false_accept <= THRESHOLDS["false_accept_max"]
        and top1 >= THRESHOLDS["top1_chapter_min"]
        and top3 >= THRESHOLDS["top3_chapter_min"]
        and pair >= THRESHOLDS["compare_pair_min"]
    )
    summary["verdict"] = "PASS" if ok else "FAIL"
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("\n===== 汇总 =====")
        for key in ("false_refusal", "false_accept", "top1_chapter_hit", "top3_chapter_hit", "compare_pair_covered"):
            print(f"  {key}: {summary[key]}")
        print(f"  判定: {summary['verdict']}  (失败 {len(summary['failed_cases'])} 例)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
