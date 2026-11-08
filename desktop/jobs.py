"""Answer job state machine and request payload helpers (P1 extraction).

Pure of HTTP concerns: these used to live inside ``desktop/web_server.py``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
import threading
import time
from typing import Any

from core import config
from core.query_scope import QueryScope, QueryScopeError

MAX_HISTORY_TURNS = config.SETTINGS.max_history_turns


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
        turn: dict[str, Any] = {
            "question": question.strip()[:2000],
            "answer": answer.strip()[:6000],
        }
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
    # P3: cooperative per-job deadline (checked by the streaming client too).
    timeout_at: float = 0.0

    def __post_init__(self) -> None:
        if not self.timeout_at:
            self.timeout_at = self.created_at + config.SETTINGS.job_timeout_seconds

    @property
    def timed_out(self) -> bool:
        return time.time() >= self.timeout_at

    def is_cancelled(self) -> bool:
        """Cancellation or deadline — the callback passed into the engine."""
        return self.cancelled.is_set() or self.timed_out

    def emit(self, event: str, **payload: Any) -> None:
        with self.condition:
            self.events.append({"event": event, **payload})
            self.condition.notify_all()

    def to_status(self) -> dict[str, Any]:
        return {
            "job_id": self.id,
            "status": self.status,
            "done": self.done,
            "created_at": self.created_at,
            "event_count": len(self.events),
            "cancelled": self.cancelled.is_set(),
            "timed_out": self.timed_out,
        }


def re_fullmatch(pattern: str, value: str) -> str | None:
    match = re.fullmatch(pattern, value)
    return match.group(1) if match else None


def re_fullmatch_groups(pattern: str, value: str) -> tuple[str, ...] | None:
    match = re.fullmatch(pattern, value)
    return match.groups() if match else None


def scope_cache_key(scope: QueryScope | None) -> str:
    """Cache-key component: None and empty stay distinct from any non-default scope."""
    if scope is None:
        return "none"
    if scope.matches_nothing:
        return "nothing"
    return json.dumps(scope.to_dict(), ensure_ascii=False, sort_keys=True)


def parse_scope_payload(payload: dict) -> QueryScope | None:
    try:
        return QueryScope.from_payload(payload.get("scope"))
    except QueryScopeError as exc:
        raise ValueError(str(exc)) from exc
