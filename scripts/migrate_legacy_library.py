"""Legacy (v4) -> managed (v5) library migration (Phase D.1.1 closure).

Merge semantics — legacy content is *added* to the managed library; the
managed library is never rebuilt or overwritten:

* embeddings are copied byte-for-byte (no re-embedding, no Ollama calls);
* the effective embedding space must match, otherwise the migration aborts
  with INCOMPATIBLE_EMBEDDING_SPACE.  A destination with zero embeddings
  and blank embedding metadata has no declared space — the source space is
  adopted and the destination metadata initialized;
* the whole SQLite merge runs in one transaction with count/referential/
  integrity verification before COMMIT — any failure rolls back;
* document/chunk/chapter/summary id collisions abort unless the content is
  byte-identical (ALREADY_MIGRATED / idempotent NOOP);
* legacy documents are registered in document_sources under the default KB
  (READY / enabled=1).  Phase C never persisted full source paths, so
  source_path is best-effort (the file name) — a later relink repairs it;
* on success the managed metadata records an unambiguous migration marker
  (counts, source basename, timestamp, content fingerprint).  The runtime
  library selector only allows dual-file startup with this evidence
  (see core/runtime_library.py).

Usage:
    python scripts/migrate_legacy_library.py \
        --source data/library/textbooks.sqlite3 \
        --destination data/library/documents.sqlite3 \
        --dry-run

The legacy source file is never modified, deleted or renamed.
"""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.importer import DEFAULT_GENERAL_COLLECTION
from core.library_service import (
    DEFAULT_KB_ID,
    DEFAULT_KB_NAME,
    utc_now,
)
from core.library_store import MANAGED_SCHEMA_VERSION, SCHEMA_VERSION, fts_tokenize

MIGRATION_MARKER_PREFIX = "legacy_migration_"

CORE_TABLES = ("documents", "chunks", "embeddings", "chapters", "summaries", "pages")


class MigrationError(Exception):
    """Aborted migration (nothing was changed in the destination)."""


def _open_ro(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _read_metadata(connection: sqlite3.Connection) -> dict[str, str]:
    return {str(row[0]): str(row[1]) for row in connection.execute("SELECT key, value FROM metadata")}


def _count(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0])


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def compute_legacy_fingerprint(connection: sqlite3.Connection) -> str:
    """Content fingerprint of the legacy library (no paths involved)."""
    lines: list[str] = []
    version = _read_metadata(connection).get("schema_version", "")
    lines.append(f"schema_version={version}")
    for row in connection.execute(
        "SELECT id, title, source_name, sha256, page_count FROM documents ORDER BY id"
    ):
        lines.append(
            "doc\t" + "\t".join(str(row[column]) for column in ("id", "sha256", "title", "source_name", "page_count"))
        )
    for row in connection.execute("SELECT id, document_id, text FROM chunks ORDER BY id"):
        lines.append(f"chunk\t{row['id']}\t{row['document_id']}\t{_sha256_text(row['text'])}")
    for row in connection.execute(
        "SELECT chunk_id, model, dimension, vector FROM embeddings ORDER BY chunk_id"
    ):
        lines.append(
            f"emb\t{row['chunk_id']}\t{row['model']}\t{row['dimension']}\t{_sha256_bytes(bytes(row['vector']))}"
        )
    for row in connection.execute(
        "SELECT id, chapter_number, title, overview FROM chapters ORDER BY id"
    ):
        lines.append(f"chapter\t{row['id']}\t{row['chapter_number']}\t{row['title']}\t{_sha256_text(row['overview'])}")
    for row in connection.execute("SELECT id, text FROM summaries ORDER BY id"):
        lines.append(f"summary\t{row['id']}\t{_sha256_text(row['text'])}")
    page_hashes = [
        _sha256_text(row["text"])
        for row in connection.execute("SELECT text FROM pages ORDER BY document_id, pdf_page")
    ]
    lines.append(f"pages\t{len(page_hashes)}\t{_sha256_text(''.join(page_hashes))}")
    for row in connection.execute(
        "SELECT key, value FROM metadata WHERE key LIKE 'import_%' ORDER BY key"
    ):
        lines.append(f"meta\t{row['key']}\t{row['value']}")
    return _sha256_text("\n".join(lines))


def _source_type_of(source_connection: sqlite3.Connection, document_id: str, source_name: str) -> str:
    metadata = _read_metadata(source_connection)
    explicit = metadata.get(f"import_source_type_{document_id}", "")
    if explicit:
        return explicit
    return Path(source_name).suffix.lstrip(".").lower()


