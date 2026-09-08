"""Phase E router / rewrite evaluation (v3.4).

Reads eval/phase_e_router_golden.json, runs the deterministic QueryRouter on
every case and reports:

- route accuracy (exact)
- follow-up resolution accuracy (status + referent + rewrite semantic target)
- ambiguous false-resolution rate
- scope conflict accuracy + engine-level scope leakage (0 required)
- per-category results and every failure with a typed error class

No LLM, no embedding model, no external service: fully deterministic and
reproducible offline.  Exit code 1 when any Phase E threshold is missed.
"""

from __future__ import annotations

from contextlib import closing
import json
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.engine_v2 import StructuredQAEngine  # noqa: E402
from core.library_service import LibraryService  # noqa: E402
from core.query_router import QueryRouter  # noqa: E402
from core.query_scope import QueryScope  # noqa: E402

GOLDEN = ROOT_DIR / "eval" / "phase_e_router_golden.json"

ROUTE_ACCURACY_MIN = 0.95
FOLLOWUP_ACCURACY_MIN = 0.90
AMBIGUOUS_FALSE_RESOLUTION_MAX = 0.02
SCOPE_LEAKAGE_MAX = 0

FOLLOWUP_CATEGORIES = {"follow_up", "pronoun", "ellipsis", "topic_shift", "ambiguous", "scope_sensitive"}


class FakeEmbedder:
    """Deterministic 8-dim hashing embedder (mirrors the test fake contract)."""

    def embed(self, texts, model=None, timeout=600):
        if isinstance(texts, str):
            texts = [texts]
        return [self._vector(text) for text in texts]

    @staticmethod
    def _vector(text: str) -> list[float]:
        vector = [0.0] * 8
        for index, char in enumerate(text):
            vector[(index + ord(char)) % 8] += 1.0
        norm = max(1.0, sum(value * value for value in vector) ** 0.5)
        return [value / norm for value in vector]


class FakeOllama(FakeEmbedder):
    def embed(self, text, model=None, timeout=600):
        return super().embed(text, model)

    def chat(self, messages, model=None):
        raise RuntimeError("eval must not call the answer model")

    def generate(self, prompt, model=None):
        raise RuntimeError("eval must not call the answer model")


def semantic_contains(actual: str, expected: str) -> bool:
    if not expected:
        return actual == expected
    return expected in actual or actual in expected


