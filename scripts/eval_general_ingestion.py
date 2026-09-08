"""General ingestion evaluation (Phase C / v3.2).

Imports each cross-format fixture into its OWN library (one format per
library — the five fixtures carry identical content, so a single mixed
library would let them compete arbitrarily in top-5), then runs 5 queries
per format checking document hit, section hit and no false OOS with real
Ollama embeddings (and Qdrant when --backend qdrant).

    python -X utf8 scripts/eval_general_ingestion.py
    python -X utf8 scripts/eval_general_ingestion.py --backend qdrant
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

EVAL_SET = Path(__file__).resolve().parent / "general_ingestion_eval.json"
FIXTURE_DIR = ROOT_DIR / "tests" / "fixtures" / "documents"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="通用导入评测（5 格式 × 5 查询，每格式独立库）")
    parser.add_argument("--library-dir", type=Path, default=ROOT_DIR / "data" / "library" / "eval")
    parser.add_argument("--backend", default="sqlite", choices=["sqlite", "qdrant"])
    parser.add_argument("--embedding-model", default="bge-m3")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ["VECTOR_BACKEND"] = args.backend
    os.environ["QA_EMBEDDING_MODEL"] = args.embedding_model
    os.environ["QDRANT_COLLECTION"] = "general_documents"

    from core.engine_v2 import StructuredQAEngine
    from core.importer import DocumentImporter

    data = json.loads(EVAL_SET.read_text(encoding="utf-8"))
    formats: dict[str, str] = data["meta"]["formats"]
    queries = data["queries"]
    passed = 0
    failures: list[dict] = []
    timings: dict[str, dict] = {}

    for source_type, fixture_name in formats.items():
        library = args.library_dir / f"eval-{source_type}.sqlite3"
        importer = DocumentImporter(library, embedding_model=args.embedding_model)
        import_result = importer.import_file(FIXTURE_DIR / fixture_name)
        if import_result.status not in {"READY", "UNCHANGED"}:
            failures.append({"format": source_type, "error": f"导入失败：{import_result.status} {import_result.error}"})
            continue
        timings[source_type] = {
            "parse_ms": import_result.parse_ms,
            "chunk_ms": import_result.chunk_ms,
            "embed_ms": import_result.embed_ms,
            "index_ms": import_result.index_ms,
            "total_ms": import_result.total_ms,
            "chunk_count": import_result.chunk_count,
        }
        engine = StructuredQAEngine(library)
        for case in [c for c in queries if c["format"] == source_type]:
            vector = engine.ollama.embed(case["q"], model=engine.library.embedding_model)[0]
            search = engine.library.retrieve(case["q"], vector, top_k=5, include_front_matter=False)
            if search.out_of_scope or not search.hits:
                failures.append({"q": case["q"], "format": source_type, "error": "被误判离题或无命中"})
                continue
            document_hit = all(hit.chunk.document_id == import_result.document_id for hit in search.hits)
            expected = case.get("expect_section_contains")
            section_hit = any(
                expected.lower() in (hit.chunk.section or "").lower() for hit in search.hits
            ) if expected else True
            ok = document_hit and section_hit
            passed += ok
            if not ok:
                failures.append({
                    "q": case["q"], "format": source_type, "document_hit": document_hit,
                    "section_hit": section_hit,
                    "hit_sections": [hit.chunk.section for hit in search.hits[:3]],
                })

    print(f"=== General Ingestion Eval（{len(queries)} 条，backend={args.backend}，每格式独立库）===")
    print(f"  passed: {passed}/{len(queries)}")
    print("  per-format import timing:")
    for source_type, timing in timings.items():
        print(
            f"    {source_type:<9} chunks={timing['chunk_count']:>3}  parse={timing['parse_ms']:>7.1f}ms  "
            f"chunk={timing['chunk_ms']:>7.1f}ms  embed={timing['embed_ms']:>8.1f}ms  "
            f"index={timing['index_ms']:>8.1f}ms  total={timing['total_ms']:>9.1f}ms"
        )
    for failure in failures:
        print(f"  FAIL: {failure}")
    verdict = "PASS" if not failures else "FAIL"
    print(f"  verdict: {verdict}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
