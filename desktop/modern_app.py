"""Optional FastAPI/uvicorn HTTP stack (P3).

The default runtime stays stdlib-only for offline/PyInstaller builds.  This
module is imported lazily (``python -m desktop --modern`` or the contract
harness) and reuses the very same ``WebQAServer`` collaborators, so the HTTP
contract in ``desktop/api_contract.py`` validates both stacks.
"""
from __future__ import annotations

import json
import mimetypes
import socket
import threading
import time
from typing import Any

from core import config
from core.library_service import (
    DocumentNotFoundError,
    KnowledgeBaseNotFoundError,
    LibraryServiceError,
    LibraryStateError,
)
from core.query_scope import QueryScopeError
from desktop.jobs import parse_scope_payload, sanitize_history
from desktop.library_api_safety import redact_source_paths, sanitize_error_message
from desktop.routes_v3 import dispatch_v3_library
from desktop.transport import CONTENT_SECURITY_POLICY
from desktop.web_server import DEFAULT_PORT, WebQAServer

# FastAPI must be a *module-level* name: with ``from __future__ import
# annotations`` FastAPI resolves string annotations in the module namespace,
# and a function-local import would make ``request: Request`` look like a
# required query parameter (HTTP 422).  The try/except keeps the stdlib-only
# runtime importable when the optional modern stack is not installed.
try:
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse, Response, StreamingResponse

    FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover - default zero-dependency runtime
    FASTAPI_AVAILABLE = False
    Request = Any  # type: ignore[misc,assignment]