def analyze(source_connection: sqlite3.Connection, destination_connection: sqlite3.Connection) -> dict:
    """Read-only preflight: validate compatibility and build the merge plan.

    Raises MigrationError on anything that must block the migration.
    """
    for connection, label in ((source_connection, "source"), (destination_connection, "destination")):
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise MigrationError(f"integrity_check 失败（{label}）：{integrity}")

    source_meta = _read_metadata(source_connection)
    destination_meta = _read_metadata(destination_connection)
    try:
        source_version = int(source_meta.get("schema_version") or 0)
        destination_version = int(destination_meta.get("schema_version") or 0)
    except ValueError as exc:
        raise MigrationError(f"schema_version 不可解析：{exc}") from exc
    if source_version != SCHEMA_VERSION:
        raise MigrationError(
            f"UNSUPPORTED_SOURCE_SCHEMA：source 必须是 v{SCHEMA_VERSION} legacy 库（当前 {source_version}）"
        )
    if destination_version != MANAGED_SCHEMA_VERSION:
        raise MigrationError(
            f"UNSUPPORTED_DESTINATION_SCHEMA：destination 必须是 v{MANAGED_SCHEMA_VERSION} managed 库（当前 {destination_version}）"
        )

    source_model = source_meta.get("embedding_model", "")
    source_dimension = source_meta.get("embedding_dimension", "")
    destination_model = destination_meta.get("embedding_model", "")
    destination_dimension = destination_meta.get("embedding_dimension", "")
    if not source_model or not source_dimension:
        raise MigrationError(
            "INCOMPATIBLE_EMBEDDING_SPACE：source 缺少 embedding_model/embedding_dimension 元数据；"
            "禁止重嵌入后继续"
        )
    # The effective space of an empty destination is undefined; adopt the
    # source space and initialize the metadata so future imports can detect
    # conflicts.  Any declared or existing destination space must match.
    destination_embedding_count = _count(destination_connection, "embeddings")
    adopt_embedding_space = (
        destination_embedding_count == 0
        and not destination_model
        and destination_dimension in ("", "0")
    )
    if not adopt_embedding_space and (
        destination_model != source_model or destination_dimension != source_dimension
    ):
        raise MigrationError(
            f"INCOMPATIBLE_EMBEDDING_SPACE：embedding 空间不一致"
            f"（source={source_model}/{source_dimension} "
            f"destination={destination_model or '∅'}/{destination_dimension or '∅'}）；"
            "禁止重嵌入后继续"
        )

    source_documents = {
        row["id"]: dict(row)
        for row in source_connection.execute(
            "SELECT id, title, source_name, sha256, page_count FROM documents ORDER BY id"
        )
    }
    destination_documents = {
        row["id"]: dict(row)
        for row in destination_connection.execute(
            "SELECT id, title, source_name, sha256, page_count FROM documents"
        )
    }

    def chunks_of(connection: sqlite3.Connection) -> dict[str, tuple[str, str]]:
        return {
            row["id"]: (row["document_id"], row["text"])
            for row in connection.execute("SELECT id, document_id, text FROM chunks")
        }

    source_chunks = chunks_of(source_connection)
    destination_chunks = chunks_of(destination_connection)
    destination_chapter_ids = {
        row[0] for row in destination_connection.execute("SELECT id FROM chapters")
    }
    destination_summary_ids = {
        row[0] for row in destination_connection.execute("SELECT id FROM summaries")
    }

    documents_plan: list[dict] = []
    to_migrate = {table: 0 for table in CORE_TABLES}
    to_migrate["fts_rows"] = 0

    for document_id, source_document in sorted(source_documents.items()):
        existing = destination_documents.get(document_id)
        if existing is None:
            own_chunks = {
                chunk_id for chunk_id, (owner, _text) in source_chunks.items() if owner == document_id
            }
            collisions = sorted(set(destination_chunks) & own_chunks)
            if collisions:
                raise MigrationError(
                    f"CHUNK_ID_COLLISION：legacy 文档 {document_id} 的 chunk id 已在 destination 存在"
                    f"（{', '.join(collisions[:5])}）；不会静默覆盖"
                )
            chapter_collisions = {
                row[0]
                for row in source_connection.execute("SELECT id FROM chapters WHERE document_id = ?", (document_id,))
            } & destination_chapter_ids
            if chapter_collisions:
                raise MigrationError(
                    f"CHAPTER_ID_COLLISION：legacy 文档 {document_id} 的 chapter id 已在 destination 存在"
                    f"（{', '.join(sorted(chapter_collisions)[:5])}）"
                )
            summary_collisions = {
                row[0]
                for row in source_connection.execute("SELECT id FROM summaries WHERE document_id = ?", (document_id,))
            } & destination_summary_ids
            if summary_collisions:
                raise MigrationError(
                    f"SUMMARY_ID_COLLISION：legacy 文档 {document_id} 的 summary id 已在 destination 存在"
                    f"（{', '.join(sorted(summary_collisions)[:5])}）"
                )
            own_chunk_count = _count_for_document(source_connection, "chunks", document_id)
            documents_plan.append(
                {"document_id": document_id, "decision": "NEW", "reason": "", "chunks": own_chunk_count}
            )
            to_migrate["documents"] += 1
            to_migrate["chunks"] += _count_for_document(source_connection, "chunks", document_id)
            to_migrate["embeddings"] += _count_embeddings_for_document(source_connection, document_id)
            to_migrate["chapters"] += _count_for_document(source_connection, "chapters", document_id)
            to_migrate["summaries"] += _count_for_document(source_connection, "summaries", document_id)
            to_migrate["pages"] += _count_for_document(source_connection, "pages", document_id)
            continue

        identity_match = (
            existing["sha256"] == source_document["sha256"]
            and existing["title"] == source_document["title"]
            and existing["source_name"] == source_document["source_name"]
            and existing["page_count"] == source_document["page_count"]
        )
        if not identity_match:
            raise MigrationError(
                f"DOCUMENT_ID_COLLISION：document_id {document_id} 在两个库中都存在但内容不同"
                f"（source sha={source_document['sha256'][:12]}… destination sha={existing['sha256'][:12]}…）；"
                "不会自动重新编号或覆盖"
            )
        own_source_chunks = {
            chunk_id: text for chunk_id, (owner, text) in source_chunks.items() if owner == document_id
        }
        own_destination_chunks = {
            chunk_id: text for chunk_id, (owner, text) in destination_chunks.items() if owner == document_id
        }
        if own_source_chunks != own_destination_chunks:
            raise MigrationError(
                f"DOCUMENT_ID_COLLISION：document_id {document_id} 文档身份一致但 chunk 内容不一致"
            )
        documents_plan.append({"document_id": document_id, "decision": "ALREADY_MIGRATED", "reason": "内容逐字节一致"})

    expected_totals = {
        table: _count(destination_connection, table) + to_migrate[table] for table in CORE_TABLES
    }
    to_migrate["fts_rows"] = to_migrate["chunks"]
    return {
        "source_version": source_version,
        "destination_version": destination_version,
        "embedding_model": source_model,
        "embedding_dimension": source_dimension,
        "adopt_embedding_space": adopt_embedding_space,
        "documents": documents_plan,
        "counts_to_migrate": to_migrate,
        "expected_totals": expected_totals,
        "fingerprint": compute_legacy_fingerprint(source_connection),
        "source_document_count": len(source_documents),
        "source_chunk_count": len(source_chunks),
        "source_embedding_count": _count(source_connection, "embeddings"),
    }


