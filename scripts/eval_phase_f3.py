"""Phase F.3 semantic citation verifier evaluation (v3.5).

Quantitatively compares F.2 deterministic Layer-1 (``DeterministicCitationVerifier``)
against a candidate L2 Local Ollama Judge on ``eval/phase_f3_semantic_challenge.json``.

This is an EVALUATION / DECISION script, not a production pipeline change.  The
LLM judge is called as a standalone probe only; nothing here wires it into
``engine_v2.py`` or changes any product behavior.

Usage:
    python scripts/eval_phase_f3.py --mode l1
    python scripts/eval_phase_f3.py --mode l2 [--model qwen2.5:7b]
    python scripts/eval_phase_f3.py --mode both

Metrics reported: accuracy, supported/unsupported precision & recall,
uncertain rate, false-support rate, false-reject rate, and — crucially for the
citation scenario — how well L2 resolves the cases L1 leaves UNCERTAIN.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.citation_verifier import DeterministicCitationVerifier  # noqa: E402
from core.ollama_http import OllamaClient, OllamaError  # noqa: E402

CHALLENGE = ROOT_DIR / "eval" / "phase_f3_semantic_challenge.json"

# --- frozen judge contract -------------------------------------------------
JUDGE_PROMPT_VERSION = "judge-f3-v1"
JUDGE_SYSTEM = (
    "你是严谨的引用证据判断器。判断「结论（Claim）」是否被「证据（Evidence）」支持。"
    "只允许输出一个严格 JSON 对象，不要输出任何其他文字或 Markdown 代码块。"
    "JSON 格式固定为："
    '{"label": "SUPPORTED"|"UNSUPPORTED"|"UNCERTAIN", "confidence": 0到1的小数, "reason_code": "简短原因码"}。'
    "label 只能是以下三者之一："
    "SUPPORTED（证据明确支持结论，允许同义改写、缩写全称、单位/数值等价）；"
    "UNSUPPORTED（证据与结论矛盾，或结论丢失了关键条件/因果方向颠倒/比较方向颠倒/无中生有）；"
    "UNCERTAIN（无法确定，需要更多信息或超出证据范围的语义推断）。"
    "不得修改证据、不得重写结论、不得补充证据之外的新事实。"
)

VALID_LABELS = {"SUPPORTED", "UNSUPPORTED", "UNCERTAIN"}


def _strip_punct(text: str) -> str:
    return str(text or "").strip().rstrip("。！？!?；; \n\t")


def build_l1_input(case: dict) -> tuple[str, dict[int, str]]:
    evidence = case["evidence"]
    citations = "".join(f"[{index}]" for index in range(1, len(evidence) + 1))
    answer = _strip_punct(case["claim"]) + citations + "。"
    evidence_texts = {index: text for index, text in enumerate(evidence, 1)}
    return answer, evidence_texts


def run_l1(cases: list[dict]) -> list[dict]:
    verifier = DeterministicCitationVerifier()
    results: list[dict] = []
    for case in cases:
        answer, evidence_texts = build_l1_input(case)
        report = verifier.verify(answer, evidence_texts, citation_count=len(evidence_texts))
        supports = [v.support for v in report.verifications]
        # A single factual claim is expected; collapse to one label.
        label = supports[0] if len(supports) == 1 else ("SUPPORTED" if all(s == "SUPPORTED" for s in supports) else supports[0])
        if label == "NOT_APPLICABLE":
            label = "UNCERTAIN"
        results.append({"id": case["id"], "label": label})
    return results


def _parse_judge(raw: str) -> str:
    raw = str(raw or "").strip()
    # Strip surrounding markdown code fences if present.
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                return "UNCERTAIN"
        else:
            return "UNCERTAIN"
    label = str(data.get("label", "")).strip().upper()
    if label not in VALID_LABELS:
        # Fallback: trust a reason_code hint only if it maps to a valid label.
        hint = str(data.get("reason_code", "")).strip().upper()
        label = hint if hint in VALID_LABELS else "UNCERTAIN"
    return label


def run_l2(cases: list[dict], model: str) -> list[dict]:
    client = OllamaClient()
    results: list[dict] = []
    for index, case in enumerate(cases, 1):
        claim = case["claim"]
        evidence = "\n".join(f"- {text}" for text in case["evidence"])
        user = f"结论：{claim}\n\n证据：\n{evidence}"
        try:
            raw = client.chat(
                [
                    {"role": "system", "content": JUDGE_SYSTEM},
                    {"role": "user", "content": user},
                ],
                model=model,
                timeout=120.0,
            )
            label = _parse_judge(raw)
        except (OllamaError, Exception) as exc:  # noqa: BLE001
            label = "UNCERTAIN"
            print(f"  [judge error] {case['id']}: {type(exc).__name__}: {exc}", file=sys.stderr)
        results.append({"id": case["id"], "label": label})
        print(f"  l2 [{index}/{len(cases)}] {case['id']} -> {label}", file=sys.stderr)
    return results


def _compute_metrics(rows: list[dict]) -> dict:
    total = len(rows)
    correct = sum(1 for r in rows if r["label"] == r["ground_truth"])

    def pr(label: str) -> dict:
        tp = sum(1 for r in rows if r["label"] == label and r["ground_truth"] == label)
        fp = sum(1 for r in rows if r["label"] == label and r["ground_truth"] != label)
        fn = sum(1 for r in rows if r["label"] != label and r["ground_truth"] == label)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall}

    supported = pr("SUPPORTED")
    unsupported = pr("UNSUPPORTED")
    uncertain = pr("UNCERTAIN")

    false_support = sum(1 for r in rows if r["label"] == "SUPPORTED" and r["ground_truth"] == "UNSUPPORTED")
    false_reject = sum(1 for r in rows if r["label"] == "UNSUPPORTED" and r["ground_truth"] == "SUPPORTED")

    return {
        "total": total,
        "accuracy": correct / total if total else 0.0,
        "supported_precision": supported["precision"],
        "supported_recall": supported["recall"],
        "unsupported_precision": unsupported["precision"],
        "unsupported_recall": unsupported["recall"],
        "uncertain_precision": uncertain["precision"],
        "uncertain_recall": uncertain["recall"],
        "uncertain_rate": sum(1 for r in rows if r["label"] == "UNCERTAIN") / total if total else 0.0,
        "false_support": false_support,
        "false_support_rate": false_support / total if total else 0.0,
        "false_reject": false_reject,
        "false_reject_rate": false_reject / total if total else 0.0,
    }


def _uncertain_resolution(l1_rows: dict[str, str], l2_rows: dict[str, str], cases: list[dict]) -> dict:
    gt = {c["id"]: c["ground_truth"] for c in cases}
    uncertain_ids = [cid for cid, label in l1_rows.items() if label == "UNCERTAIN"]
    resolved = 0
    resolved_correct = 0
    for cid in uncertain_ids:
        l2_label = l2_rows.get(cid, "UNCERTAIN")
        if l2_label != "UNCERTAIN":
            resolved += 1
            if l2_label == gt[cid]:
                resolved_correct += 1
    return {
        "l1_uncertain_count": len(uncertain_ids),
        "l2_resolved_count": resolved,
        "l2_resolution_accuracy": resolved_correct / resolved if resolved else 0.0,
        "uncertain_resolution_rate": resolved / len(uncertain_ids) if uncertain_ids else 0.0,
    }


def _print_metrics(name: str, metrics: dict) -> None:
    print(f"\n== {name} ==")
    print(f"accuracy: {metrics['accuracy']:.4f} ({metrics['total']} cases)")
    print(f"supported precision/recall: {metrics['supported_precision']:.4f} / {metrics['supported_recall']:.4f}")
    print(f"unsupported precision/recall: {metrics['unsupported_precision']:.4f} / {metrics['unsupported_recall']:.4f}")
    print(f"uncertain precision/recall: {metrics['uncertain_precision']:.4f} / {metrics['uncertain_recall']:.4f}")
    print(f"uncertain rate: {metrics['uncertain_rate']:.4f}")
    print(f"false-support: {metrics['false_support']} ({metrics['false_support_rate']:.4f})")
    print(f"false-reject: {metrics['false_reject']} ({metrics['false_reject_rate']:.4f})")


def _print_confusion(rows: list[dict], gt_order: tuple[str, ...] = ("SUPPORTED", "UNSUPPORTED", "UNCERTAIN")) -> None:
    print("\nconfusion matrix (rows=predicted, cols=ground_truth):")
    header = "           " + "".join(f"{g:>12}" for g in gt_order)
    print(header)
    for pred in ("SUPPORTED", "UNSUPPORTED", "UNCERTAIN"):
        cells = []
        for gt in gt_order:
            cells.append(sum(1 for r in rows if r["label"] == pred and r["ground_truth"] == gt))
        print(f"{pred:>11}" + "".join(f"{c:>12}" for c in cells))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("l1", "l2", "both"), default="both")
    parser.add_argument("--model", default="qwen2.5:7b")
    args = parser.parse_args()

    golden = json.loads(CHALLENGE.read_text(encoding="utf-8"))
    cases = golden["cases"]

    started = time.perf_counter()

    l1_rows: dict[str, str] = {}
    l2_rows: dict[str, str] = {}
    l1_metrics = l2_metrics = None

    if args.mode in ("l1", "both"):
        l1_rows = {r["id"]: r["label"] for r in run_l1(cases)}
        l1_full = [{"id": c["id"], "label": l1_rows[c["id"]], "ground_truth": c["ground_truth"]} for c in cases]
        l1_metrics = _compute_metrics(l1_full)
        _print_metrics("L1 (deterministic Layer-1)", l1_metrics)
        _print_confusion(l1_full)

    if args.mode in ("l2", "both"):
        print(f"\n== L2 judge model: {args.model} (prompt {JUDGE_PROMPT_VERSION}) ==")
        l2_rows = {r["id"]: r["label"] for r in run_l2(cases, args.model)}
        l2_full = [{"id": c["id"], "label": l2_rows[c["id"]], "ground_truth": c["ground_truth"]} for c in cases]
        l2_metrics = _compute_metrics(l2_full)
        _print_metrics("L2 (Ollama LLM judge)", l2_metrics)
        _print_confusion(l2_full)

    if args.mode == "both" and l1_rows and l2_rows:
        print("\n== L1 vs L2 ==")
        print(f"L1 accuracy {l1_metrics['accuracy']:.4f} -> L2 accuracy {l2_metrics['accuracy']:.4f}")
        print(f"L1 false-support {l1_metrics['false_support_rate']:.4f} -> L2 false-support {l2_metrics['false_support_rate']:.4f}")
        res = _uncertain_resolution(l1_rows, l2_rows, cases)
        print("\n== Uncertain Resolution (L2 over L1-UNCERTAIN cases) ==")
        print(f"L1 uncertain count: {res['l1_uncertain_count']}")
        print(f"L2 resolved: {res['l2_resolved_count']} ({res['uncertain_resolution_rate']:.4f})")
        print(f"L2 resolution accuracy: {res['l2_resolution_accuracy']:.4f}")

    print(f"\ntotal wall time: {round((time.perf_counter() - started) * 1000)} ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
