"""Responsive web application and authenticated v2 API for the local engine."""

from __future__ import annotations

from dataclasses import dataclass, field
import hmac
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import mimetypes
from pathlib import Path
import queue
import secrets
import socket
import threading
import time
from typing import Any
from urllib.parse import urlsplit

API_VERSION = 2
DEFAULT_PORT = 8765
MAX_BODY_BYTES = 64 * 1024
TOKEN_LIFETIME_SECONDS = 12 * 60 * 60
JOB_RETENTION_SECONDS = 30 * 60
AUTH_FAILURE_LIMIT = 5
AUTH_BLOCK_SECONDS = 60
WEB_ROOT = Path(__file__).resolve().parents[1] / "web"


def create_pairing_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def discover_lan_addresses() -> list[str]:
    candidates: list[str] = []
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        candidates.append(str(probe.getsockname()[0]))
    except OSError:
        pass
    finally:
        probe.close()
    try:
        candidates.extend(str(info[4][0]) for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET))
    except OSError:
        pass
    addresses: list[str] = []
    for candidate in candidates:
        try:
            address = ipaddress.ip_address(candidate)
        except ValueError:
            continue
        if isinstance(address, ipaddress.IPv4Address) and address.is_private and not address.is_loopback and not address.is_link_local and candidate not in addresses:
            addresses.append(candidate)
    return addresses


@dataclass
class AnswerJob:
    id: str
    question: str
    created_at: float = field(default_factory=time.time)
    status: str = "queued"
    events: list[dict[str, Any]] = field(default_factory=list)
    done: bool = False
    cancelled: threading.Event = field(default_factory=threading.Event)
    condition: threading.Condition = field(default_factory=threading.Condition)

    def emit(self, event: str, **payload: Any) -> None:
        with self.condition:
            self.events.append({"event": event, **payload})
            self.condition.notify_all()


class WebQAServer:
    def __init__(
        self,
        engine: Any,
        host: str = "127.0.0.1",
        port: int = DEFAULT_PORT,
        pairing_code: str | None = None,
        web_root: Path | None = None,
    ) -> None:
        self.engine = engine
        self.host = host
        self.requested_port = int(port)
        self.pairing_code = pairing_code or create_pairing_code()
        if len(self.pairing_code) != 6 or not self.pairing_code.isdigit():
            raise ValueError("配对码必须是 6 位数字。")
        self.web_root = Path(web_root or WEB_ROOT).resolve()
        self._tokens: dict[str, float] = {}
        self._token_lock = threading.Lock()
        self._auth_failures: dict[str, tuple[int, float]] = {}
        self._jobs: dict[str, AnswerJob] = {}
        self._jobs_lock = threading.Lock()
        self._engine_lock = threading.Lock()
        self._queue: queue.Queue[AnswerJob | None] = queue.Queue(maxsize=20)
        self.shutdown_requested = threading.Event()
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._worker: threading.Thread | None = None

    @property
    def port(self) -> int:
        return int(self._httpd.server_address[1]) if self._httpd else self.requested_port

    @property
    def local_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def lan_urls(self) -> list[str]:
        if self.host in {"127.0.0.1", "localhost", "::1"}:
            return [self.local_url]
        return [f"http://{address}:{self.port}" for address in discover_lan_addresses()] or [self.local_url]

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self) -> None:
        if self.running:
            return
        try:
            self._httpd = ThreadingHTTPServer((self.host, self.requested_port), make_handler(self))
        except OSError:
            if self.requested_port == 0:
                raise
            self._httpd = ThreadingHTTPServer((self.host, 0), make_handler(self))
        self._httpd.daemon_threads = True
        self._thread = threading.Thread(target=self._httpd.serve_forever, name="qa-web", daemon=True)
        self._worker = threading.Thread(target=self._work_loop, name="qa-worker", daemon=True)
        self._thread.start()
        self._worker.start()

    def stop(self) -> None:
        httpd = self._httpd
        self._httpd = None
        if httpd:
            httpd.shutdown()
            httpd.server_close()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        for thread in (self._thread, self._worker):
            if thread and thread is not threading.current_thread():
                thread.join(timeout=3)
        self._thread = None
        self._worker = None

    def pair(self, code: str, client_ip: str) -> tuple[str | None, int]:
        valid, retry_after = self._check_pairing_code(code, client_ip)
        if not valid:
            return None, retry_after
        token = secrets.token_urlsafe(32)
        with self._token_lock:
            self._tokens[token] = time.time() + TOKEN_LIFETIME_SECONDS
        return token, 0

    def authorized(self, authorization: str) -> bool:
        if not authorization.startswith("Bearer "):
            return False
        token = authorization[7:].strip()
        now = time.time()
        with self._token_lock:
            expired = [key for key, expiry in self._tokens.items() if expiry <= now]
            for key in expired:
                self._tokens.pop(key, None)
            expiry = self._tokens.get(token, 0)
        return expiry > now

    def _check_pairing_code(self, code: str, client_ip: str) -> tuple[bool, int]:
        now = time.time()
        with self._token_lock:
            failures, blocked_until = self._auth_failures.get(client_ip, (0, 0.0))
            if blocked_until > now:
                return False, max(1, int(blocked_until - now + 0.999))
            if hmac.compare_digest(self.pairing_code, str(code or "")):
                self._auth_failures.pop(client_ip, None)
                return True, 0
            failures = 1 if blocked_until else failures + 1
            blocked_until = now + AUTH_BLOCK_SECONDS if failures >= AUTH_FAILURE_LIMIT else 0.0
            self._auth_failures[client_ip] = (failures, blocked_until)
            return False, AUTH_BLOCK_SECONDS if blocked_until else 0

    def health(self) -> dict[str, Any]:
        data = dict(self.engine.health())
        data.update({"service": "local-textbook-qa", "api_version": API_VERSION, "queue_depth": self._queue.qsize(), "lan_urls": self.lan_urls})
        return data

    def create_job(self, question: str) -> AnswerJob:
        self._prune_jobs()
        job = AnswerJob(secrets.token_urlsafe(12), question)
        with self._jobs_lock:
            self._jobs[job.id] = job
        try:
            self._queue.put_nowait(job)
        except queue.Full as exc:
            with self._jobs_lock:
                self._jobs.pop(job.id, None)
            raise RuntimeError("等待队列已满，请稍后重试。") from exc
        return job

    def get_job(self, job_id: str) -> AnswerJob | None:
        with self._jobs_lock:
            return self._jobs.get(job_id)

    def _prune_jobs(self) -> None:
        cutoff = time.time() - JOB_RETENTION_SECONDS
        with self._jobs_lock:
            stale = [key for key, job in self._jobs.items() if job.done and job.created_at < cutoff]
            for key in stale:
                self._jobs.pop(key, None)

    def _work_loop(self) -> None:
        while True:
            job = self._queue.get()
            if job is None:
                return
            if job.cancelled.is_set():
                job.status = "cancelled"
                job.done = True
                job.emit("cancelled")
                continue
            job.status = "running"
            job.emit("status", message="正在检索教材")
            try:
                with self._engine_lock:
                    result = self.engine.answer(
                        job.question,
                        on_token=lambda token: job.emit("token", text=token),
                        cancelled=job.cancelled.is_set,
                    )
                if job.cancelled.is_set():
                    raise InterruptedError("回答已取消。")
                job.status = "complete"
                job.emit("final", result=result.to_dict() if hasattr(result, "to_dict") else dict(result))
            except InterruptedError:
                job.status = "cancelled"
                job.emit("cancelled")
            except Exception as exc:
                job.status = "failed"
                job.emit("error", message=str(exc))
            finally:
                job.done = True
                with job.condition:
                    job.condition.notify_all()


