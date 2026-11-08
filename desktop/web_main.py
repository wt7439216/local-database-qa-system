"""Launch the v2 local textbook server and responsive web interface."""

from __future__ import annotations

import argparse
import os
import signal
import sys
import webbrowser

from core import config
from core.engine_v2 import StructuredQAEngine
from core.library_service import LibraryService
from core.path_policy import ImportPathPolicy
from core.runtime_library import resolve_runtime_library
from desktop.web_server import DEFAULT_PORT, WebQAServer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="本地教材问答 v2")
    parser.add_argument("--host", default=config.SETTINGS.default_host)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--modern", action="store_true",
                        help="使用可选 FastAPI/uvicorn 栈（需安装 fastapi/uvicorn/httpx）")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    # P0: 防止把教材片段/问题发到非本机地址（QA_ALLOW_REMOTE_SERVICES=1 显式放行）。
    config.validate_service_urls()
    # Phase D.1 runtime integration: engine and manager share ONE library
    # identity (see core/runtime_library.py for the static selection rules).
    library_path = resolve_runtime_library()
    engine = StructuredQAEngine(library_path)
    # Phase D: managed general-documents library (v5 registry).  The manager
    # page and /api/v3/library endpoints fail soft when this is unavailable.
    # Security closure: web-triggered path imports are confined to the
    # configured LIBRARY_IMPORT_ROOTS (disabled entirely when none are set).
    try:
        library_service = LibraryService(
            library_path, path_policy=ImportPathPolicy(config.LIBRARY_IMPORT_ROOTS)
        )
    except Exception as exc:
        # P0: 不再静默降级成「v3 API 全部 404」，启动阶段就明确失败。
        raise RuntimeError(f"知识库管理初始化失败：{exc}") from exc
    if args.modern:
        from desktop.modern_app import ModernServer

        server = ModernServer(
            engine, host=args.host, port=args.port,
            pairing_code=config.SETTINGS.pairing_code or None,
            library_service=library_service,
        )
        mutation_hook = server.owner._on_library_mutated
    else:
        server = WebQAServer(
            engine, host=args.host, port=args.port,
            pairing_code=config.SETTINGS.pairing_code or None,
            library_service=library_service,
        )
        mutation_hook = server._on_library_mutated
    # Phase D.1: every committed library mutation re-syncs the QA runtime
    # (snapshots, dense index, fingerprint, answer cache) in place.
    library_service.on_mutated = mutation_hook
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
