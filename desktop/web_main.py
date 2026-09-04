"""Launch the v2 local textbook server and responsive web interface."""

from __future__ import annotations

import argparse
import os
import signal
import sys
import threading
import webbrowser

from core.engine_v2 import StructuredQAEngine
from desktop.web_server import DEFAULT_PORT, WebQAServer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="本地教材问答 v2")
    parser.add_argument("--host", default=os.getenv("QA_DESKTOP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("QA_DESKTOP_PORT", str(DEFAULT_PORT))))
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    engine = StructuredQAEngine()
    server = WebQAServer(engine, host=args.host, port=args.port, pairing_code=os.getenv("QA_PAIRING_CODE") or None)
    server.start()
    print(f"本机地址：{server.local_url}")
    print(f"配对码：{server.pairing_code}")
    for url in server.lan_urls:
        print(f"局域网地址：{url}")
    if not args.no_browser:
        webbrowser.open(server.local_url)

    def stop(*_args) -> None:
        server.shutdown_requested.set()

    signal.signal(signal.SIGINT, stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, stop)
    try:
        while not server.shutdown_requested.wait(0.5):
            pass
    finally:
        server.stop()
    # A windowed PyInstaller process can otherwise be retained by a native
    # runtime thread after the HTTP listener has closed.
    if getattr(sys, "frozen", False):
        os._exit(0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
