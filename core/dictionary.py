"""Domain dictionary for Chinese FTS tokenisation (P4, stdlib-only).

The default index uses 2/3-gram sliding windows: robust but noisy (e.g.
「移动通信」 also produces 「动通」).  P4 adds an **optional** dictionary layer
that also indexes complete domain terms found in the library itself:

1. ``scripts/build_domain_dictionary.py`` mines document-frequency statistics
   from ``chunks.text`` and writes ``data/library/domain_dictionary.txt``.
2. ``QA_FTS_DICTIONARY=1`` makes ``core.tokenizer.fts_terms`` add those terms
   on BOTH the index and the query side (symmetry is preserved).
3. ``scripts/rebuild_fts_index.py --apply`` rebuilds the derived ``chunk_fts``
   table.  SQLite stays the single source of truth.

All of this is off by default; with the switch off or no dictionary file the
tokeniser output is byte-for-byte identical to P0-P3.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
import re
from typing import Iterable

CJK_RE = re.compile(r"[\u4e00-\u9fff]+")
# Function words virtually never occur inside a genuine Chinese domain term.
# Filtering them removes most sliding-window fragments (「…信道的传输」).
STOP_CHARS = frozenset("的了在是与和到中对从把被由等这那其之为以及或个种可能会将已并而但则也都就更最要所把使让给向于上下面第有着得很")


def default_dictionary_path() -> Path:
    from core import config

    return Path(config.LIBRARY_DB).parent / "domain_dictionary.txt"


class DomainDictionary:
    """Immutable word set with longest-match segmentation."""

    def __init__(self, words: Iterable[str]) -> None:
        self.words = frozenset(word for word in words if len(word) >= 2)
        self.max_len = max((len(word) for word in self.words), default=0)

    def __len__(self) -> int:
        return len(self.words)

    def __bool__(self) -> bool:
        return bool(self.words)

    @classmethod
    def from_chunks(
        cls,
        texts: Iterable[str],
        *,
        min_df: int = 2,
        max_terms: int = 1500,
        min_len: int = 3,
        max_len: int = 6,
        min_branch: int = 3,
    ) -> "DomainDictionary":
        """Mine complete CJK terms by document frequency and boundary diversity.

        A candidate must appear in at least ``min_df`` distinct chunks **and**
        have at least ``min_branch`` distinct left/right neighbouring characters.
        The boundary test is what removes sliding-window fragments such as
        「信道到物理信道的」: fragments are almost always embedded in one fixed
        longer phrase, while real domain terms occur in many contexts.  Short
        sub-terms covered by a longer equally frequent term are pruned too.
        """
        counts: Counter[str] = Counter()
        left: dict[str, set[str]] = defaultdict(set)
        right: dict[str, set[str]] = defaultdict(set)
        for text in texts:
            seen: set[str] = set()
            for run in CJK_RE.findall(text or ""):
                length = len(run)
                for size in range(min_len, min(max_len, length) + 1):
                    for index in range(length - size + 1):
                        word = run[index:index + size]
                        seen.add(word)
                        left[word].add(run[index - 1] if index > 0 else "^")
                        right[word].add(run[index + size] if index + size < length else "$")
            counts.update(seen)
        candidates = sorted(
            (
                (word, count) for word, count in counts.items()
                if count >= min_df
                and len(left[word]) >= min_branch
                and len(right[word]) >= min_branch
                and not any(char in STOP_CHARS for char in word)
            ),
            key=lambda item: (-item[1], -len(item[0]), item[0]),
        )
        kept: list[tuple[str, int]] = []
        for word, count in candidates[: max_terms * 6]:
            redundant = any(
                len(longer) > len(word) and word in longer and longer_count >= count * 0.85
                for longer, longer_count in kept[:400]
            )
            if not redundant:
                kept.append((word, count))
            if len(kept) >= max_terms:
                break
        return cls(word for word, _ in kept)

    def _forward(self, run: str) -> list[str]:
        result: list[str] = []
        index = 0
        while index < len(run):
            matched = None
            for size in range(min(self.max_len, len(run) - index), 1, -1):
                candidate = run[index:index + size]
                if candidate in self.words:
                    matched = candidate
                    break
            if matched:
                result.append(matched)
                index += len(matched)
            else:
                index += 1
        return result

    def _backward(self, run: str) -> list[str]:
        result: list[str] = []
        index = len(run)
        while index > 0:
            matched = None
            for size in range(min(self.max_len, index), 1, -1):
                candidate = run[index - size:index]
                if candidate in self.words:
                    matched = candidate
                    break
            if matched:
                result.append(matched)
                index -= len(matched)
            else:
                index -= 1
        result.reverse()
        return result

    def segment(self, text: str) -> list[str]:
        """Bidirectional maximum matching; fewer tokens wins (longer terms)."""
        if not self.words:
            return []
        result: list[str] = []
        for match in CJK_RE.finditer(text or ""):
            run = match.group(0)
            forward = self._forward(run)
            backward = self._backward(run)
            chosen = forward if len(forward) <= len(backward) else backward
            result.extend(chosen)
        return result

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(sorted(self.words, key=lambda word: (-len(word), word))) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> "DomainDictionary":
        if not path.is_file():
            return cls(())
        words = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
        return cls(word for word in words if word and not word.startswith("#"))


@lru_cache(maxsize=8)
def _cached(path: str, mtime_ns: int) -> DomainDictionary:  # noqa: ARG001
    return DomainDictionary.load(Path(path))


def load_dictionary(path: Path | None = None) -> DomainDictionary:
    """Load with mtime-based invalidation (a rebuild is picked up in-process)."""
    target = Path(path) if path is not None else default_dictionary_path()
    if not target.is_file():
        return DomainDictionary(())
    return _cached(str(target.resolve()), target.stat().st_mtime_ns)
