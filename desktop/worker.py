"""Concurrent answer workers (P3).

P1/P2 used a single worker with ``_engine_lock`` held across the whole LLM
call: one slow answer blocked every other job (head-of-line blocking).  P3
runs N workers in parallel and replaces the coarse lock with an *epoch*:

* a mutation bumps the epoch and clears the cache immediately (no waiting for
  an in-flight generation);
* a worker records the epoch before generating and only writes its answer to
  the cache if the epoch is unchanged, so a stale answer can never be
  reinserted after a mutation.

Cancellation is cooperative and deadline-aware via ``AnswerJob.is_cancelled``.
"""
from __future__ import annotations

import queue
import time
from typing import Any

from desktop.jobs import scope_cache_key


def process_job(server: Any, job: Any) -> None:
    if job.is_cancelled():
        if job.timed_out and not job.cancelled.is_set():
            job.status = "failed"
            job.emit("error", message="回答超时，请重试。")
        else:
            job.status = "cancelled"
            job.emit("cancelled")
        job.done = True
        return
    job.status = "running"
    job.emit("status", message="正在检索教材")
    with server._active_lock:
        server._active_jobs += 1
    try:
        with server._state_lock:
            epoch = server._epoch
            fingerprint = server._engine_fingerprint
        cache_key = (
            job.question.strip(),
            fingerprint,
            str(getattr(server.engine, "answer_model", "")),
            scope_cache_key(job.scope),
        )
        cached = None if job.history else server._cache_get(cache_key)
        if cached is not None:
            data = cached
            job.emit("status", message="命中缓存")
        else:
            scope_kwargs = {} if job.scope is None else {"scope": job.scope}
            result = server.engine.answer(
                job.question,
                history=job.history,
                on_token=lambda token: job.emit("token", text=token),
                cancelled=job.is_cancelled,
                **scope_kwargs,
            )
            data = result.to_dict() if hasattr(result, "to_dict") else dict(result)
        if job.is_cancelled():
            raise InterruptedError("回答已取消。")
        if cached is None and not job.history:
            with server._state_lock:
                if server._epoch == epoch:
                    server._cache_put(cache_key, data)
        server._log_answer(job.question, data)
        job.status = "complete"
        job.emit("final", result=data)
    except InterruptedError:
        if job.timed_out and not job.cancelled.is_set():
            job.status = "failed"
            server._log_event("timeout", job.question, "job deadline exceeded")
            job.emit("error", message="回答超时，请重试。")
        else:
            job.status = "cancelled"
            server._log_event("cancelled", job.question, "")
            job.emit("cancelled")
    except Exception as exc:
        job.status = "failed"
        server._log_event("error", job.question, str(exc))
        job.emit("error", message=str(exc))
    finally:
        with server._active_lock:
            server._active_jobs -= 1
        job.done = True
        with job.condition:
            job.condition.notify_all()


def work_loop(server: Any) -> None:
    """One of N worker threads; exits on the shared stop event."""
    while not server._workers_stop.is_set():
        try:
            job = server._queue.get(timeout=0.2)
        except queue.Empty:
            continue
        if job is None:
            server._queue.task_done()
            return
        try:
            process_job(server, job)
        finally:
            server._queue.task_done()


def prune_jobs(server: Any) -> None:
    cutoff = time.time() - server.job_retention_seconds
    with server._jobs_lock:
        stale = [
            key for key, job in server._jobs.items()
            if job.done and job.created_at < cutoff
        ]
        for key in stale:
            server._jobs.pop(key, None)