def run_router_cases() -> dict:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    titles = golden["meta"]["document_titles"]
    router = QueryRouter()
    failures: list[dict] = []
    per_category: dict[str, list[int]] = {}
    route_ok = 0
    followup_total = 0
    followup_ok = 0
    ambiguous_total = 0
    ambiguous_false = 0
    scope_total = 0
    scope_conflict_ok = 0

    for case in golden["cases"]:
        category = case["category"]
        allowed = set(case["scope_allowed"]) if case["scope_allowed"] else None
        decision = router.route(case["question"], case["history"], titles, allowed)
        entry = per_category.setdefault(category, [0, 0])

        route_match = decision.route == case["expected_route"]
        if route_match:
            route_ok += 1
        entry[0] += 1
        if route_match:
            entry[1] += 1

        expected_resolution = case["expected_resolution"]
        if expected_resolution != "none":
            followup_total += 1
            status_ok = decision.resolution_status == expected_resolution
            referent_ok = semantic_contains(decision.referent, case["expected_referent"])
            rewrite_ok = (
                decision.normalized_question == case["question"]
                if case["expected_rewrite"] is None
                else semantic_contains(decision.normalized_question, case["expected_rewrite"])
            )
            if expected_resolution == "ambiguous":
                ambiguous_total += 1
                if not status_ok:
                    ambiguous_false += 1
            if status_ok and referent_ok and rewrite_ok and route_match:
                followup_ok += 1
            else:
                failures.append(
                    {
                        "id": case["id"],
                        "class": (
                            "ROUTER_ERROR"
                            if not route_match
                            else "REFERENT_ERROR"
                            if not referent_ok
                            else "REWRITE_ERROR"
                            if not rewrite_ok
                            else "TOPIC_SHIFT_ERROR" if expected_resolution == "topic_shift" else "RESOLUTION_ERROR"
                        ),
                        "question": case["question"],
                        "expected": f"route={case['expected_route']} resolution={expected_resolution} referent={case['expected_referent']!r} rewrite={case['expected_rewrite']!r}",
                        "actual": f"route={decision.route} resolution={decision.resolution_status} referent={decision.referent!r} rewrite={decision.normalized_question!r}",
                    }
                )
        elif decision.normalized_question != case["question"]:
            failures.append(
                {
                    "id": case["id"],
                    "class": "REWRITE_ERROR",
                    "question": case["question"],
                    "expected": "no rewrite",
                    "actual": decision.normalized_question,
                }
            )

        if category == "scope_sensitive":
            scope_total += 1
            if decision.scope_conflict == case["expected_conflict"]:
                scope_conflict_ok += 1
            if decision.scope_conflict != case["expected_conflict"]:
                failures.append(
                    {
                        "id": case["id"],
                        "class": "SCOPE_ERROR",
                        "question": case["question"],
                        "expected": f"scope_conflict={case['expected_conflict']}",
                        "actual": f"scope_conflict={decision.scope_conflict}",
                    }
                )

    return {
        "total": len(golden["cases"]),
        "route_ok": route_ok,
        "route_accuracy": route_ok / len(golden["cases"]),
        "followup_total": followup_total,
        "followup_ok": followup_ok,
        "followup_accuracy": followup_ok / followup_total if followup_total else 1.0,
        "ambiguous_total": ambiguous_total,
        "ambiguous_false": ambiguous_false,
        "ambiguous_false_rate": ambiguous_false / ambiguous_total if ambiguous_total else 0.0,
        "scope_total": scope_total,
        "scope_conflict_ok": scope_conflict_ok,
        "per_category": per_category,
        "failures": failures,
    }


def markdown(title: str, body: str) -> str:
    return f"# {title}\n\n## 内容\n{body}\n"


def run_engine_scope_leakage_check() -> dict:
    """Engine-level check: a rewrite may mention an out-of-scope document,
    but retrieval and the prepared contexts must never leak it."""
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        library = root / "managed.sqlite3"
        service = LibraryService(library, embedding_model="test-embed", ollama=FakeEmbedder())
        kb_a = service.create_knowledge_base("kb-a")["knowledge_base_id"]
        kb_b = service.create_knowledge_base("kb-b")["knowledge_base_id"]
        source_a = root / "doc_a.md"
        source_a.write_text(
            markdown(
                "移动通信",
                "OFDM 是正交频分复用技术，把高速数据流分配到多个子载波上并行传输，"
                "广泛用于宽带无线通信系统。多径衰落是移动信道的主要现象，"
                "多径信号叠加会导致信号幅度起伏与相位旋转变化。",
            ),
            encoding="utf-8",
        )
        doc_a = service.import_document(source_a, knowledge_base_id=kb_a)["document_id"]
        source_b = root / "doc_b.md"
        source_b.write_text(
            markdown(
                "移动通信测试文档",
                "BETA_ONLY 标记的机密关键词只属于乙文档内容范围，不得在甲知识库范围内出现。"
                "CDMA 是码分多址接入技术，各用户使用不同的正交扩频码共享同一频段。",
            ),
            encoding="utf-8",
        )
        doc_b = service.import_document(source_b, knowledge_base_id=kb_b)["document_id"]

        engine = StructuredQAEngine(library, ollama=FakeOllama(), answer_model="answer:test")
        scope_a = QueryScope(document_ids=(doc_a,))
        leaked = 0
        runs = 0

        def check(engine: StructuredQAEngine, question: str, history: list[dict] | None, scope: QueryScope) -> None:
            nonlocal leaked, runs
            prepared = engine.prepare(question, history, scope)
            runs += 1
            allowed = engine.library.effective_allowed_ids(engine.library.resolve_scope(scope))
            for chunk in prepared.contexts:
                if allowed is not None and chunk.document_id not in allowed:
                    leaked += 1
            chapters_leaked = any(
                chapter.document_id not in allowed
                for chapter in prepared.chapters
                if allowed is not None
            )
            leaked += int(chapters_leaked)

        # 1. Explicit out-of-scope document reference -> scope_conflict path.
        prepared = engine.prepare("那移动通信测试文档呢", [{"question": "介绍OFDM", "answer": "A"}], scope_a)
        if not (prepared.decision is not None and prepared.decision.scope_conflict):
            leaked += 1  # conflict must be reported, never silently broadened
        # 2. Rewrite mentions the out-of-scope document; retrieval must stay empty.
        check(engine, "那它呢？", [{"question": "移动通信测试文档讲了什么", "answer": "A"}], scope_a)
        # 3. In-scope follow-up still resolves and retrieves in-scope only.
        check(engine, "它有什么优点？", [{"question": "介绍OFDM", "answer": "A"}], scope_a)
        # 4. Book routes stay inside the scope.
        check(engine, "那本书有哪些章节", [{"question": "介绍OFDM", "answer": "A"}], scope_a)
        # 5. Compare that names the out-of-scope document: conflict + no leak.
        prepared = engine.prepare("和移动通信测试文档相比有什么区别", [], scope_a)
        if not (prepared.decision is not None and prepared.decision.scope_conflict):
            leaked += 1
        check(engine, "GSM和CDMA有什么区别", [], scope_a)

        with closing(sqlite3.connect(library)) as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        del engine
        del service
        import gc

        gc.collect()
        return {"runs": runs, "leaked": leaked, "doc_a": doc_a, "doc_b": doc_b, "integrity": integrity}