def create_app(owner: WebQAServer, port: int) -> Any:
    """Build the ASGI application for the optional modern stack."""
    if not FASTAPI_AVAILABLE:
        raise RuntimeError("FastAPI 未安装；默认零依赖运行时不受影响。")
    app = FastAPI(
        title="Local Database QA — modern HTTP stack",
        version="2/3",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    allowed_hosts = {
        "127.0.0.1", "localhost", "[::1]",
        *(f"{name}:{port}" for name in ("127.0.0.1", "localhost", "[::1]")),
    }

    def error(status: int, message: str) -> JSONResponse:
        return JSONResponse({"error": message, "status": status}, status_code=status)

    def common(response: Response) -> Response:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.middleware("http")
    async def guard(request: Request, call_next):  # noqa: ANN001
        host = (request.headers.get("host") or "").lower()
        if host not in allowed_hosts:
            return common(error(403, "Host 头不匹配，拒绝访问。"))
        response = await call_next(request)
        return common(response)

    def authorized(request: Request) -> bool:
        return owner.authorized(request.headers.get("Authorization", ""))

    @app.get("/api/v2/bootstrap")
    def bootstrap(request: Request):
        if request.client is None or request.client.host not in {"127.0.0.1", "::1"}:
            return error(403, "配对信息只能在本机查看。")
        return {"pairing_code": owner.pairing_code, "lan_urls": owner.lan_urls}

    @app.post("/api/v2/pair")
    async def pair(request: Request):
        payload = await request.json()
        token, retry_after = owner.pair(str(payload.get("code") or ""), request.client.host)
        if not token:
            response = error(
                429 if retry_after else 401,
                "配对尝试过多，请稍后重试。" if retry_after else "配对码不正确。",
            )
            if retry_after:
                response.headers["Retry-After"] = str(retry_after)
            return response
        return {"token": token, "expires_in": config.SETTINGS.token_lifetime_seconds}

    @app.get("/api/v2/health")
    def health(request: Request):
        if not authorized(request):
            return error(401, "请先使用配对码连接。")
        return owner.health()

    @app.post("/api/v2/jobs", status_code=202)
    async def create_job(request: Request):
        if not authorized(request):
            return error(401, "请先使用配对码连接。")
        payload = await request.json()
        question = payload.get("question", payload.get("query"))
        if not isinstance(question, str) or not question.strip():
            return error(400, "question 不能为空。")
        try:
            history = sanitize_history(payload.get("history"))
            scope = parse_scope_payload(payload)
            job = owner.create_job(question.strip(), history, scope)
        except ValueError as exc:
            return error(400, str(exc))
        except RuntimeError as exc:
            return error(503, str(exc))
        return {"job_id": job.id, "status": job.status}

    def event_stream(job: Any, sse: bool = False):
        idle = config.SETTINGS.stream_idle_seconds

        def generate():
            position = 0
            while True:
                with job.condition:
                    if position >= len(job.events) and not job.done:
                        job.condition.wait(timeout=idle)
                    events = job.events[position:]
                    position = len(job.events)
                    done = job.done
                for event in events:
                    payload = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
                    yield (f"event: {event['event']}\ndata: {payload}\n\n" if sse
                           else payload + "\n")
                if not events and not done:
                    yield "event: ping\ndata: {}\n\n" if sse else '{"event":"ping"}\n'
                if done and position >= len(job.events):
                    break

        media = "text/event-stream" if sse else "application/x-ndjson"
        return StreamingResponse(generate(), media_type=media)

    @app.get("/api/v2/jobs/{job_id}/events")
    def job_events(job_id: str, request: Request):
        if not authorized(request):
            return error(401, "请先使用配对码连接。")
        job = owner.get_job(job_id)
        if not job:
            return error(404, "任务不存在或已过期。")
        return event_stream(job)

    @app.get("/api/v2/jobs/{job_id}/stream")
    def job_sse(job_id: str, request: Request):
        if not authorized(request):
            return error(401, "请先使用配对码连接。")
        job = owner.get_job(job_id)
        if not job:
            return error(404, "任务不存在或已过期。")
        return event_stream(job, sse=True)

    @app.get("/api/v2/jobs/{job_id}")
    def job_status(job_id: str, request: Request):
        if not authorized(request):
            return error(401, "请先使用配对码连接。")
        status = owner.job_status(job_id)
        return status if status else error(404, "任务不存在或已过期。")

    @app.delete("/api/v2/jobs/{job_id}")
    def cancel_job(job_id: str, request: Request):
        if not authorized(request):
            return error(401, "请先使用配对码连接。")
        job = owner.get_job(job_id)
        if not job:
            return error(404, "任务不存在或已过期。")
        job.cancelled.set()
        job.emit("status", message="正在取消")
        return {"job_id": job.id, "status": "cancelling"}

    @app.post("/api/v2/shutdown")
    def shutdown(request: Request):
        if not authorized(request):
            return error(401, "请先使用配对码连接。")
        if request.client is None or request.client.host not in {"127.0.0.1", "::1"}:
            return error(403, "只能在本机停止服务。")
        owner.shutdown_requested.set()
        return {"status": "stopping"}

    @app.api_route("/api/v3/library{rest:path}", methods=["GET", "POST", "DELETE"])
    async def library_api(rest: str, request: Request):
        if not authorized(request):
            return error(401, "请先使用配对码连接。")
        service = owner.library_service
        if service is None:
            return error(404, "Library 管理未启用。")
        payload = None
        if request.method == "POST":
            try:
                payload = await request.json()
            except Exception:
                payload = {}
        path = "/api/v3/library" + rest
        policy = getattr(service, "path_policy", None)
        roots = tuple(str(root) for root in policy.roots) if policy is not None else ()
        try:
            status, body = dispatch_v3_library(service, path, request.method, payload, str(request.url))
        except (DocumentNotFoundError, KnowledgeBaseNotFoundError) as exc:
            return error(404, sanitize_error_message(exc, roots))
        except LibraryStateError as exc:
            return error(409, sanitize_error_message(exc, roots))
        except (LibraryServiceError, QueryScopeError, ValueError, OSError) as exc:
            return error(400, sanitize_error_message(exc, roots))
        except Exception:
            return error(500, "服务器内部错误，详情已记录到日志。")
        if status == 404 and body == {}:
            return error(404, "接口不存在。")
        return JSONResponse(redact_source_paths(body, service.source_display), status_code=status)

    @app.get("/{path:path}")
    def static(path: str):
        relative = "index.html" if path in {"", "/"} else path
        candidate = (owner.web_root / relative).resolve()
        try:
            candidate.relative_to(owner.web_root)
        except ValueError:
            return error(404, "文件不存在。")
        if not candidate.is_file():
            return error(404, "文件不存在。")
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        if candidate.suffix.lower() in {".js", ".mjs"}:
            content_type = "text/javascript"
        body = candidate.read_bytes()
        response = Response(body, media_type=content_type)
        if content_type.startswith(("text/", "application/javascript")):
            response.headers["Content-Type"] = f"{content_type}; charset=utf-8"
        return response

    return app


class ModernServer:
    """uvicorn-backed façade with the same contract surface as WebQAServer."""

    def __init__(
        self,
        engine: Any,
        host: str = "127.0.0.1",
        port: int = DEFAULT_PORT,
        pairing_code: str | None = None,
        web_root: Any | None = None,
        log_file: Any | None = None,
        library_service: Any | None = None,
    ) -> None:
        self.owner = WebQAServer(
            engine, host=host, port=port, pairing_code=pairing_code,
            web_root=web_root, log_file=log_file, library_service=library_service,
        )
        self.host = host
        self._port = 0
        self._server: Any = None
        self._thread: threading.Thread | None = None

    def _free_port(self) -> int:
        with socket.socket() as probe:
            probe.bind((self.host, self.owner.requested_port or 0))
            return int(probe.getsockname()[1])

    def start(self) -> None:
        import uvicorn

        self._port = self._free_port()
        app = create_app(self.owner, self._port)
        self._server = uvicorn.Server(uvicorn.Config(
            app, host=self.host, port=self._port,
            log_level="error", access_log=False,
        ))
        owner = self.owner
        owner._workers_stop.clear()
        owner._workers = [
            threading.Thread(target=owner._work_loop, name=f"qa-modern-worker-{i}", daemon=True)
            for i in range(owner.answer_workers)
        ]
        for worker in owner._workers:
            worker.start()
        self._thread = threading.Thread(target=self._server.run, name="qa-uvicorn", daemon=True)
        self._thread.start()
        deadline = time.time() + 15
        while not self._server.started and time.time() < deadline:
            time.sleep(0.05)
        if not self._server.started:
            raise RuntimeError("uvicorn failed to start")

    @property
    def port(self) -> int:
        return self._port

    @property
    def local_url(self) -> str:
        return f"http://127.0.0.1:{self._port}"

    @property
    def pairing_code(self) -> str:
        return self.owner.pairing_code

    @property
    def lan_urls(self) -> list[str]:
        return [self.local_url]

    @property
    def shutdown_requested(self) -> threading.Event:
        return self.owner.shutdown_requested

    def pair(self, code: str, client_ip: str):
        return self.owner.pair(code, client_ip)

    def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=5)
        self.owner._workers_stop.set()
        try:
            self.owner._queue.put_nowait(None)
        except Exception:
            pass
        for worker in self.owner._workers:
            worker.join(timeout=3)
        self.owner._workers = []
