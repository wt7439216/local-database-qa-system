"""Single SQLite connection factory (P1).

The codebase used six slightly different connect recipes (timeout, FK,
row_factory, read-only URI).  New code should use :func:`connect`; the
parameters reproduce the exact behaviour of each legacy call site.
"""
from __future__ import annotations

from pathlib import Path
import sqlite3


def connect(
    path: Path | str,
    *,
    readonly: bool = False,
    timeout: float = 30.0,
    foreign_keys: bool = True,
    row_factory: object = sqlite3.Row,
) -> sqlite3.Connection:
    if readonly:
        uri = Path(path).resolve().as_uri() + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True, timeout=timeout)
    else:
        connection = sqlite3.connect(path, timeout=timeout)
    if row_factory is not None:
        connection.row_factory = row_factory  # type: ignore[assignment]
    if not readonly and foreign_keys:
        connection.execute("PRAGMA foreign_keys = ON")
    return connection
