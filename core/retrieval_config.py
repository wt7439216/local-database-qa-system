"""Centralised retrieval / generation tuning knobs (P2).

Previously these constants were frozen inside ``hybrid_retriever.py``,
``library_store.py`` and ``engine_v2.py``.  They are now one dataclass, still
with the exact same defaults, and can be overridden per process with
``QA_RETRIEVAL_*`` environment variables for offline calibration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import os


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv("QA_RETRIEVAL_" + name, str(default)))
    except ValueError:
        return default


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv("QA_RETRIEVAL_" + name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class RetrievalSettings:
    # --- RRF fusion ---------------------------------------------------------
    rrf_k: float = 60.0
    lexical_weight: float = 1.0
    dense_weight: float = 1.25
    section_limit: int = 2
    two_char_min_chunks: int = 5
    two_char_min_dense: float = 0.30

    # --- lexical search -----------------------------------------------------
    fts_body_weight: float = 1.0
    fts_heading_weight: float = 4.0
    fts_heading_bonus: float = 0.006
    dense_candidate_floor: float = 0.15
    dense_gates: dict[str, float] = field(default_factory=lambda: {
        "strong": 0.48, "accept": 0.55, "dense_only": 0.50,
    })

    # --- routing / context budget -------------------------------------------
    top_k_locate_chapter: int = 10
    top_k_compare: int = 7
    top_k_default: int = 5
    min_compare_k: int = 3
    prompt_reserve: int = 600
    min_prompt_budget: int = 1200

    @classmethod
    def from_env(cls) -> "RetrievalSettings":
        gates = {
            "strong": _float("GATE_STRONG", 0.48),
            "accept": _float("GATE_ACCEPT", 0.55),
            "dense_only": _float("GATE_DENSE_ONLY", 0.50),
        }
        return cls(
            rrf_k=_float("RRF_K", 60.0),
            lexical_weight=_float("LEXICAL_WEIGHT", 1.0),
            dense_weight=_float("DENSE_WEIGHT", 1.25),
            section_limit=_int("SECTION_LIMIT", 2),
            two_char_min_chunks=_int("TWO_CHAR_MIN_CHUNKS", 5),
            two_char_min_dense=_float("TWO_CHAR_MIN_DENSE", 0.30),
            fts_body_weight=_float("FTS_BODY_WEIGHT", 1.0),
            fts_heading_weight=_float("FTS_HEADING_WEIGHT", 4.0),
            fts_heading_bonus=_float("FTS_HEADING_BONUS", 0.006),
            dense_candidate_floor=_float("DENSE_CANDIDATE_FLOOR", 0.15),
            dense_gates=gates,
            top_k_locate_chapter=_int("TOP_K_LOCATE_CHAPTER", 10),
            top_k_compare=_int("TOP_K_COMPARE", 7),
            top_k_default=_int("TOP_K_DEFAULT", 5),
            min_compare_k=_int("MIN_COMPARE_K", 3),
            prompt_reserve=_int("PROMPT_RESERVE", 600),
            min_prompt_budget=_int("MIN_PROMPT_BUDGET", 1200),
        )

    def top_k(self, route: str) -> int:
        """Route-dependent candidate count (was an inline ternary in engine_v2)."""
        if route == "locate_chapter":
            return self.top_k_locate_chapter
        if route == "compare":
            return self.top_k_compare
        return self.top_k_default

    def compare_k(self, query_count: int) -> int:
        """Per-entity candidate count for compare routes."""
        divisor = max(1, query_count)
        return max(self.min_compare_k, self.top_k("compare") // divisor + 1)

    def prompt_budget(self, context_window: int, num_predict: int) -> int:
        return max(
            self.min_prompt_budget,
            context_window - num_predict - self.prompt_reserve,
        )
