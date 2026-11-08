"""v3 Library API route table as a pure dispatch function (P1 extraction).

No HTTP handler state here: method/path/payload are explicit inputs, which
makes the whole v3 surface directly unit-testable and contract-checkable.
"""
from __future__ import annotations

from http import HTTPStatus
from typing import Any
from urllib.parse import parse_qs, urlsplit

from desktop.jobs import re_fullmatch, re_fullmatch_groups

ROUTE_MISS = (HTTPStatus.NOT_FOUND, {})


def dispatch_v3_library(
    service: Any,
    path: str,
    method: str,
    payload: dict[str, Any] | None,
    raw_path: str,
) -> tuple[HTTPStatus, dict[str, Any]]:
    if path == "/api/v3/library":
        return HTTPStatus.OK, {
            "statistics": service.statistics(),
            "knowledge_bases": service.list_knowledge_bases(),
            "documents": service.list_documents(),
        }
    if path == "/api/v3/library/knowledge-bases":
        if method == "POST":
            return HTTPStatus.CREATED, service.create_knowledge_base(
                (payload or {}).get("name"), (payload or {}).get("description", ""))
        return HTTPStatus.OK, {"knowledge_bases": service.list_knowledge_bases()}

    match = re_fullmatch(r"/api/v3/library/knowledge-bases/([^/]+)", path)
    if match:
        if method == "DELETE":
            return HTTPStatus.OK, service.delete_knowledge_base(match)
        if method == "POST":
            return HTTPStatus.OK, service.update_knowledge_base(
                match, name=(payload or {}).get("name"),
                description=(payload or {}).get("description"))
        return HTTPStatus.OK, service.get_knowledge_base(match)

    if path == "/api/v3/library/tags":
        return HTTPStatus.OK, {"tags": service.list_tags()}

    if path == "/api/v3/library/documents":
        if method == "POST" and payload is not None and payload.get("action") == "import":
            result = service.import_document(
                payload.get("path"),
                knowledge_base_id=payload.get("knowledge_base_id") or "kb-default",
                tags=payload.get("tags") or (),
                force=bool(payload.get("force")),
                dry_run=bool(payload.get("dry_run")),
            )
            status = HTTPStatus.CREATED if result.get("import_status") == "READY" else HTTPStatus.OK
            return status, result
        kb = parse_qs(urlsplit(raw_path).query).get("kb", [None])[0]
        return HTTPStatus.OK, {"documents": service.list_documents(kb)}

    match = re_fullmatch(r"/api/v3/library/documents/([^/]+)", path)
    if match:
        if method == "DELETE":
            return HTTPStatus.OK, service.delete_document(match)
        if method == "GET":
            return HTTPStatus.OK, service.get_document(match)
        return ROUTE_MISS

    action = re_fullmatch_groups(
        r"/api/v3/library/documents/([^/]+)/(enable|disable|retry-index|retry-delete|relink|tags)",
        path,
    )
    if action:
        document_id, operation = action
        if operation == "enable":
            return HTTPStatus.OK, service.set_document_enabled(document_id, True)
        if operation == "disable":
            return HTTPStatus.OK, service.set_document_enabled(document_id, False)
        if operation == "retry-index":
            return HTTPStatus.OK, service.retry_index(document_id)
        if operation == "retry-delete":
            return HTTPStatus.OK, service.retry_delete(document_id)
        if operation == "relink":
            return HTTPStatus.OK, service.relink_document(
                document_id, (payload or {}).get("path"),
                update_if_changed=bool((payload or {}).get("update_if_changed")),
            )
        tags = service.set_document_tags(document_id, (payload or {}).get("tags") or ())
        return HTTPStatus.OK, {"document_id": document_id, "tags": tags}
    return ROUTE_MISS
