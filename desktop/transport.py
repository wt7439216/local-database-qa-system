"""HTTP transport helpers shared by the request handler (P1 extraction).

``TransportMixin`` is mixed into ``BaseHTTPRequestHandler`` subclasses; the
bound ``owner`` (WebQAServer) is supplied by ``make_handler``.
"""
from __future__ import annotations

from http import HTTPStatus
import json
import logging
import mimetypes
from typing import Any

from core import config
from core.library_service import (
    DocumentNotFoundError,
    KnowledgeBaseNotFoundError,
    LibraryServiceError,
    LibraryStateError,
)
from core.query_scope import QueryScopeError
from desktop.jobs import AnswerJob
from desktop.library_api_safety import redact_source_paths, sanitize_error_message
from desktop.routes_v3 import ROUTE_MISS, dispatch_v3_library

MAX_BODY_BYTES = config.SETTINGS.max_body_bytes
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; connect-src 'self'; img-src 'self' data:; "
    "style-src 'self'; script-src 'self'; object-src 'none'; "
    "form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
)


class TransportMixin:
    owner: Any

    def _is_loopback(self) -> bool:
        return self.client_address[0] in {"127.0.0.1", "::1"}

    def _host_allowed(self) -> bool:
        host = self.headers.get("Host", "").strip().lower()
        return bool(host) and host in self.owner.allowed_hosts()

    def _authorized(self) -> bool:
        if self.owner.authorized(self.headers.get("Authorization", "")):
            return True
        self._error(HTTPStatus.UNAUTHORIZED, "请先使用配对码连接。")
        return False

    def _read_json(self) -> dict[str, Any] | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._error(HTTPStatus.BAD_REQUEST, "Content-Length 无效。")
            return None
        if length <= 0 or length > MAX_BODY_BYTES:
            self._error(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE if length > MAX_BODY_BYTES
                else HTTPStatus.BAD_REQUEST,
                "请求体为空或过大。",
            )
            return None
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._error(HTTPStatus.BAD_REQUEST, "请求体必须是 UTF-8 JSON。")
            return None
        if not isinstance(payload, dict):
            self._error(HTTPStatus.BAD_REQUEST, "JSON 顶层必须是对象。")
            return None
        return payload

    def _stream_job(self, job: AnswerJob) -> None:
        self.send_response(HTTPStatus.OK)
        self._common_headers()
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        position = 0
        try:
            while True:
                with job.condition:
                    if position >= len(job.events) and not job.done:
                        job.condition.wait(timeout=15)
                    events = job.events[position:]
                    position = len(job.events)
                    done = job.done
                for event in events:
                    self._chunk((json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
                if not events and not done:
                    self._chunk(b'{"event":"ping"}\n')
                if done and position >= len(job.events):
                    break
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except OSError:
            pass

    def _sse_job(self, job: AnswerJob) -> None:
        """P3: standards-compliant Server-Sent Events for the same event stream."""
        self.send_response(HTTPStatus.OK)
        self._common_headers()
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        position = 0
        idle = config.SETTINGS.stream_idle_seconds
        try:
            while True:
                with job.condition:
                    if position >= len(job.events) and not job.done:
                        job.condition.wait(timeout=idle)
                    events = job.events[position:]
                    position = len(job.events)
                    done = job.done
                for event in events:
                    payload = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
                    frame = f"event: {event['event']}\ndata: {payload}\n\n".encode("utf-8")
                    self._chunk(frame)
                if not events and not done:
                    self._chunk(b"event: ping\ndata: {}\n\n")
                if done and position >= len(job.events):
                    break
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except OSError:
            pass

    def _chunk(self, data: bytes) -> None:
        self.wfile.write(f"{len(data):X}\r\n".encode("ascii") + data + b"\r\n")
        self.wfile.flush()

    def _static(self, path: str) -> None:
        relative = "index.html" if path in {"", "/"} else path.lstrip("/")
        candidate = (self.owner.web_root / relative).resolve()
        try:
            candidate.relative_to(self.owner.web_root)
        except ValueError:
            self._error(HTTPStatus.NOT_FOUND, "文件不存在。")
            return
        if not candidate.is_file():
            self._error(HTTPStatus.NOT_FOUND, "文件不存在。")
            return
        body = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        # P3: ES modules require a JavaScript MIME type on every platform.
        if candidate.suffix.lower() in {".js", ".mjs"}:
            content_type = "text/javascript"
        self.send_response(HTTPStatus.OK)
        self._common_headers()
        self.send_header(
            "Content-Type",
            f"{content_type}; charset=utf-8"
            if content_type.startswith(("text/", "application/javascript")) else content_type,
        )
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(
        self, status: HTTPStatus, payload: dict[str, Any],
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self._common_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except OSError:
            pass

    def _error(
        self, status: HTTPStatus, message: str,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self._json(status, {"error": message, "status": int(status)}, extra_headers)

    def _common_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", CONTENT_SECURITY_POLICY)

    def _v3_library(self, path: str, payload: dict | None = None) -> None:
        """v3 library-manager API: dispatch + error mapping + path redaction."""
        service = self.owner.library_service
        if service is None:
            self._error(HTTPStatus.NOT_FOUND, "Library 管理未启用。")
            return
        policy = getattr(service, "path_policy", None)
        import_roots = tuple(str(root) for root in policy.roots) if policy is not None else ()

        def _log_detail(exc: BaseException) -> None:
            if self.owner.logger is not None:
                self.owner.logger.error("v3 library error %s: %r", path, exc)

        try:
            status, body = dispatch_v3_library(
                service, path, self.command, payload, self.path
            )
        except (DocumentNotFoundError, KnowledgeBaseNotFoundError) as exc:
            _log_detail(exc)
            self._error(HTTPStatus.NOT_FOUND, sanitize_error_message(exc, import_roots))
        except LibraryStateError as exc:
            _log_detail(exc)
            self._error(HTTPStatus.CONFLICT, sanitize_error_message(exc, import_roots))
        except (LibraryServiceError, QueryScopeError, ValueError) as exc:
            _log_detail(exc)
            self._error(HTTPStatus.BAD_REQUEST, sanitize_error_message(exc, import_roots))
        except OSError as exc:
            _log_detail(exc)
            self._error(HTTPStatus.BAD_REQUEST, sanitize_error_message(exc, import_roots))
        except Exception as exc:  # pragma: no cover - unexpected service bug
            _log_detail(exc)
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "服务器内部错误，详情已记录到日志。")
        else:
            if status == ROUTE_MISS[0] and body == ROUTE_MISS[1]:
                self._error(HTTPStatus.NOT_FOUND, "接口不存在。")
                return
            self._json(status, redact_source_paths(body, service.source_display))

    def log_message(self, format: str, *args: Any) -> None:
        logging.getLogger(__name__).debug("http %s", format % args)
