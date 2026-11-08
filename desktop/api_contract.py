"""Machine-readable HTTP contract (OpenAPI 3.1 / JSON Schema 2020-12), P1.

This is the single source of truth for the v2 answer API and v3 library API.
It is deliberately conservative: required fields are pinned, extra fields are
allowed so additive evolution does not break the contract.
"""
from __future__ import annotations

from typing import Any

API_VERSION = "3.1.0"


def _obj(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "object", "properties": properties,
                             "additionalProperties": True}
    if required:
        schema["required"] = required
    return schema


def _array(items: dict[str, Any]) -> dict[str, Any]:
    return {"type": "array", "items": items}


SCHEMAS: dict[str, Any] = {
    "Error": _obj({"error": {"type": "string"}, "status": {"type": "integer"}},
                  ["error", "status"]),
    "Bootstrap": _obj({
        "pairing_code": {"type": "string", "pattern": "^[0-9]{6}$"},
        "lan_urls": _array({"type": "string"}),
    }, ["pairing_code", "lan_urls"]),
    "PairRequest": _obj({"code": {"type": "string"}}, ["code"]),
    "PairResponse": _obj({
        "token": {"type": "string", "minLength": 1},
        "expires_in": {"type": "integer"},
    }, ["token", "expires_in"]),
    "Health": _obj({
        "service": {"type": "string"},
        "api_version": {"type": "integer"},
        "queue_depth": {"type": "integer"},
        "lan_urls": _array({"type": "string"}),
        "documents": {"type": "integer"},
        "chunks": {"type": "integer"},
    }, ["service", "api_version", "queue_depth", "lan_urls"]),
    "CreateJobRequest": _obj({
        "question": {"type": "string", "minLength": 1},
        "history": _array({"type": "object"}),
        "scope": {"type": ["object", "null"]},
    }, ["question"]),
    "JobCreated": _obj({"job_id": {"type": "string"}, "status": {"type": "string"}},
                       ["job_id", "status"]),
    "JobCancelled": _obj({"job_id": {"type": "string"}, "status": {"const": "cancelling"}},
                         ["job_id", "status"]),
    "StatusResponse": _obj({"status": {"type": "string"}}, ["status"]),
    "NDJSONEvent": _obj({"event": {"type": "string"}}, ["event"]),
    "JobStatus": _obj({
        "job_id": {"type": "string"},
        "status": {"type": "string"},
        "done": {"type": "boolean"},
        "created_at": {"type": "number"},
        "event_count": {"type": "integer"},
        "cancelled": {"type": "boolean"},
        "timed_out": {"type": "boolean"},
    }, ["job_id", "status", "done"]),
    "LibraryOverview": _obj({
        "statistics": {"type": "object"},
        "knowledge_bases": _array({"type": "object"}),
        "documents": _array({"type": "object"}),
    }, ["statistics", "knowledge_bases", "documents"]),
    "KnowledgeBaseList": _obj({"knowledge_bases": _array({"type": "object"})},
                              ["knowledge_bases"]),
    "KnowledgeBase": _obj({"knowledge_base_id": {"type": "string"}}),
    "TagList": _obj({"tags": _array({"type": "string"})}, ["tags"]),
    "DocumentList": _obj({"documents": _array({"type": "object"})}, ["documents"]),
    "ImportRequest": _obj({
        "action": {"const": "import"},
        "path": {"type": "string"},
        "knowledge_base_id": {"type": "string"},
        "tags": _array({"type": "string"}),
        "force": {"type": "boolean"},
        "dry_run": {"type": "boolean"},
    }, ["action", "path"]),
    "ImportResult": _obj({"document_id": {"type": "string"}}),
    "DocumentAction": _obj({"document_id": {"type": "string"}}),
    "TagUpdate": _obj({"tags": _array({"type": "string"})}, ["tags"]),
}


def _response(description: str, schema: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"description": description}
    if schema:
        result["content"] = {
            "application/json": {"schema": {"$ref": f"#/components/schemas/{schema}"}}
        }
    return result


def _error_responses(*codes: int) -> dict[str, Any]:
    return {str(code): _response("Error", "Error") for code in codes}