def _count_for_document(connection: sqlite3.Connection, table: str, document_id: str) -> int:
    return int(
        connection.execute(f"SELECT count(*) FROM {table} WHERE document_id = ?", (document_id,)).fetchone()[0]
    )


def _count_embeddings_for_document(connection: sqlite3.Connection, document_id: str) -> int:
    return int(
        connection.execute(
            "SELECT count(*) FROM embeddings WHERE chunk_id IN (SELECT id FROM chunks WHERE document_id = ?)",
            (document_id,),
        ).fetchone()[0]
    )


def _ensure_default_kb(destination_connection: sqlite3.Connection, now: str) -> None:
    destination_connection.execute(
        "INSERT OR IGNORE INTO knowledge_bases VALUES (?, ?, ?, ?, ?, 'active')",
        (DEFAULT_KB_ID, DEFAULT_KB_NAME, "迁移默认知识库（Phase D v3.3）", now, now),
    )


def _ensure_registry_row(
    destination_connection: sqlite3.Connection,
    document_id: str,
    source_name: str,
    sha256: str,
    source_type: str,
    now: str,
) -> None:
    """Register a migrated document (same best-effort semantics as
    ensure_managed_schema: source_path is the file name; relink repairs)."""
    destination_connection.execute(
        """
        INSERT OR IGNORE INTO document_sources
            (document_id, knowledge_base_id, source_path, source_type,
             document_type, source_hash, status, enabled, created_at, updated_at, last_error)
        VALUES (?, ?, ?, ?, ?, ?, 'READY', 1, ?, ?, '')
        """,
        (document_id, DEFAULT_KB_ID, str(source_name or ""), source_type, source_type, str(sha256 or ""), now, now),
    )


