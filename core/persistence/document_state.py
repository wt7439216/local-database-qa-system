"""Document lifecycle state machine — single source of truth (P4).

The status strings are part of the v3 HTTP contract, so they stay verbatim.
This module centralises the *policy* (which transition an operation may
perform) that was previously repeated as ad-hoc ``status in {...}`` checks
inside ``LibraryService``.  Soft-disable (``enabled``) is orthogonal to
``status`` and deliberately has no state here.
"""
from __future__ import annotations

DOCUMENT_STATUSES = (
    "IMPORTING", "READY", "UPDATING", "FAILED", "FAILED_INDEX",
    "DELETING", "DELETE_FAILED",
)
RETRIEVABLE_STATUSES = ("READY",)

# Persisted statuses only.  Result codes (UNCHANGED / DELETED / RELINKED /
# SOURCE_CHANGED) are API responses, not registry states.
TRANSITIONS: dict[str, frozenset[str]] = {
    "IMPORTING": frozenset({"READY", "FAILED", "FAILED_INDEX", "DELETING"}),
    "UPDATING": frozenset({"READY", "FAILED", "FAILED_INDEX", "DELETING"}),
    "READY": frozenset({"UPDATING", "FAILED_INDEX", "DELETING"}),
    "FAILED": frozenset({"UPDATING", "IMPORTING", "DELETING"}),
    "FAILED_INDEX": frozenset({"READY", "UPDATING", "DELETING"}),
    "DELETING": frozenset({"DELETE_FAILED", "DELETING"}),
    "DELETE_FAILED": frozenset({"DELETING", "UPDATING", "IMPORTING"}),
}

_NON_RELINKABLE = frozenset({"DELETING", "DELETE_FAILED"})
_NON_ENABLEABLE = frozenset({"DELETING", "DELETE_FAILED"})


def is_retrievable(status: str) -> bool:
    return status in RETRIEVABLE_STATUSES


def can_relink(status: str) -> bool:
    return status not in _NON_RELINKABLE


def can_set_enabled(status: str) -> bool:
    return status not in _NON_ENABLEABLE


def can_retry_delete(status: str) -> bool:
    return status == "DELETE_FAILED"


def can_retry_index(status: str) -> bool:
    return status == "FAILED_INDEX"


def assert_transition(current: str, target: str) -> None:
    """Raise ValueError for an impossible persisted-state transition.

    Diagnostic helper for migrations/tests; the service keeps its own
    ``LibraryStateError`` messages so HTTP responses stay unchanged.
    """
    if current not in DOCUMENT_STATUSES or target not in DOCUMENT_STATUSES:
        raise ValueError(f"未知文档状态：{current!r} -> {target!r}")
    if target not in TRANSITIONS[current]:
        raise ValueError(f"非法状态转移：{current} -> {target}")
