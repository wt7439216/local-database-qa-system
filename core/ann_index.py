"""IVF (inverted-file) ANN index — pure Python standard library (P4).

The SQLite backend used to compute a full O(N·D) dot-product scan for every
query.  This module clusters the (already L2-normalised) vectors into a small
number of spherical k-means centroids at load time, then a query only scans
``nprobe`` nearest lists.  SQLite remains the single source of truth; the
index is an in-memory derived structure rebuilt on every ``_load()``.

Opt-in via ``QA_VECTOR_ANN=1``; with the switch off nothing changes and no
third-party dependency is introduced (``math.sumprod`` on 3.12+, otherwise a
small Python fallback).
"""
from __future__ import annotations

from array import array
import math
import random

try:
    from math import sumprod as _dot  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - Python < 3.12
    def _dot(left, right):  # type: ignore[misc]
        return sum(a * b for a, b in zip(left, right))


def _normalize(values) -> array:
    data = array("f", (float(value) for value in values))
    norm = math.sqrt(_dot(data, data))
    if norm <= 0:
        return data
    return array("f", (value / norm for value in data))


class IVFIndex:
    """Immutable coarse-quantiser index over a flat float32 vector array."""

    def __init__(
        self,
        vectors,
        dimension: int,
        centroids: list[array],
        lists: list[list[int]],
        nprobe: int,
    ) -> None:
        self.vectors = vectors
        self.dimension = dimension
        self.centroids = centroids
        self.lists = lists
        self.nprobe = max(1, min(nprobe, len(centroids)))
        self.total = sum(len(items) for items in lists)
        self.last_scanned = 0

    @classmethod
    def build(
        cls,
        vectors,
        dimension: int,
        *,
        n_clusters: int = 64,
        nprobe: int = 8,
        seed: int = 17,
        max_iter: int = 6,
        train_limit: int = 1024,
    ) -> "IVFIndex | None":
        """Return None when the corpus is too small for ANN to be worthwhile."""
        if dimension <= 0 or not vectors:
            return None
        total = len(vectors) // dimension
        k = min(max(1, n_clusters), total)
        if total < k * 2:
            return None
        view = memoryview(vectors)
        rng = random.Random(seed)
        positions = list(range(total))
        if total > train_limit:
            rng.shuffle(positions)
            positions = positions[:train_limit]
        chosen = rng.sample(positions, min(k, len(positions)))
        centroids = [
            _normalize(view[p * dimension:(p + 1) * dimension]) for p in chosen
        ]
        while len(centroids) < k:
            centroids.append(array("f", centroids[len(centroids) % max(1, len(chosen))]))

        for _ in range(max_iter):
            sums = [array("d", [0.0]) * dimension for _ in range(k)]
            counts = [0] * k
            for position in positions:
                vector = view[position * dimension:(position + 1) * dimension]
                best = max(range(k), key=lambda c: _dot(vector, centroids[c]))
                target = sums[best]
                for index, value in enumerate(vector):
                    target[index] += value
                counts[best] += 1
            for cluster in range(k):
                if counts[cluster]:
                    centroids[cluster] = _normalize(sums[cluster])

        lists: list[list[int]] = [[] for _ in range(k)]
        for position in range(total):
            vector = view[position * dimension:(position + 1) * dimension]
            best = max(range(k), key=lambda c: _dot(vector, centroids[c]))
            lists[best].append(position)
        return cls(view, dimension, centroids, lists, nprobe)

    def search(self, query, limit: int, allowed: set[int] | None = None):
        """Return ``[(score, position), ...]`` ordered exactly like brute force."""
        if limit <= 0:
            return []
        centroid_scores = [_dot(query, centroid) for centroid in self.centroids]
        probe = sorted(
            range(len(self.centroids)),
            key=lambda cluster: (-centroid_scores[cluster], -cluster),
        )[: self.nprobe]
        dimension = self.dimension
        scored: list[tuple[float, int]] = []
        for cluster in probe:
            for position in self.lists[cluster]:
                if allowed is not None and position not in allowed:
                    continue
                vector = self.vectors[position * dimension:(position + 1) * dimension]
                scored.append((_dot(query, vector), position))
        self.last_scanned = len(scored)
        scored.sort(reverse=True)
        return scored[: max(1, int(limit))]

    @property
    def coverage(self) -> float:
        """Fraction of the corpus scanned by the most recent query."""
        return self.last_scanned / self.total if self.total else 0.0
