"""Cancellable NDJSON streaming client (P3).

* When ``httpx`` is installed (modern stack / dev / CI) it is used, with a
  watchdog thread that closes the response as soon as cancellation is
  signalled — so a stalled model can be interrupted, not just ignored.
* Otherwise the standard-library urllib opener is used, keeping the default
  runtime **zero third-party dependency** as before.  Cancellation is still
  checked between lines (cooperative).

Neither path changes the wire format or the JSON-lines semantics.
"""
from __future__ import annotations

from collections.abc import Callable, Iterator
import json
import threading
from typing import Any
import urllib.request


def _proxy_free_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _urllib_stream(
    url: str,
    payload: dict[str, Any],
    timeout: float,
    cancelled: Callable[[], bool] | None,
) -> Iterator[str]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Accept": "application/x-ndjson", "Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with _proxy_free_opener().open(request, timeout=timeout) as response:
        while True:
            if cancelled is not None and cancelled():
                raise InterruptedError("回答已取消。")
            line = response.readline()
            if not line:
                break
            if line.strip():
                yield line.decode("utf-8")


def _httpx_stream(
    url: str,
    payload: dict[str, Any],
    timeout: float,
    cancelled: Callable[[], bool] | None,
) -> Iterator[str]:
    import httpx

    with httpx.stream(
        "POST", url, json=payload,
        headers={"Accept": "application/x-ndjson"},
        timeout=httpx.Timeout(timeout, connect=10.0),
    ) as response:
        response.raise_for_status()
        stop = threading.Event()

        def watchdog() -> None:
            while not stop.wait(0.1):
                if cancelled is not None and cancelled():
                    # Closing from the watchdog interrupts a blocked read.
                    try:
                        response.close()
                    except Exception:
                        pass
                    return

        watcher = threading.Thread(target=watchdog, name="qa-stream-cancel", daemon=True)
        watcher.start()
        try:
            for line in response.iter_lines():
                if cancelled is not None and cancelled():
                    raise InterruptedError("回答已取消。")
                if line.strip():
                    yield line
        finally:
            stop.set()
            watcher.join(timeout=0.5)


def stream_ndjson(
    url: str,
    payload: dict[str, Any],
    *,
    timeout: float = 600.0,
    cancelled: Callable[[], bool] | None = None,
    prefer_httpx: bool = True,
) -> Iterator[str]:
    """Yield NDJSON lines from a streaming POST, honouring cancellation."""
    if prefer_httpx:
        try:
            import httpx  # noqa: F401
        except ImportError:
            prefer_httpx = False
    iterator = (
        _httpx_stream(url, payload, timeout, cancelled) if prefer_httpx
        else _urllib_stream(url, payload, timeout, cancelled)
    )
    yield from iterator
