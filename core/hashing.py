"""Shared hashing helpers (P1): one implementation for the whole codebase.

Previously ``hashlib.sha256(...).hexdigest()`` was duplicated in a dozen
modules, with three slightly different file-hashing implementations.  All
helpers here are byte-for-byte equivalent to the originals.
"""
from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str, encoding: str = "utf-8") -> str:
    return sha256_bytes(text.encode(encoding))


def sha256_file(path: Path | str) -> str:
    """Streaming hash; safe for large PDF/SQLite files."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def short_id(prefix: str, payload: str, length: int = 12) -> str:
    """Stable short identifier, e.g. ``doc-`` / ``sec-`` / ``chp-``."""
    return prefix + sha256_text(payload)[:length]


def canonical_lf_bytes(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