def _operation(
    operation_id: str, summary: str, *, security: bool = True,
    request_schema: str | None = None, success_status: str = "200",
    success_schema: str | None = None, errors: tuple[int, ...] = (400, 401, 404),
    parameters: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    op: dict[str, Any] = {
        "operationId": operation_id,
        "summary": summary,
        "responses": {**_error_responses(*errors),
                      success_status: _response("Success", success_schema)},
    }
    if parameters:
        op["parameters"] = parameters
    if request_schema:
        op["requestBody"] = {
            "required": True,
            "content": {"application/json": {
                "schema": {"$ref": f"#/components/schemas/{request_schema}"}
            }},
        }
    if security:
        op["security"] = [{"bearerToken": []}]
    return op


def _path_param(name: str) -> dict[str, Any]:
    return {"name": name, "in": "path", "required": True,
            "schema": {"type": "string"}}


def build_openapi() -> dict[str, Any]:
    get = lambda oid, summary, **kw: {"get": _operation(oid, summary, **kw)}  # noqa: E731
    return {
        "openapi": API_VERSION,
        "info": {
            "title": "Local Database QA — HTTP API",
            "version": "2 (v2 answers) / 3 (v3 library)",
            "description": "Fully local, authenticated API. All v3 responses redact server paths.",
        },
        "servers": [{"url": "http://127.0.0.1:8765"}],
        "components": {
            "securitySchemes": {
                "bearerToken": {"type": "http", "scheme": "bearer"},
            },
            "schemas": SCHEMAS,
        },
        "paths": {
            "/api/v2/bootstrap": get("getBootstrap", "Pairing code (loopback only)",
                                     security=False, success_schema="Bootstrap", errors=(403,)),
            "/api/v2/pair": {"post": _operation(
                "postPair", "Exchange pairing code for token", security=False,
                request_schema="PairRequest", success_schema="PairResponse",
                errors=(400, 401, 429))},
            "/api/v2/health": get("getHealth", "Engine and library health",
                                  success_schema="Health", errors=(401,)),
            "/api/v2/jobs": {"post": _operation(
                "postJob", "Submit a question", request_schema="CreateJobRequest",
                success_status="202", success_schema="JobCreated",
                errors=(400, 401, 503))},
            "/api/v2/jobs/{job_id}/events": get(
                "getJobEvents", "NDJSON event stream", success_schema="NDJSONEvent",
                errors=(401, 404), parameters=[_path_param("job_id")]),
            "/api/v2/jobs/{job_id}/stream": get(
                "getJobSSE", "Standard Server-Sent Events stream",
                success_schema="NDJSONEvent", errors=(401, 404),
                parameters=[_path_param("job_id")]),
            "/api/v2/jobs/{job_id}": {
                "get": _operation(
                    "getJobStatus", "Lightweight job status probe",
                    success_schema="JobStatus", errors=(401, 404),
                    parameters=[_path_param("job_id")]),
                "delete": _operation(
                    "deleteJob", "Cancel a job", success_schema="JobCancelled",
                    errors=(401, 404), parameters=[_path_param("job_id")]),
            },
            "/api/v2/shutdown": {"post": _operation(
                "postShutdown", "Request graceful shutdown (loopback only)",
                success_schema="StatusResponse", errors=(401, 403))},
            "/api/v3/library": get("getLibrary", "Library overview",
                                   success_schema="LibraryOverview"),
            "/api/v3/library/knowledge-bases": {
                "get": _operation("listKnowledgeBases", "List knowledge bases",
                                  success_schema="KnowledgeBaseList"),
                "post": _operation("createKnowledgeBase", "Create knowledge base",
                                   request_schema="KnowledgeBase",
                                   success_status="201",
                                   success_schema="KnowledgeBase"),
            },
            "/api/v3/library/knowledge-bases/{id}": {
                "get": _operation("getKnowledgeBase", "Knowledge base detail",
                                  parameters=[_path_param("id")]),
                "post": _operation("updateKnowledgeBase", "Update knowledge base",
                                   request_schema="KnowledgeBase",
                                   parameters=[_path_param("id")]),
                "delete": _operation("deleteKnowledgeBase", "Delete knowledge base",
                                     success_schema="StatusResponse",
                                     parameters=[_path_param("id")]),
            },
            "/api/v3/library/tags": get("listTags", "List tags", success_schema="TagList"),
            "/api/v3/library/documents": {
                "get": _operation("listDocuments", "List documents (optional ?kb=)",
                                  success_schema="DocumentList",
                                  parameters=[{
                                      "name": "kb", "in": "query", "required": False,
                                      "schema": {"type": "string"},
                                  }]),
                "post": _operation("importDocument", "Import a document",
                                   request_schema="ImportRequest",
                                   success_status="201", success_schema="ImportResult",
                                   errors=(400, 404, 409)),
            },
            "/api/v3/library/documents/{id}": {
                "get": _operation("getDocument", "Document detail",
                                  parameters=[_path_param("id")]),
                "delete": _operation("deleteDocument", "Delete document",
                                     success_schema="StatusResponse",
                                     parameters=[_path_param("id")]),
            },
            "/api/v3/library/documents/{id}/{action}": {"post": _operation(
                "documentAction", "enable/disable/retry-index/retry-delete/relink/tags",
                success_schema="DocumentAction",
                parameters=[_path_param("id"), _path_param("action")],
                errors=(400, 404, 409))},
            "/": get("getIndex", "Static web workbench", security=False,
                     success_schema=None, errors=()),
            "/{file}": get("getStatic", "Static asset", security=False,
                           success_schema=None, errors=(404,),
                           parameters=[_path_param("file")]),
        },
    }


def schema_for_response(path: str, method: str, status: int) -> dict[str, Any] | None:
    """Resolve a response schema (with $ref) for contract assertions."""
    operation = build_openapi()["paths"].get(path, {}).get(method.lower())
    if not operation:
        return None
    response = operation.get("responses", {}).get(str(status))
    if not response or "content" not in response:
        return None
    ref = response["content"]["application/json"]["schema"].get("$ref")
    return SCHEMAS[ref.rsplit("/", 1)[-1]] if ref else None
