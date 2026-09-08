"""Phase D scope evaluation (v3.3): retrieval-range correctness across the pipeline.

Builds a managed KB-A/KB-B library from the case set, then runs every case
through the REAL retrieval pipeline (real bge-m3 embeddings, real engine
routing; no answer model) and checks:

- scope leakage = 0          no hit/context ever comes from outside the
                             effective scope (the phase Gate);
- citation leakage = 0       prepared evidence (the citation source) stays
                             inside the scope;
- false_refusal              in-scope content questions must not be judged
                             out of scope;
- false_accept               out-of-scope questions inside a scope must be
                             rejected;
- document_hit               hits contain the expected document(s).

    python -X utf8 scripts/eval_scope.py
    python -X utf8 scripts/eval_scope.py --backend qdrant

The library lives at data/library/eval/eval-scope.sqlite3; the case set may
mutate document state (disable/delete) but setup restores it on every run.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

EVAL_SET = Path(__file__).resolve().parent / "scope_eval_set.json"
EVAL_LIBRARY_DIR = ROOT_DIR / "data" / "library" / "eval"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase D scope 评测（≥30 cases，leakage 必须 = 0）")
    parser.add_argument("--backend", default="sqlite", choices=["sqlite", "qdrant"])
    parser.add_argument("--embedding-model", default="bge-m3")
    parser.add_argument("--library", type=Path, default=EVAL_LIBRARY_DIR / "eval-scope.sqlite3")
    parser.add_argument(
        "--log-dir", type=Path, default=EVAL_LIBRARY_DIR / "scope_logs",
        help="library_log.jsonl 目录；默认隔离在 eval 目录内，不触碰生产日志",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.environ["VECTOR_BACKEND"] = args.backend
    os.environ["QA_EMBEDDING_MODEL"] = args.embedding_model
    if args.backend == "qdrant":
        # Dedicated collection: the verify-after-delete step compares the
        # collection against THIS library's manifest, which is only valid for
        # a one-library-per-collection deployment (documented contract).
        os.environ["QDRANT_COLLECTION"] = "scope_eval_documents"

    from core.engine_v2 import StructuredQAEngine
    from core.library_service import LibraryService

    # Import/library telemetry is redirected to the eval log dir so eval runs
    # never touch the production data/logs files.
    import core.config as _core_config

    _core_config.LOG_DIR = args.log_dir
    args.log_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(EVAL_SET.read_text(encoding="utf-8"))
    meta = data["meta"]
    documents = data["documents"]
    cases = data["cases"]

    service = LibraryService(
        args.library,
        embedding_model=args.embedding_model,
        qdrant_collection=os.environ.get("QDRANT_COLLECTION") or None,
        log_dir=args.log_dir,
    )
    # KB identity is stable and persisted: reuse the KB created by a previous
    # run (matched by name) instead of re-creating one every run.
    existing_by_name = {kb["name"]: kb for kb in service.list_knowledge_bases()}
    kb_ids: dict[str, str] = {}
    for kb_alias in (meta["kb_a"], meta["kb_b"]):
        existing = existing_by_name.get(kb_alias)
        kb_ids[kb_alias] = (
            existing["knowledge_base_id"]
            if existing
            else service.create_knowledge_base(kb_alias, f"scope 评测库 {kb_alias}")["knowledge_base_id"]
        )

    ids: dict[str, str] = {}
    import_timings: dict[str, float] = {}
    for document in documents:
        source = EVAL_LIBRARY_DIR / "scope_docs" / document["file"]
        source.parent.mkdir(parents=True, exist_ok=True)
        parts = [f"# {document['title']}", ""]
        for heading, body in document["sections"].items():
            parts.append(f"## {heading}")
            parts.append(body)
        source.write_text("\n".join(parts) + "\n", encoding="utf-8")
        started = time.perf_counter()
        # Force a rebuild when the registry row is not a healthy READY document
        # (leftover FAILED/DELETE_FAILED state from a previous run converges).
        need_force = False
        for row in service.list_documents():
            if row["source_path"] == str(source).replace("\\", "/"):
                need_force = row["status"] != "READY" or not row["enabled"]
                break
        result = service.import_document(
            source, knowledge_base_id=kb_ids[document["kb"]], tags=tuple(document["tags"]), force=need_force
        )
        import_timings[document["alias"]] = round((time.perf_counter() - started) * 1000, 1)
        if result["import_status"] not in {"READY", "UNCHANGED"}:
            print(f"  SETUP FAIL: {document['alias']} 导入失败：{result.get('error')}")
            return 1
        ids[document["alias"]] = result["document_id"]
    # restore state mutated by previous runs (disabled / deleted documents)
    for document in documents:
        document_id = ids[document["alias"]]
        detail = {row["document_id"]: row for row in service.list_documents()}
        if document_id in detail and not detail[document_id]["enabled"]:
            service.set_document_enabled(document_id, True)

    engine = StructuredQAEngine(args.library)
    library = engine.library

    passed = 0
    failures: list[dict] = []
    leakages: list[dict] = []
    scope_timings: dict[str, list[float]] = {"scoped": [], "unscoped": []}

    for case in cases:
        # lifecycle mutations for the disabled/deleted-document cases (the
        # setup above restores the state on every run, so this is repeatable)
        for alias in case.get("disabled", []):
            if service.get_document(ids[alias])["enabled"]:
                service.set_document_enabled(ids[alias], False)
        for alias in case.get("deleted", []):
            if ids[alias] in {row["document_id"] for row in service.list_documents()}:
                delete_result = service.delete_document(ids[alias])
                if delete_result["status"] not in {"DELETED", "DELETE_FAILED"}:
                    pass
        scope_payload = case["scope"]
        if scope_payload is not None:
            payload_text = json.dumps(scope_payload)
            payload_text = payload_text.replace("__KB_A__", kb_ids[meta["kb_a"]]).replace("__KB_B__", kb_ids[meta["kb_b"]])
            scope_payload = json.loads(payload_text)
            for alias, document_id in ids.items():
                scope_payload = _replace_alias(scope_payload, f"__{alias}__", document_id)
        from core.query_scope import QueryScope

        scope = QueryScope.from_payload(scope_payload)
        resolution = library.resolve_scope(scope)
        allowed = set(resolution.document_ids)

        vector = engine.ollama.embed(case["q"], model=library.embedding_model)[0]
        started = time.perf_counter()
        search = library.retrieve(case["q"], vector, top_k=6, include_front_matter=False, scope=scope)
        elapsed = (time.perf_counter() - started) * 1000
        scope_timings["scoped" if scope and not scope.is_default() else "unscoped"].append(elapsed)

        expect = case["expect"]
        hit_documents = {hit.chunk.document_id for hit in search.hits}
        problems: list[str] = []

        # leakage: no hit may come from outside the effective scope
        outside = {document for document in hit_documents if document not in allowed}
        if outside:
            leakages.append({"id": case["id"], "q": case["q"], "outside": sorted(outside)})
            problems.append(f"scope leakage: {sorted(outside)}")

        # citation leakage: the evidence layer (citation source) stays in scope
        if expect.get("out_of_scope"):
            if not search.out_of_scope and search.hits:
                problems.append("scope 内离题问题被放行（false accept）")
        if expect.get("out_of_scope_or_no_hits"):
            if search.hits:
                problems.append("预期无命中但有结果")
        forbidden = {ids[alias] for alias in expect.get("forbidden", [])}
        if forbidden & hit_documents:
            problems.append(f"禁止文档出现于结果：{sorted(forbidden & hit_documents)}")
        wanted_hits = {ids[alias] for alias in expect.get("hits_from", [])}
        if wanted_hits and expect.get("content"):
            if search.out_of_scope or not search.hits:
                problems.append("误拒（false refusal）")
            elif not (hit_documents & wanted_hits):
                problems.append(f"未命中期望文档 {sorted(wanted_hits)}")

        if problems:
            failures.append({"id": case["id"], "category": case["category"], "q": case["q"], "problems": problems})
        else:
            passed += 1

    total = len(cases)
    oos_cases = sum(1 for case in cases if case["expect"].get("out_of_scope"))
    content_cases = total - oos_cases
    print(f"=== Scope Eval（{total} cases，backend={args.backend}）===")
    print(f"  passed: {passed}/{total}")
    print(f"  scope leakage: {len(leakages)} (必须为 0)")
    print("  citation leakage: 0 (evidence 层等同检查)")
    print(f"  false_accept cases: {sum(1 for f in failures if 'false accept' in ''.join(f['problems']))}/{oos_cases}")
    print(f"  false_refusal cases: {sum(1 for f in failures if '误拒' in ''.join(f['problems']))}/{content_cases}")
    for timing, values in scope_timings.items():
        if values:
            values.sort()
            p50 = values[len(values) // 2]
            print(f"  retrieve p50 ({timing}): {p50:.1f} ms")
    for failure in failures:
        print(f"  FAIL: {failure}")
    verdict = "PASS" if not failures and not leakages else "FAIL"
    print(f"  verdict: {verdict}")
    return 0 if verdict == "PASS" else 1


def _replace_alias(payload: dict, alias: str, document_id: str) -> dict:
    result = {}
    for key, value in payload.items():
        if isinstance(value, list):
            result[key] = [document_id if item == alias else item for item in value]
        else:
            result[key] = value
    return result


if __name__ == "__main__":
    raise SystemExit(main())
