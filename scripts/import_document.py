"""Import a document into a general knowledge library (Phase C CLI, Phase D managed).

    python -X utf8 scripts/import_document.py --file path/to/doc.docx
    python -X utf8 scripts/import_document.py --file doc.md --dry-run
    python -X utf8 scripts/import_document.py --file doc.pdf --backend qdrant
    python -X utf8 scripts/import_document.py --file doc.md --legacy   # raw v4 importer

Default (Phase D): routes through core.library_service.LibraryService — the
library is migrated to the v5 managed registry and the document gets a
persisted stable identity.  ``--legacy`` keeps the exact Phase C behavior
(path-derived identity, no registry writes).
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

from core.importer import DEFAULT_GENERAL_LIBRARY, DocumentImporter  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="通用文档导入 CLI（Phase C / v3.2 + Phase D managed）")
    parser.add_argument("--file", type=Path, nargs="+", required=True, help="要导入的文档（可多个）")
    parser.add_argument("--library", type=Path, default=DEFAULT_GENERAL_LIBRARY)
    parser.add_argument("--dry-run", action="store_true", help="解析/chunk/校验，但不写 SQLite/Qdrant/嵌入")
    parser.add_argument("--backend", default="sqlite", choices=["sqlite", "qdrant"])
    parser.add_argument("--collection", default=None, help="Qdrant collection（默认 general_documents）")
    parser.add_argument("--force", action="store_true", help="source_hash 未变化也强制重导")
    parser.add_argument("--embedding-model", default=None, help="覆盖嵌入模型（默认 QA_EMBEDDING_MODEL）")
    parser.add_argument("--kb", default=None, help="目标知识库 id（默认 kb-default）")
    parser.add_argument("--tags", default="", help="逗号分隔的标签")
    parser.add_argument("--legacy", action="store_true", help="绕过 LibraryService，直接使用 Phase C v4 导入器")
    return parser.parse_args()


def _summary(result) -> dict:
    if isinstance(result, dict):
        return {
            "file": result.get("source") or result.get("source_path") or "",
            "status": result.get("import_status") or result.get("status") or result.get("import_status"),
            "state": result.get("state", ""),
            "document_id": result.get("document_id", ""),
            "title": result.get("title", ""),
            "source_type": result.get("source_type", ""),
            "chunk_count": result.get("chunk_count", 0),
            "embedded_new": result.get("embedded_new", 0),
            "embedded_reused": result.get("embedded_reused", 0),
            "duplicate_candidates": result.get("duplicate_candidates", []),
            "total_ms": result.get("total_ms", 0.0),
            "error": result.get("error", ""),
        }
    return {
        "file": result.source,
        "status": result.status,
        "state": result.state,
        "document_id": result.document_id,
        "title": result.title,
        "source_type": result.source_type,
        "chunk_count": result.chunk_count,
        "embedded_new": result.embedded_new,
        "embedded_reused": result.embedded_reused,
        "duplicate_candidates": [],
        "total_ms": result.total_ms,
        "error": result.error,
    }


def main() -> int:
    args = parse_args()
    if args.backend == "qdrant":
        os.environ["VECTOR_BACKEND"] = "qdrant"
        if args.collection:
            os.environ["QDRANT_COLLECTION"] = args.collection
    tags = [item.strip() for item in args.tags.split(",") if item.strip()]
    failures = 0
    if args.legacy:
        importer = DocumentImporter(args.library, embedding_model=args.embedding_model)
        for source in args.file:
            result = importer.import_file(source, force=args.force, dry_run=args.dry_run)
            summary = _summary(result)
            print(json.dumps(summary, ensure_ascii=False))
            if result.status in {"FAILED", "FAILED_INDEX"}:
                failures += 1
        return 1 if failures else 0

    from core.library_service import LibraryService

    service = LibraryService(args.library, embedding_model=args.embedding_model)
    for source in args.file:
        try:
            result = service.import_document(
                source,
                knowledge_base_id=args.kb or "kb-default",
                tags=tuple(tags),
                force=args.force,
                dry_run=args.dry_run,
            )
        except Exception as exc:
            print(f"[FAIL] {source}: {exc}")
            failures += 1
            continue
        summary = _summary(result)
        print(json.dumps(summary, ensure_ascii=False))
        if summary["status"] in {"FAILED", "FAILED_INDEX"}:
            failures += 1
            if summary["error"]:
                print(f"  error: {summary['error']}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