def main() -> int:
    started = time.perf_counter()
    router_results = run_router_cases()
    leakage = run_engine_scope_leakage_check()
    latency_ms = round((time.perf_counter() - started) * 1000, 1)

    print("== Phase E Router Evaluation ==")
    print(f"cases: {router_results['total']}")
    print(f"route accuracy: {router_results['route_accuracy']:.4f} (>= {ROUTE_ACCURACY_MIN})")
    print(
        f"follow-up accuracy: {router_results['followup_accuracy']:.4f} "
        f"(n={router_results['followup_total']}, >= {FOLLOWUP_ACCURACY_MIN})"
    )
    print(
        f"ambiguous false-resolution rate: {router_results['ambiguous_false_rate']:.4f} "
        f"(n={router_results['ambiguous_total']}, <= {AMBIGUOUS_FALSE_RESOLUTION_MAX})"
    )
    print(f"scope conflict accuracy: {router_results['scope_conflict_ok']}/{router_results['scope_total']}")
    print(f"engine scope leakage: {leakage['leaked']} (must be 0), runs={leakage['runs']}, integrity={leakage['integrity']}")
    print("\nper category (ok/total):")
    for category, (total, ok) in sorted(router_results["per_category"].items()):
        print(f"  {category}: {ok}/{total}")

    failures = router_results["failures"]
    if failures:
        print(f"\nfailure cases: {len(failures)}")
        for failure in failures:
            print(f"  [{failure['class']}] {failure['id']} {failure['question']}")
            print(f"    expected: {failure['expected']}")
            print(f"    actual:   {failure['actual']}")
    else:
        print("\nfailure cases: 0")

    print(f"\nrouter+eval wall time: {latency_ms} ms")

    passed = (
        router_results["route_accuracy"] >= ROUTE_ACCURACY_MIN
        and router_results["followup_accuracy"] >= FOLLOWUP_ACCURACY_MIN
        and router_results["ambiguous_false_rate"] <= AMBIGUOUS_FALSE_RESOLUTION_MAX
        and leakage["leaked"] <= SCOPE_LEAKAGE_MAX
        and router_results["scope_conflict_ok"] == router_results["scope_total"]
    )
    print(f"\nPhase E eval gate: {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
