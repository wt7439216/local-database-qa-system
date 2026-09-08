"""Responsive web application and authenticated v2 API for the local engine."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
import hmac
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
import logging
import mimetypes
from pathlib import Path
import queue
import secrets
import socket
import threading
import time
from typing import Any
from urllib.parse import parse_qs, urlsplit

from core import config
from core.library_service import (
    DocumentNotFoundError,
    KnowledgeBaseNotFoundError,
    LibraryServiceError,
    LibraryStateError,
)
from core.query_scope import QueryScope, QueryScopeError
from desktop.library_api_safety import redact_source_paths, sanitize_error_message

API_VERSION = 2
DEFAULT_PORT = 8765
MAX_BODY_BYTES = 64 * 1024
TOKEN_LIFETIME_SECONDS = 12 * 60 * 60
JOB_RETENTION_SECONDS = 30 * 60
MAX_HISTORY_TURNS = 3
ANSWER_CACHE_SIZE = 64
AUTH_FAILURE_LIMIT = 5
AUTH_BLOCK_SECONDS = 60
AUTH_FAILURE_RETENTION_SECONDS = 60 * 60
WEB_ROOT = Path(__file__).resolve().parents[1] / "web"


class QAThreadingHTTPServer(ThreadingHTTPServer):
    # Windows maps SO_REUSEADDR to "another process may silently steal this
    # port"; refusing reuse is safer, and start() falls back to a random port.
    allow_reuse_address = False


def sanitize_history(history: Any) -> list[dict[str, str]]:
    """Validate the client-supplied conversation history for a follow-up ask.

    Phase E: optional structured fields (route / chapter / document_ids /
    compare_entities / referent) are whitelist-passed so the router can use
    them; old clients that send only {question, answer} keep working.
    """
    if history is None:
        return []
    if not isinstance(history, list):
        raise ValueError("history 必须是列表。")
    if len(history) > MAX_HISTORY_TURNS:
        history = history[-MAX_HISTORY_TURNS:]
    turns: list[dict[str, str]] = []
    for item in history:
        if not isinstance(item, dict):
            raise ValueError("history 项必须是对象。")
        question = item.get("question")
        answer = item.get("answer", "")
        if not isinstance(question, str) or not question.strip():
            raise ValueError("history 项缺少 question。")
        if not isinstance(answer, str):
            raise ValueError("history 项的 answer 必须是字符串。")
        turn: dict[str, Any] = {"question": question.strip()[:2000], "answer": answer.strip()[:6000]}
        route = item.get("route")
        if isinstance(route, str) and route:
            turn["route"] = route[:40]
        chapter = item.get("chapter")
        if isinstance(chapter, int) and not isinstance(chapter, bool) and 1 <= chapter <= 999:
            turn["chapter"] = chapter
        for field_name in ("document_ids", "compare_entities"):
            value = item.get(field_name)
            if isinstance(value, list) and all(isinstance(entry, str) for entry in value):
                turn[field_name] = [str(entry)[:200] for entry in value][:50]
        referent = item.get("referent")
        if isinstance(referent, str) and referent:
            turn["referent"] = referent.strip()[:200]
        turns.append(turn)
    return turns


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
    history: list[dict[str, str]] = field(default_factory=list)
    scope: QueryScope | None = None
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
        log_file: str | Path | None = None,
        library_service: Any | None = None,
    ) -> None:
        self.engine = engine
        self.library_service = library_service
        self.host = host
        self.requested_port = int(port)
        self.pairing_code = pairing_code or create_pairing_code()
        if len(self.pairing_code) != 6 or not self.pairing_code.isdigit():
            raise ValueError("配对码必须是 6 位数字。")
        self.web_root = Path(web_root or WEB_ROOT).resolve()
        self.logger = self._build_logger(log_file)
        # 相同问题缓存：键含教材指纹与回答模型，教材重建后自动失效。
        # 追问（带 history）依赖上下文，不参与缓存。
        self._answer_cache: OrderedDict[tuple[str, str, str], dict[str, Any]] = OrderedDict()
        self._cache_lock = threading.Lock()
        self._recompute_fingerprint()
        self._tokens: dict[str, float] = {}
        self._token_lock = threading.Lock()
        self._auth_failures: dict[str, tuple[int, float, float]] = {}
        self._jobs: dict[str, AnswerJob] = {}
        self._jobs_lock = threading.Lock()
        self._engine_lock = threading.Lock()
        self._queue: queue.Queue[AnswerJob | None] = queue.Queue(maxsize=20)
        self.shutdown_requested = threading.Event()
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._worker: threading.Thread | None = None
        self._allowed_hosts_cache: tuple[float, set[str]] = (0.0, set())

    @staticmethod
    def _build_logger(log_file: str | Path | None) -> logging.Logger | None:
        # A dedicated Logger instance (not the global registry) keeps servers
        # isolated in tests; the handler is closed again in stop().
        path = Path(log_file) if log_file else Path(config.QA_LOG_FILE) if config.QA_LOG_FILE else None
        if path is None:
            return None
        logger = logging.Logger(f"qa-server:{path}", level=logging.INFO)
        handler = logging.FileHandler(path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        logger.addHandler(handler)
        return logger

    def _recompute_fingerprint(self) -> None:
        """Rebuild the cache fingerprint from the current library metadata
        (Phase D.1): runtime mutations change it, so stale cached answers
        can never survive an import/update/disable/delete."""
        library = getattr(self.engine, "library", None)
        metadata = getattr(library, "metadata", None) if library is not None else None
        fingerprint = metadata.get("built_at", "") if isinstance(metadata, dict) else ""
        fingerprint += "|" + str(metadata.get("source_sha256", "")) if isinstance(metadata, dict) else ""
        self._engine_fingerprint = fingerprint

    def _on_library_mutated(self) -> None:
        """Phase D.1 runtime integration: after a committed library mutation
        the QA runtime is brought back in sync in place — snapshots and the
        dense index reload, the fingerprint is recomputed and the answer
        cache is dropped.  Runs under _engine_lock so an in-flight answer
        finishes against the old consistent snapshot."""
        with self._engine_lock:
            library = getattr(self.engine, "library", None)
            if library is not None and hasattr(library, "refresh"):
                library.refresh()
            self._recompute_fingerprint()
            with self._cache_lock:
                self._answer_cache.clear()

    def _cache_get(self, key: tuple[str, str, str]) -> dict[str, Any] | None:
        with self._cache_lock:
            cached = self._answer_cache.get(key)
            if cached is not None:
                self._answer_cache.move_to_end(key)
            return cached

    def _cache_put(self, key: tuple[str, str, str], result: dict[str, Any]) -> None:
        with self._cache_lock:
            self._answer_cache[key] = result
            self._answer_cache.move_to_end(key)
            while len(self._answer_cache) > ANSWER_CACHE_SIZE:
                self._answer_cache.popitem(last=False)

    @staticmethod
    def _compact(text: Any, limit: int = 200) -> str:
        return json.dumps(str(text)[:limit], ensure_ascii=False)

    def _log_answer(self, question: str, data: dict[str, Any]) -> None:
        if not self.logger:
            return
        self.logger.info(
            "answer route=%s mode=%s confidence=%s out_of_scope=%s elapsed_ms=%s question=%s",
            data.get("route", ""),
            data.get("retrieval_mode", ""),
            data.get("confidence", ""),
            data.get("out_of_scope", ""),
            data.get("elapsed_ms", ""),
            self._compact(question),
        )

    def _log_event(self, event: str, question: str, detail: str) -> None:
        if not self.logger:
            return
        self.logger.info("%s detail=%s question=%s", event, self._compact(detail), self._compact(question))

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

    def allowed_hosts(self) -> set[str]:
        """Host header values this service accepts.

        Rejecting foreign Host headers blocks DNS rebinding pages from reading
        the pairing code or calling the API through a re-bound domain name.
        """
        computed_at, cached = self._allowed_hosts_cache
        now = time.time()
        if cached and now - computed_at < 10:
            return cached
        port = self.port
        hostname = socket.gethostname().lower()
        names = {"127.0.0.1", "localhost", "[::1]", hostname, f"{hostname}.local"}
        if self.host not in {"127.0.0.1", "localhost", "::1"}:
            names.update(discover_lan_addresses())
        hosts = names | {f"{name}:{port}" for name in names}
        self._allowed_hosts_cache = (now, hosts)
        return hosts

    def start(self) -> None:
        if self.running:
            return
        try:
            self._httpd = QAThreadingHTTPServer((self.host, self.requested_port), make_handler(self))
        except OSError:
            if self.requested_port == 0:
                raise
            self._httpd = QAThreadingHTTPServer((self.host, 0), make_handler(self))
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
        if self.logger is not None:
            for handler in list(self.logger.handlers):
                handler.close()
                self.logger.removeHandler(handler)

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
            # Failure records are kept for one hour only so a long-running
            # service cannot accumulate unbounded per-IP state.
            stale = [
                key
                for key, value in self._auth_failures.items()
                if value[2] < now - AUTH_FAILURE_RETENTION_SECONDS
            ]
            for key in stale:
                self._auth_failures.pop(key, None)
            failures, blocked_until, _updated = self._auth_failures.get(client_ip, (0, 0.0, 0.0))
            if blocked_until > now:
                return False, max(1, int(blocked_until - now + 0.999))
            if hmac.compare_digest(self.pairing_code, str(code or "")):
                self._auth_failures.pop(client_ip, None)
                return True, 0
            failures = 1 if blocked_until else failures + 1
            blocked_until = now + AUTH_BLOCK_SECONDS if failures >= AUTH_FAILURE_LIMIT else 0.0
            self._auth_failures[client_ip] = (failures, blocked_until, now)
            return False, AUTH_BLOCK_SECONDS if blocked_until else 0

    def health(self) -> dict[str, Any]:
        data = dict(self.engine.health())
        data.update({"service": "local-textbook-qa", "api_version": API_VERSION, "queue_depth": self._queue.qsize(), "lan_urls": self.lan_urls})
        return data

    def create_job(
        self,
        question: str,
        history: list[dict[str, str]] | None = None,
        scope: QueryScope | None = None,
    ) -> AnswerJob:
        self._prune_jobs()
        job = AnswerJob(secrets.token_urlsafe(12), question, list(history or []), scope)
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
            cache_key = (
                job.question.strip(),
                self._engine_fingerprint,
                str(getattr(self.engine, "answer_model", "")),
                scope_cache_key(job.scope),
            )
            try:
                cached = None if job.history else self._cache_get(cache_key)
                if cached is not None:
                    data = cached
                    job.emit("status", message="命中缓存")
                else:
                    with self._engine_lock:
                        # Only pass scope when actually set: engines without a
                        # scope parameter (Phase C contract) keep working.
                        scope_kwargs = {} if job.scope is None else {"scope": job.scope}
                        result = self.engine.answer(
                            job.question,
                            history=job.history,
                            on_token=lambda token: job.emit("token", text=token),
                            cancelled=job.cancelled.is_set,
                            **scope_kwargs,
                        )
                    if job.cancelled.is_set():
                        raise InterruptedError("回答已取消。")
                    data = result.to_dict() if hasattr(result, "to_dict") else dict(result)
                    if not job.history:
                        self._cache_put(cache_key, data)
                self._log_answer(job.question, data)
                job.status = "complete"
                job.emit("final", result=data)
            except InterruptedError:
                job.status = "cancelled"
                self._log_event("cancelled", job.question, "")
                job.emit("cancelled")
            except Exception as exc:
                job.status = "failed"
                self._log_event("error", job.question, str(exc))
                job.emit("error", message=str(exc))
            finally:
                job.done = True
                with job.condition:
                    job.condition.notify_all()


def make_handler(owner: WebQAServer) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "LocalTextbookQA/2"
        protocol_version = "HTTP/1.1"
        timeout = 30

        def do_GET(self) -> None:  # noqa: N802
            if not self._host_allowed():
                self._error(HTTPStatus.FORBIDDEN, "Host 头不匹配，拒绝访问。")
                return
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
                if not self._authorized():
                    return
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

        def _v3_library(self, path: str, payload: dict | None = None) -> None:
            """Phase D library-manager API (backed by core.library_service)."""
            service = owner.library_service
            if service is None:
                self._error(HTTPStatus.NOT_FOUND, "Library 管理未启用。")
                return
            policy = getattr(service, "path_policy", None)
            import_roots = tuple(str(root) for root in policy.roots) if policy is not None else ()

            def _log_detail(exc: BaseException) -> None:
                # P0-04: full details (including server paths) go to the log
                # only; the HTTP body carries the sanitized message.
                if owner.logger is not None:
                    owner.logger.error("v3 library error %s: %r", path, exc)

            try:
                status, body = self._v3_library_dispatch(service, path, payload)
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
                if status == HTTPStatus.NOT_FOUND and body == {}:
                    # Route-miss sentinel: the dispatch never emits a response
                    # itself, so this is the only write for the request.
                    self._error(HTTPStatus.NOT_FOUND, "接口不存在。")
                    return
                # Security closure: never return server absolute paths.
                self._json(status, redact_source_paths(body, service.source_display))

        def _v3_library_dispatch(self, service, path: str, payload: dict | None) -> tuple[HTTPStatus, dict[str, Any]]:
            if path == "/api/v3/library":
                return HTTPStatus.OK, {
                    "statistics": service.statistics(),
                    "knowledge_bases": service.list_knowledge_bases(),
                    "documents": service.list_documents(),
                }
            if path == "/api/v3/library/knowledge-bases":
                if self.command == "POST":
                    return HTTPStatus.CREATED, service.create_knowledge_base(
                        payload.get("name"), payload.get("description", ""))
                return HTTPStatus.OK, {"knowledge_bases": service.list_knowledge_bases()}
            match = re_fullmatch(r"/api/v3/library/knowledge-bases/([^/]+)", path)
            if match:
                if self.command == "DELETE":
                    return HTTPStatus.OK, service.delete_knowledge_base(match)
                if self.command == "POST":
                    return HTTPStatus.OK, service.update_knowledge_base(
                        match, name=payload.get("name"), description=payload.get("description"))
                return HTTPStatus.OK, service.get_knowledge_base(match)
            if path == "/api/v3/library/tags":
                return HTTPStatus.OK, {"tags": service.list_tags()}
            if path == "/api/v3/library/documents":
                if self.command == "POST" and payload is not None and payload.get("action") == "import":
                    result = service.import_document(
                        payload.get("path"),
                        knowledge_base_id=payload.get("knowledge_base_id") or "kb-default",
                        tags=payload.get("tags") or (),
                        force=bool(payload.get("force")),
                        dry_run=bool(payload.get("dry_run")),
                    )
                    status = HTTPStatus.CREATED if result.get("import_status") == "READY" else HTTPStatus.OK
                    return status, result
                query = urlsplit(self.path).query
                kb = parse_qs(query).get("kb", [None])[0]
                return HTTPStatus.OK, {"documents": service.list_documents(kb)}
            match = re_fullmatch(r"/api/v3/library/documents/([^/]+)", path)
            if match:
                if self.command == "DELETE":
                    return HTTPStatus.OK, service.delete_document(match)
                if self.command == "GET":
                    return HTTPStatus.OK, service.get_document(match)
                return HTTPStatus.NOT_FOUND, {}
            action = re_fullmatch_groups(r"/api/v3/library/documents/([^/]+)/(enable|disable|retry-index|retry-delete|relink|tags)", path)
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
                        document_id, payload.get("path"),
                        update_if_changed=bool(payload.get("update_if_changed")),
                    )
                tags = service.set_document_tags(document_id, payload.get("tags") or ())
                return HTTPStatus.OK, {"document_id": document_id, "tags": tags}
            return HTTPStatus.NOT_FOUND, {}

        def _is_loopback(self) -> bool:
            return self.client_address[0] in {"127.0.0.1", "::1"}

        def _host_allowed(self) -> bool:
            host = self.headers.get("Host", "").strip().lower()
            return bool(host) and host in owner.allowed_hosts()

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
                        # Keep idle connections alive while the engine works;
                        # embedding can stay silent for a couple of minutes.
                        self._chunk(b'{"event":"ping"}\n')
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

        def _json(self, status: HTTPStatus, payload: dict[str, Any], extra_headers: dict[str, str] | None = None) -> None:
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

        def _error(self, status: HTTPStatus, message: str, extra_headers: dict[str, str] | None = None) -> None:
            self._json(status, {"error": message, "status": int(status)}, extra_headers)

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


def re_fullmatch_groups(pattern: str, value: str) -> tuple[str, ...] | None:
    import re

    match = re.fullmatch(pattern, value)
    return match.groups() if match else None


def scope_cache_key(scope: QueryScope | None) -> str:
    """Cache-key component for a scope: None and empty stay distinct from any
    non-default scope so a scoped answer can never be served unscoped."""
    if scope is None:
        return "none"
    return json.dumps(scope.to_dict(), ensure_ascii=False, sort_keys=True)


def parse_scope_payload(payload: dict) -> QueryScope | None:
    try:
        return QueryScope.from_payload(payload.get("scope"))
    except QueryScopeError as exc:
        raise ValueError(str(exc)) from exc