def _copy_document(
    destination_connection: sqlite3.Connection,
    source_connection: sqlite3.Connection,
    document_id: str,
    now: str,
) -> None:
    """Copy one legacy document (rows + FTS + doc metadata + registry)."""
    document = source_connection.execute(
        "SELECT id, title, source_name, sha256, page_count FROM documents WHERE id = ?", (document_id,)
    ).fetchone()
    destination_connection.execute(
        "INSERT INTO documents VALUES (?, ?, ?, ?, ?)",
        (document["id"], document["title"], document["source_name"], document["sha256"], document["page_count"]),
    )
    for row in source_connection.execute(
        """
        SELECT id, document_id, chapter, section, pdf_page_start, pdf_page_end,
               printed_page_start, printed_page_end, text, quality_score, kind, sort_order
        FROM chunks WHERE document_id = ? ORDER BY sort_order
        """,
        (document_id,),
    ):
        destination_connection.execute(
            "INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(row)
        )
        destination_connection.execute(
            "INSERT INTO chunk_fts VALUES (?, ?, ?)",
            (row["id"], fts_tokenize(row["text"]), fts_tokenize(row["section"])),
        )
    for row in source_connection.execute(
        "SELECT chunk_id, model, dimension, vector FROM embeddings WHERE chunk_id IN "
        "(SELECT id FROM chunks WHERE document_id = ?) ORDER BY chunk_id",
        (document_id,),
    ):
        destination_connection.execute("INSERT INTO embeddings VALUES (?, ?, ?, ?)", tuple(row))
    for row in source_connection.execute(
        """
        SELECT id, document_id, chapter_number, title, pdf_page_start, pdf_page_end,
               printed_page_start, printed_page_end, overview, sort_order
        FROM chapters WHERE document_id = ? ORDER BY sort_order
        """,
        (document_id,),
    ):
        destination_connection.execute("INSERT INTO chapters VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(row))
    for row in source_connection.execute(
        """
        SELECT id, document_id, scope_type, chapter, page_start, page_end, text, sort_order
        FROM summaries WHERE document_id = ? ORDER BY sort_order
        """,
        (document_id,),
    ):
        # Explicit core columns: the destination may already carry the F.1
        # additive provenance columns, whose defaults mark migrated legacy
        # rows as generator_type='legacy' (provenance unknown — never faked).
        destination_connection.execute(
            "INSERT INTO summaries (id, document_id, scope_type, chapter, page_start, page_end, text, sort_order) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            tuple(row),
        )
    for row in source_connection.execute(
        "SELECT document_id, pdf_page, printed_page, extraction_method, chapter, text "
        "FROM pages WHERE document_id = ? ORDER BY pdf_page",
        (document_id,),
    ):
        destination_connection.execute("INSERT INTO pages VALUES (?, ?, ?, ?, ?, ?)", tuple(row))
    for key, value in source_connection.execute(
        "SELECT key, value FROM metadata WHERE key IN (?, ?)",
        (f"import_source_type_{document_id}", f"import_extras_{document_id}"),
    ):
        destination_connection.execute("INSERT OR REPLACE INTO metadata VALUES (?, ?)", (key, value))
    _ensure_registry_row(
        destination_connection,
        document_id,
        document["source_name"],
        document["sha256"],
        _source_type_of(source_connection, document_id, document["source_name"]),
        now,
    )


def _write_marker(destination_connection: sqlite3.Connection, plan: dict, source_name: str, now: str) -> None:
    values = {
        "completed": "1",
        "source": source_name,
        "document_count": str(plan["source_document_count"]),
        "chunk_count": str(plan["source_chunk_count"]),
        "embedding_count": str(plan["source_embedding_count"]),
        "timestamp": now,
        "fingerprint": plan["fingerprint"],
    }
    for suffix, value in values.items():
        destination_connection.execute(
            "INSERT OR REPLACE INTO metadata VALUES (?, ?)", (MIGRATION_MARKER_PREFIX + suffix, value)
        )


def _verify_merged(
    destination_connection: sqlite3.Connection, before: dict[str, int], plan: dict
) -> None:
    expected = {
        table: before[table] + plan["counts_to_migrate"][table] for table in CORE_TABLES
    }
    for table, wanted in expected.items():
        actual = _count(destination_connection, table)
        if actual != wanted:
            raise MigrationError(f"count verification 失败：{table} 期望 {wanted} 实际 {actual}")
    fts_rows = _count(destination_connection, "chunk_fts")
    if fts_rows != _count(destination_connection, "chunks"):
        raise MigrationError(f"count verification 失败：chunk_fts {fts_rows} != chunks {_count(destination_connection, 'chunks')}")
    orphans = int(
        destination_connection.execute(
            "SELECT count(*) FROM embeddings WHERE chunk_id NOT IN (SELECT id FROM chunks)"
        ).fetchone()[0]
    )
    if orphans:
        raise MigrationError(f"referential verification 失败：{orphans} 条孤立 embeddings")
    integrity = destination_connection.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise MigrationError(f"迁移后 integrity_check 失败：{integrity}")


def _sync_qdrant(destination: Path, migrated_document_ids: list[str], expected_chunks: dict[str, int]) -> dict:
    """Post-commit convergence of the managed Qdrant collection.

    Vectors come from the migrated SQLite embeddings (no re-embedding).
    Reuses LibraryService._build_records via sync_index_payloads(force=True).
    """
    from core.library_service import LibraryService
    from core.qdrant_store import QdrantVectorStore

    service = LibraryService(destination)
    synced = service.sync_index_payloads(force=True)
    store = QdrantVectorStore(collection=DEFAULT_GENERAL_COLLECTION)
    verification: dict[str, dict] = {}
    for document_id in migrated_document_ids:
        points = store.scroll_payloads(
            query_filter={"must": [{"key": "document_id", "match": {"value": document_id}}]}
        )
        owned = [payload for payload in points if payload.get("document_id") == document_id]
        verification[document_id] = {
            "points": len(owned),
            "expected": expected_chunks.get(document_id),
        }
    return {
        "status": "ok",
        "collection": DEFAULT_GENERAL_COLLECTION,
        "synced_documents": synced,
        "verification": verification,
    }


def migrate(
    source: str | Path,
    destination: str | Path,
    *,
    dry_run: bool = False,
    qdrant_sync: bool = False,
) -> dict:
    """Merge a legacy v4 library into the managed v5 library."""
    source_path = Path(source)
    destination_path = Path(destination)
    if not source_path.is_file():
        raise MigrationError(f"source 不存在：{source_path.name}")
    if not destination_path.is_file():
        raise MigrationError(f"destination 不存在：{destination_path.name}")
    if source_path.resolve() == destination_path.resolve():
        raise MigrationError("source 与 destination 不能是同一个文件")

    with _open_ro(source_path) as source_connection, _open_ro(destination_path) as destination_connection:
        plan = analyze(source_connection, destination_connection)

    migrated_document_ids = [
        item["document_id"] for item in plan["documents"] if item["decision"] == "NEW"
    ]
    plan["qdrant"] = {
        "enabled": bool(qdrant_sync),
        "collection": DEFAULT_GENERAL_COLLECTION,
        "migrated_document_ids": migrated_document_ids,
        "records_to_upsert": plan["counts_to_migrate"]["embeddings"],
        "dimension": plan["embedding_dimension"],
    }
    if dry_run:
        plan["dry_run"] = True
        return plan

    # Re-analyze against the write connection to guard against changes
    # between preflight and write (TOCTOU).
    destination_connection = sqlite3.connect(destination_path, timeout=30)
    destination_connection.row_factory = sqlite3.Row
    destination_connection.execute("PRAGMA foreign_keys = ON")
    expected_chunks: dict[str, int] = {}
    try:
        with _open_ro(source_path) as source_connection:
            plan = analyze(source_connection, destination_connection)
            migrated_document_ids = [
                item["document_id"] for item in plan["documents"] if item["decision"] == "NEW"
            ]
            expected_chunks = {
                item["document_id"]: item["chunks"]
                for item in plan["documents"]
                if item["decision"] == "NEW"
            }
            plan["qdrant"] = {
                "enabled": bool(qdrant_sync),
                "collection": DEFAULT_GENERAL_COLLECTION,
                "migrated_document_ids": migrated_document_ids,
                "records_to_upsert": plan["counts_to_migrate"]["embeddings"],
                "dimension": plan["embedding_dimension"],
            }
            before = {table: _count(destination_connection, table) for table in CORE_TABLES}
            now = utc_now()
            destination_connection.execute("BEGIN IMMEDIATE")
            try:
                _ensure_default_kb(destination_connection, now)
                for item in plan["documents"]:
                    document_id = item["document_id"]
                    if item["decision"] == "NEW":
                        _copy_document(destination_connection, source_connection, document_id, now)
                    else:
                        document = source_connection.execute(
                            "SELECT source_name, sha256 FROM documents WHERE id = ?", (document_id,)
                        ).fetchone()
                        _ensure_registry_row(
                            destination_connection,
                            document_id,
                            document["source_name"],
                            document["sha256"],
                            _source_type_of(source_connection, document_id, document["source_name"]),
                            now,
                        )
                if plan["adopt_embedding_space"]:
                    destination_connection.execute(
                        "INSERT OR REPLACE INTO metadata VALUES ('embedding_model', ?)",
                        (plan["embedding_model"],),
                    )
                    destination_connection.execute(
                        "INSERT OR REPLACE INTO metadata VALUES ('embedding_dimension', ?)",
                        (plan["embedding_dimension"],),
                    )
                _write_marker(destination_connection, plan, source_path.name, now)
                _verify_merged(destination_connection, before, plan)
                destination_connection.commit()
            except Exception:
                destination_connection.rollback()
                raise
    except MigrationError:
        raise
    except Exception as exc:
        raise MigrationError(f"迁移失败，已回滚：{exc}") from exc
    finally:
        destination_connection.close()

    result: dict = {
        "dry_run": False,
        "plan": plan,
        "status": "merged",
        "migrated_document_ids": migrated_document_ids,
    }
    if qdrant_sync and migrated_document_ids:
        try:
            result["qdrant"] = _sync_qdrant(destination_path, migrated_document_ids, expected_chunks)
        except Exception as exc:
            result["qdrant"] = {"status": "failed", "error": str(exc)[:500]}
    return result


def _print_plan(plan: dict) -> None:
    print(f"source schema version: {plan['source_version']} (legacy v4)")
    print(f"destination schema version: {plan['destination_version']} (managed v5)")
    print(f"embedding compatibility: model={plan['embedding_model']} dimension={plan['embedding_dimension']}")
    for item in plan["documents"]:
        print(f"  document {item['document_id']}: {item['decision']}" + (f"（{item['reason']}）" if item["reason"] else ""))
    print("counts to migrate:", ", ".join(f"{k}={v}" for k, v in plan["counts_to_migrate"].items()))
    print("expected destination totals:", ", ".join(f"{k}={v}" for k, v in plan["expected_totals"].items()))
    print(f"legacy fingerprint: {plan['fingerprint']}")
    qdrant = plan["qdrant"]
    if qdrant["enabled"]:
        print(
            f"Qdrant plan: collection={qdrant['collection']} records_to_upsert={qdrant['records_to_upsert']}"
            f" dimension={qdrant['dimension']} migrated_documents={qdrant['migrated_document_ids']}"
        )
    else:
        print("Qdrant plan: disabled（--qdrant-sync 未指定）")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Legacy v4 -> managed v5 library migration (Phase D.1.1)")
    parser.add_argument("--source", required=True, help="legacy v4 library path")
    parser.add_argument("--destination", required=True, help="managed v5 library path")
    parser.add_argument("--dry-run", action="store_true", help="plan only; never write")
    parser.add_argument(
        "--qdrant-sync",
        action="store_true",
        help="after the SQLite merge, re-upsert READY points into the managed Qdrant "
        "collection (vectors copied from SQLite, never re-embedded)",
    )
    args = parser.parse_args(argv)
    try:
        result = migrate(args.source, args.destination, dry_run=args.dry_run, qdrant_sync=args.qdrant_sync)
    except MigrationError as exc:
        print(f"MIGRATION_ERROR: {exc}")
        return 2
    _print_plan(result["plan"] if "plan" in result else result)
    if args.dry_run:
        print("DRY-RUN: no changes were written.")
        return 0
    print(f"migrated documents: {result['migrated_document_ids']}")
    if "qdrant" in result and result["qdrant"]["status"] == "failed":
        print(f"QDRANT_SYNC_FAILED（SQLite 迁移已提交；可重跑 --qdrant-sync 或 sync_index_payloads）：{result['qdrant']['error']}")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