def make_handler(owner: WebQAServer) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "LocalTextbookQA/2"
        protocol_version = "HTTP/1.1"

        def do_GET(self) -> None:  # noqa: N802
            path = urlsplit(self.path).path
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
            if path.startswith("/api/"):
                self._error(HTTPStatus.NOT_FOUND, "接口不存在。")
                return
            self._static(path)

        def do_POST(self) -> None:  # noqa: N802
            path = urlsplit(self.path).path.rstrip("/") or "/"
            if path == "/api/v2/pair":
                payload = self._read_json()
                if payload is None:
                    return
                token, retry_after = owner.pair(str(payload.get("code") or ""), self.client_address[0])
                if not token:
                    self._error(HTTPStatus.TOO_MANY_REQUESTS if retry_after else HTTPStatus.UNAUTHORIZED, "配对尝试过多，请稍后重试。" if retry_after else "配对码不正确。")
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
            payload = self._read_json()
            if payload is None:
                return
            question = payload.get("question", payload.get("query"))
            if not isinstance(question, str) or not question.strip():
                self._error(HTTPStatus.BAD_REQUEST, "question 不能为空。")
                return
            if path == "/api/v2/jobs":
                try:
                    job = owner.create_job(question.strip())
                    self._json(HTTPStatus.ACCEPTED, {"job_id": job.id, "status": job.status})
                except RuntimeError as exc:
                    self._error(HTTPStatus.SERVICE_UNAVAILABLE, str(exc))
                return
            if path == "/api/v2/ask":
                try:
                    with owner._engine_lock:
                        result = owner.engine.answer(question.strip())
                    data = result.to_dict() if hasattr(result, "to_dict") else dict(result)
                    self._json(HTTPStatus.OK, data)
                except ValueError as exc:
                    self._error(HTTPStatus.BAD_REQUEST, str(exc))
                except Exception as exc:
                    self._error(HTTPStatus.SERVICE_UNAVAILABLE, str(exc))
                return
            self._error(HTTPStatus.NOT_FOUND, "接口不存在。")

        def do_DELETE(self) -> None:  # noqa: N802
            path = urlsplit(self.path).path
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

        def _is_loopback(self) -> bool:
            return self.client_address[0] in {"127.0.0.1", "::1"}

        def _authorized(self) -> bool:
            if owner.authorized(self.headers.get("Authorization", "")):
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
                self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE if length > MAX_BODY_BYTES else HTTPStatus.BAD_REQUEST, "请求体为空或过大。")
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
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
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
            candidate = (owner.web_root / relative).resolve()
            try:
                candidate.relative_to(owner.web_root)
            except ValueError:
                self._error(HTTPStatus.NOT_FOUND, "文件不存在。")
                return
            if not candidate.is_file():
                self._error(HTTPStatus.NOT_FOUND, "文件不存在。")
                return
            body = candidate.read_bytes()
            content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self._common_headers()
            self.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith(("text/", "application/javascript")) else content_type)
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self._common_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except OSError:
                pass

        def _error(self, status: HTTPStatus, message: str) -> None:
            self._json(status, {"error": message, "status": int(status)})

        def _common_headers(self) -> None:
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self' http:; img-src 'self' data:; style-src 'self'; script-src 'self'; base-uri 'none'; frame-ancestors 'none'")

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def re_fullmatch(pattern: str, value: str) -> str | None:
    import re

    match = re.fullmatch(pattern, value)
    return match.group(1) if match else None
