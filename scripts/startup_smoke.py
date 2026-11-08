"""P5 startup smoke: start a real local server and verify no library writes.

Uses a fake engine (no Ollama, no Qdrant) and a temporary web root, so it is
safe in a clean clone.  Verifies pairing, health, a v3 route and static
serving, then shuts the server down and asserts the managed library bytes are
unchanged.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import config  # noqa: E402
from desktop.web_server import WebQAServer  # noqa: E402


class FakeEngine:
    answer_model = "test-answer"

    def __init__(self) -> None:
        self.library = None

    def health(self) -> dict:
        return {"ok": True, "chunks": 1, "has_vectors": False}

    def answer(self, *_args, **_kwargs):
        raise AssertionError("startup smoke must not generate an answer")


def _get(url: str, token: str = "") -> tuple[int, str]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def main() -> int:
    db = Path(config.LIBRARY_DB)
    digest_before = hashlib.sha256(db.read_bytes()).hexdigest() if db.is_file() else ""
    with tempfile.TemporaryDirectory(prefix="p5-startup-") as directory:
        root = Path(directory) / "web"
        root.mkdir()
        (root / "index.html").write_text("<!doctype html><title>smoke</title>",
                                         encoding="utf-8")
        server = WebQAServer(FakeEngine(), host="127.0.0.1", port=0,
                             pairing_code="123456", web_root=root)
        server.start()
        try:
            token, _ = server.pair("123456", "127.0.0.1")
            base = server.local_url
            checks = {
                "unauthorized_health": _get(base + "/api/v2/health")[0] == 401,
                "health": _get(base + "/api/v2/health", token)[0] == 200,
                "static": _get(base + "/")[0] == 200,
                "v3_library_no_service": _get(base + "/api/v3/library", token)[0] == 404,
            }
        finally:
            server.stop()
    digest_after = hashlib.sha256(db.read_bytes()).hexdigest() if db.is_file() else ""
    checks["library_bytes_unchanged"] = digest_before == digest_after
    report = {"checks": checks, "result": "PASS" if all(checks.values()) else "FAIL",
              "library_sha256": digest_after[:16]}
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
