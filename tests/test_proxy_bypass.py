"""Proxy-policy isolation tests for the local HTTP clients.

Contract (closure audit): loopback hosts (127.0.0.1, localhost, ::1) must be
reached DIRECTLY even when HTTP_PROXY / HTTPS_PROXY point at a local proxy
such as 127.0.0.1:7890; non-loopback hosts keep urllib's default proxy
behavior.  Git proxy configuration is out of scope here and is never touched.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
import threading
import unittest
import urllib.request
from unittest.mock import MagicMock, Mock, patch

from core.ollama_http import OllamaClient, is_loopback_url, open_request
from core.qdrant_store import QdrantVectorStore

PROXY = "http://127.0.0.1:7890"
PROXY_ENV = {
    "HTTP_PROXY": PROXY,
    "HTTPS_PROXY": PROXY,
    "http_proxy": PROXY,
    "https_proxy": PROXY,
}


class _Handler(BaseHTTPRequestHandler):
    server_version = "LocalProbe/1"

    def _reply(self, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802
        if self.path.startswith("/api/tags"):
            self._reply({"models": [{"name": "probe-model"}]})
        else:
            self._reply({"title": "qdrant - vector search engine", "version": "probe"})

    def log_message(self, format, *args):  # noqa: A002
        return


class LoopbackProxyBypassTests(unittest.TestCase):
    """A: with proxy env set, loopback requests still reach the local servers.

    The proxy at 127.0.0.1:7890 does not exist; if either client routed
    through it the request would fail with connection refused.  Success is
    therefore proof of a direct loopback connection.
    """

    def setUp(self):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.httpd.shutdown)
        self.addCleanup(self.httpd.server_close)
        env = patch.dict(os.environ, PROXY_ENV)
        env.start()
        self.addCleanup(env.stop)

    def test_ollama_loopback_is_direct_under_proxy_env(self):
        client = OllamaClient(base_url=f"http://127.0.0.1:{self.port}")
        self.assertEqual(client.list_models(), [{"name": "probe-model"}])

    def test_qdrant_loopback_is_direct_under_proxy_env(self):
        store = QdrantVectorStore(base_url=f"http://127.0.0.1:{self.port}", collection="probe")
        self.assertEqual(store.server_version(), "probe")

    def test_localhost_hostname_is_direct_under_proxy_env(self):
        client = OllamaClient(base_url=f"http://localhost:{self.port}")
        self.assertEqual(client.list_models(), [{"name": "probe-model"}])


class LoopbackClassificationTests(unittest.TestCase):
    def test_loopback_hosts_are_classified_direct(self):
        for url in (
            "http://127.0.0.1:6333/collections",
            "http://localhost:11434/api/tags",
            "http://[::1]:6333/",
        ):
            with self.subTest(url=url):
                self.assertTrue(is_loopback_url(url))

    def test_non_loopback_hosts_are_not_classified_direct(self):
        for url in (
            "http://example.com/api",
            "http://192.168.1.5:6333/",
            "http://10.0.0.2/",
        ):
            with self.subTest(url=url):
                self.assertFalse(is_loopback_url(url))


class NonLoopbackDefaultBehaviorTests(unittest.TestCase):
    """B: the change must not disable proxies for non-loopback hosts."""

    def test_non_loopback_still_uses_default_urlopen(self):
        with patch("core.ollama_http.urllib.request.urlopen") as urlopen_mock:
            urlopen_mock.return_value.__enter__.return_value = Mock()
            request = urllib.request.Request("http://example.com/api")
            open_request(request, timeout=1.0)
        urlopen_mock.assert_called_once()

    def test_loopback_never_uses_default_urlopen(self):
        with patch("core.ollama_http.urllib.request.urlopen") as urlopen_mock:
            opener = MagicMock()
            opener.open.return_value.__enter__.return_value = Mock()
            with patch("core.ollama_http._NO_PROXY_OPENER", opener):
                request = urllib.request.Request("http://127.0.0.1:6333/api")
                open_request(request, timeout=1.0)
        urlopen_mock.assert_not_called()
        opener.open.assert_called_once()


if __name__ == "__main__":
    unittest.main()
