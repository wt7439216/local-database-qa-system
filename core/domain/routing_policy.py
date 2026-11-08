"""Route-dependent retrieval policy (P2 extraction)."""
from __future__ import annotations

from core import config


class RoutePolicy:
    """Replaces the inline top_k/per_k ternaries that lived in engine_v2."""

    def __init__(self, settings=config.RETRIEVAL) -> None:
        self.settings = settings

    def top_k(self, route: str) -> int:
        return self.settings.top_k(route)

    def compare_k(self, query_count: int) -> int:
        return self.settings.compare_k(query_count)

    def include_front_matter(self, route: str) -> bool:
        return route in {"qa", "compare"}


ROUTE_POLICY = RoutePolicy()
