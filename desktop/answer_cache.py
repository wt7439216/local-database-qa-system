"""In-process LRU answer cache and library fingerprint (P1 extraction)."""
from __future__ import annotations

from collections import OrderedDict
import threading
from typing import Any

from core import config

ANSWER_CACHE_SIZE = config.SETTINGS.answer_cache_size
CacheKey = tuple[str, str, str, str]


def compute_fingerprint(engine: Any) -> str:
    """Cache identity derived from the loaded library metadata."""
    library = getattr(engine, "library", None)
    metadata = getattr(library, "metadata", None) if library is not None else None
    if not isinstance(metadata, dict):
        return ""
    return str(metadata.get("built_at", "")) + "|" + str(metadata.get("source_sha256", ""))


class AnswerCache:
    def __init__(self, size: int = ANSWER_CACHE_SIZE) -> None:
        self.size = size
        self.store: OrderedDict[CacheKey, dict[str, Any]] = OrderedDict()
        self.lock = threading.Lock()

    def get(self, key: CacheKey) -> dict[str, Any] | None:
        with self.lock:
            cached = self.store.get(key)
            if cached is not None:
                self.store.move_to_end(key)
            return cached

    def put(self, key: CacheKey, result: dict[str, Any]) -> None:
        with self.lock:
            self.store[key] = result
            self.store.move_to_end(key)
            while len(self.store) > self.size:
                self.store.popitem(last=False)

    def clear(self) -> None:
        with self.lock:
            self.store.clear()
