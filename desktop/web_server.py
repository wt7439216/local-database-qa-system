"""Web application server (P1): composition root + compatibility façade.

The HTTP implementation now lives in focused modules:

* ``jobs.py``          — AnswerJob, request payload helpers
* ``auth.py``          — pairing/token auth and Host policy
* ``answer_cache.py``  — LRU answer cache and library fingerprint
* ``transport.py``     — JSON/static/NDJSON transport helpers
* ``routes_v3.py``     — v3 library route table (pure function)
* ``handler.py``       — v2/v3 request routing
* ``worker.py``        — answer queue loop

Every name previously exported from this module is re-exported below so
existing imports (``from desktop.web_server import ...``) keep working.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
import queue
import secrets
import threading
from http.server import ThreadingHTTPServer
from typing import Any

from core import config
from core.query_scope import QueryScope
from desktop.answer_cache import ANSWER_CACHE_SIZE, AnswerCache, compute_fingerprint
from desktop.auth import (
    AUTH_BLOCK_SECONDS,
    AUTH_FAILURE_LIMIT,
    AUTH_FAILURE_RETENTION_SECONDS,
    LOOPBACK_BIND,
    TOKEN_LIFETIME_SECONDS,
    AuthManager,
    HostPolicy,
    create_pairing_code,
    discover_lan_addresses,
)
from desktop.handler import make_handler
from desktop.jobs import (
    MAX_HISTORY_TURNS,
    AnswerJob,
    parse_scope_payload,
    re_fullmatch,
    re_fullmatch_groups,
    sanitize_history,
    scope_cache_key,
)
from desktop.transport import CONTENT_SECURITY_POLICY, MAX_BODY_BYTES
from desktop.worker import prune_jobs, work_loop

API_VERSION = config.SETTINGS.api_version
DEFAULT_PORT = config.SETTINGS.default_port
JOB_RETENTION_SECONDS = config.SETTINGS.job_retention_seconds
JOB_QUEUE_SIZE = config.SETTINGS.job_queue_size
WEB_ROOT = Path(__file__).resolve().parents[1] / "web"

__all__ = [
    "API_VERSION", "ANSWER_CACHE_SIZE", "AUTH_BLOCK_SECONDS", "AUTH_FAILURE_LIMIT",
    "AUTH_FAILURE_RETENTION_SECONDS", "CONTENT_SECURITY_POLICY", "DEFAULT_PORT",
    "JOB_QUEUE_SIZE", "JOB_RETENTION_SECONDS", "MAX_BODY_BYTES", "MAX_HISTORY_TURNS",
    "TOKEN_LIFETIME_SECONDS", "WEB_ROOT", "AnswerCache", "AnswerJob", "AuthManager",
    "HostPolicy", "QAThreadingHTTPServer", "WebQAServer", "create_pairing_code",
    "discover_lan_addresses", "make_handler", "parse_scope_payload", "re_fullmatch",
    "re_fullmatch_groups", "sanitize_history", "scope_cache_key",
]


class QAThreadingHTTPServer(ThreadingHTTPServer):
    # Windows maps SO_REUSEADDR to "another process may silently steal this
    # port"; refusing reuse is safer, and start() falls back to a random port.
    allow_reuse_address = False


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
        self.auth = AuthManager(self.pairing_code)
        # Compatibility aliases for code/tests that read the old private state.
        self._tokens = self.auth.tokens
        self._auth_failures = self.auth.failures
        self._token_lock = self.auth.lock
        self.host_policy = HostPolicy()
        self.web_root = Path(web_root or WEB_ROOT).resolve()
        self.logger = self._build_logger(log_file)

        self.answer_cache = AnswerCache()
        self._answer_cache = self.answer_cache.store
        self._cache_lock = self.answer_cache.lock
        self._recompute_fingerprint()

        self._jobs: dict[str, AnswerJob] = {}
        self._jobs_lock = threading.Lock()
        self._engine_lock = threading.Lock()  # kept for compatibility
        self._queue: queue.Queue[AnswerJob | None] = queue.Queue(maxsize=JOB_QUEUE_SIZE)
        self.job_retention_seconds = JOB_RETENTION_SECONDS
        self.shutdown_requested = threading.Event()
        # P3 concurrency: N workers + epoch-based cache invalidation.
        self._state_lock = threading.RLock()
        self._epoch = 0
        self._active_lock = threading.Lock()
        self._active_jobs = 0
        self.answer_workers = config.SETTINGS.answer_workers
        self._workers_stop = threading.Event()
        self._workers: list[threading.Thread] = []
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._worker: threading.Thread | None = None  # legacy alias

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
        """Rebuild the cache fingerprint from the current library metadata."""
        self._engine_fingerprint = compute_fingerprint(self.engine)

    def _on_library_mutated(self) -> None:
        """After a committed library mutation, re-sync the QA runtime in place.

        P3: bump an epoch instead of holding a global lock across generation.
        In-flight answers keep their own snapshot but cannot repopulate the
        fresh cache (workers check the epoch before writing).
        """
        with self._state_lock:
            library = getattr(self.engine, "library", None)
            if library is not None and hasattr(library, "refresh"):
                library.refresh()
            self._recompute_fingerprint()
            self._epoch += 1
            self.answer_cache.clear()

    def _cache_get(self, key: tuple[str, str, str, str]) -> dict[str, Any] | None:
        return self.answer_cache.get(key)

    def _cache_put(self, key: tuple[str, str, str, str], result: dict[str, Any]) -> None:
        self.answer_cache.put(key, result)

    @staticmethod
    def _compact(text: Any, limit: int = 200) -> str:
        return json.dumps(str(text)[:limit], ensure_ascii=False)

    def _log_answer(self, question: str, data: dict[str, Any]) -> None:
        if not self.logger:
            return
        self.logger.info(
            "answer route=%s mode=%s confidence=%s out_of_scope=%s elapsed_ms=%s question=%s",
            data.get("route", ""), data.get("retrieval_mode", ""),
            data.get("confidence", ""), data.get("out_of_scope", ""),
            data.get("elapsed_ms", ""), self._compact(question),
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
        if self.host in LOOPBACK_BIND:
            return [self.local_url]
        return [f"http://{address}:{self.port}" for address in discover_lan_addresses()] or [self.local_url]

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def allowed_hosts(self) -> set[str]:
        """Host header values this service accepts (DNS-rebinding defence)."""
        return self.host_policy.allowed(self.host, self.port)

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
        # P3: a pool of independent workers removes head-of-line blocking.
        self._workers_stop.clear()
        self._workers = [
            threading.Thread(target=self._work_loop, name=f"qa-worker-{index}", daemon=True)
            for index in range(self.answer_workers)
        ]
        self._worker = self._workers[0] if self._workers else None
        self._thread.start()
        for worker in self._workers:
            worker.start()

    def stop(self) -> None:
        httpd = self._httpd
        self._httpd = None
        if httpd:
            httpd.shutdown()
            httpd.server_close()
        self._workers_stop.set()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        for thread in [self._thread, *self._workers]:
            if thread and thread is not threading.current_thread():
                thread.join(timeout=3)
        self._thread = None
        self._workers = []
        self._worker = None
        if self.logger is not None:
            for handler in list(self.logger.handlers):
                handler.close()
                self.logger.removeHandler(handler)

    def pair(self, code: str, client_ip: str) -> tuple[str | None, int]:
        return self.auth.pair(code, client_ip)

    def authorized(self, authorization: str) -> bool:
        return self.auth.authorized(authorization)

    def _check_pairing_code(self, code: str, client_ip: str) -> tuple[bool, int]:
        return self.auth.check_pairing_code(code, client_ip)

    def health(self) -> dict[str, Any]:
        data = dict(self.engine.health())
        data.update({
            "service": "local-textbook-qa", "api_version": API_VERSION,
            "queue_depth": self._queue.qsize(), "lan_urls": self.lan_urls,
            "active_workers": self._active_jobs,
            "worker_count": self.answer_workers,
        })
        return data

    def create_job(
        self,
        question: str,
        history: list[dict[str, str]] | None = None,
        scope: QueryScope | None = None,
    ) -> AnswerJob:
        prune_jobs(self)
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

    def job_status(self, job_id: str) -> dict[str, Any] | None:
        """P3: lightweight status probe (no event stream)."""
        job = self.get_job(job_id)
        return job.to_status() if job else None

    def _prune_jobs(self) -> None:
        prune_jobs(self)

    def _work_loop(self) -> None:
        work_loop(self)
