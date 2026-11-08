"""HTTP request routing for v2 answers and v3 library management (P1).

``RequestHandler`` is a plain class (no closure); ``make_handler`` binds a
WebQAServer instance as the ``owner`` class attribute, preserving the old
``make_handler(owner)`` public API.
"""
from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from typing import Any
from urllib.parse import urlsplit

from desktop.auth import TOKEN_LIFETIME_SECONDS
from desktop.jobs import parse_scope_payload, re_fullmatch, sanitize_history
from desktop.transport import TransportMixin


class RequestHandler(TransportMixin, BaseHTTPRequestHandler):
    server_version = "LocalTextbookQA/2"
    protocol_version = "HTTP/1.1"
    timeout = 30
    owner: Any = None

    def do_GET(self) -> None:  # noqa: N802
        if not self._host_allowed():
            self._error(HTTPStatus.FORBIDDEN, "Host 头不匹配，拒绝访问。")
            return
        path = urlsplit(self.path).path
        owner = self.owner
        if path == "/api/v2/bootstrap":
            if not self._is_loopback():
                self._error(HTTPStatus.FORBIDDEN, "配对信息只能在本机查看。")
                return
            self._json(HTTPStatus.OK, {"pairing_code": owner.pairing_code, "lan_urls": owner.lan_urls})
            return
        if path == "/api/v2/health":
            if not self._authorized():
                return
            self._json(HTTPStatus.OK, owner.health())
            return
        match = re_fullmatch(r"/api/v2/jobs/([^/]+)/events", path)
        if match:
            if not self._authorized():
                return
            job = owner.get_job(match)
            if not job:
                self._error(HTTPStatus.NOT_FOUND, "任务不存在或已过期。")
                return
            self._stream_job(job)
            return
        match = re_fullmatch(r"/api/v2/jobs/([^/]+)/stream", path)
        if match:
            if not self._authorized():
                return
            job = owner.get_job(match)
            if not job:
                self._error(HTTPStatus.NOT_FOUND, "任务不存在或已过期。")
                return
            self._sse_job(job)
            return
        match = re_fullmatch(r"/api/v2/jobs/([^/]+)", path)
        if match:
            if not self._authorized():
                return
            status = owner.job_status(match)
            if status is None:
                self._error(HTTPStatus.NOT_FOUND, "任务不存在或已过期。")
                return
            self._json(HTTPStatus.OK, status)
            return
        if path.startswith("/api/v3/library"):
            if not self._authorized():
                return
            self._v3_library(path)
            return
        if path.startswith("/api/"):
            self._error(HTTPStatus.NOT_FOUND, "接口不存在。")
            return
        self._static(path)

    def do_POST(self) -> None:  # noqa: N802
        if not self._host_allowed():
            self._error(HTTPStatus.FORBIDDEN, "Host 头不匹配，拒绝访问。")
            return
        path = urlsplit(self.path).path.rstrip("/") or "/"
        owner = self.owner
        if path == "/api/v2/pair":
            payload = self._read_json()
            if payload is None:
                return
            token, retry_after = owner.pair(str(payload.get("code") or ""), self.client_address[0])
            if not token:
                retry_headers = {"Retry-After": str(retry_after)} if retry_after else None
                self._error(
                    HTTPStatus.TOO_MANY_REQUESTS if retry_after else HTTPStatus.UNAUTHORIZED,
                    "配对尝试过多，请稍后重试。" if retry_after else "配对码不正确。",
                    retry_headers,
                )
                return
            self._json(HTTPStatus.OK, {"token": token, "expires_in": TOKEN_LIFETIME_SECONDS})
            return
        if not self._authorized():
            return
        if path == "/api/v2/shutdown":
            if not self._is_loopback():
                self._error(HTTPStatus.FORBIDDEN, "只能在本机停止服务。")
                return
            self._json(HTTPStatus.OK, {"status": "stopping"})
            owner.shutdown_requested.set()
            return
        if path.startswith("/api/v3/library"):
            payload = self._read_json()
            if payload is None:
                return
            self._v3_library(path, payload)
            return
        payload = self._read_json()
        if payload is None:
            return
        question = payload.get("question", payload.get("query"))
        if not isinstance(question, str) or not question.strip():
            self._error(HTTPStatus.BAD_REQUEST, "question 不能为空。")
            return
        if path == "/api/v2/jobs":
            try:
                history = sanitize_history(payload.get("history"))
                scope = parse_scope_payload(payload)
                job = owner.create_job(question.strip(), history, scope)
                self._json(HTTPStatus.ACCEPTED, {"job_id": job.id, "status": job.status})
            except ValueError as exc:
                self._error(HTTPStatus.BAD_REQUEST, str(exc))
            except RuntimeError as exc:
                self._error(HTTPStatus.SERVICE_UNAVAILABLE, str(exc))
            return
        self._error(HTTPStatus.NOT_FOUND, "接口不存在。")

    def do_DELETE(self) -> None:  # noqa: N802
        if not self._host_allowed():
            self._error(HTTPStatus.FORBIDDEN, "Host 头不匹配，拒绝访问。")
            return
        path = urlsplit(self.path).path
        owner = self.owner
        if path.startswith("/api/v3/library"):
            if not self._authorized():
                return
            self._v3_library(path)
            return
        match = re_fullmatch(r"/api/v2/jobs/([^/]+)", path)
        if not match:
            self._error(HTTPStatus.NOT_FOUND, "接口不存在。")
            return
        if not self._authorized():
            return
        job = owner.get_job(match)
        if not job:
            self._error(HTTPStatus.NOT_FOUND, "任务不存在或已过期。")
            return
        job.cancelled.set()
        job.emit("status", message="正在取消")
        self._json(HTTPStatus.OK, {"job_id": job.id, "status": "cancelling"})


def make_handler(owner: Any) -> type[BaseHTTPRequestHandler]:
    return type("Handler", (RequestHandler,), {"owner": owner})
