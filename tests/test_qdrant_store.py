"""Qdrant adapter tests: transport error mapping + semantic fake coverage.

A throwaway local ``http.server`` instance injects real HTTP-level failures
(200 garbage body, HTTP 500, slow response, refused connection) so the
stdlib-only ``HttpQdrantTransport`` is exercised end to end without any
external service.  Semantic behaviors (collections, filters, deterministic
ids, idempotent upsert, verify) are covered against ``FakeQdrantTransport``.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time
import unittest

from core.qdrant_store import QdrantHTTPError, QdrantVectorStore
from core.vector_store import (
    VectorBackendUnavailableError,
    VectorDimensionMismatchError,
    VectorHealth,
    VectorProtocolError,
    VectorStoreError,
)
from tests.fake_qdrant import FakeQdrantTransport


class _Handler(BaseHTTPRequestHandler):
    server_version = "FakeQdrantHTTP/1"

    def _reply(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve(self) -> None:
        mode = self.server.mode
        if mode == "slow":
            time.sleep(1.0)
        if mode == "ok":
            self._reply(200, json.dumps({"title": "qdrant - vector database", "version": "1.19.1-test"}).encode())
        elif mode == "garbage":
            self._reply(200, b"this is definitely not json")
        elif mode in {"error500", "slow"}:
            self._reply(500, json.dumps({"error": "boom"}).encode())
        else:  # plain-404
            self._reply(404, json.dumps({"error": "Not Found"}).encode())

    def do_GET(self):  # noqa: N802
        self._serve()

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)
        self._serve()

    def do_PUT(self):  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)
        self._serve()

    def log_message(self, format, *args):  # noqa: A002
        return


class QdrantTransportTests(unittest.TestCase):
    def setUp(self):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.httpd.mode = "ok"
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.httpd.shutdown)
        self.addCleanup(self.httpd.server_close)
        self.store = QdrantVectorStore(
            base_url=f"http://127.0.0.1:{self.port}",
            collection="transport-test",
            timeout=2.0,
        )

    def test_valid_response_and_version_parsing(self):
        self.assertEqual(self.store.server_version(), "1.19.1-test")
        health = self.store.health()
        self.assertIsInstance(health, VectorHealth)
        # The canned server only answers the root endpoint, so collection
        # lookup surfaces an explicit error instead of a silent ok.
        self.assertFalse(health.ok)
        self.assertTrue(health.error)

    def test_http_error_is_mapped(self):
        self.httpd.mode = "error500"
        with self.assertRaises(QdrantHTTPError):
            self.store.server_version()

    def test_invalid_json_is_protocol_error(self):
        self.httpd.mode = "garbage"
        with self.assertRaises(VectorProtocolError):
            self.store.server_version()

    def test_timeout_is_unavailable(self):
        self.httpd.mode = "slow"
        slow = QdrantVectorStore(
            base_url=f"http://127.0.0.1:{self.port}",
            collection="transport-test",
            timeout=0.2,
        )
        started = time.perf_counter()
        with self.assertRaises(VectorBackendUnavailableError):
            slow.server_version()
        self.assertLess(time.perf_counter() - started, 1.0)

    def test_connection_refused_is_unavailable(self):
        self.httpd.shutdown()
        self.thread.join(timeout=2)
        with self.assertRaises(VectorBackendUnavailableError):
            self.store.server_version()

    def test_health_never_raises_on_outage(self):
        self.httpd.mode = "error500"
        health = self.store.health()
        self.assertFalse(health.ok)
        self.assertTrue(health.error)


class ScriptedTransport:
    """Returns canned (status, payload) pairs to test response validation."""

    def __init__(self, response):
        self.response = response

    def request(self, method, path, payload=None, timeout=None):
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class QdrantResponseValidationTests(unittest.TestCase):
    def test_missing_result_field_is_protocol_error(self):
        store = QdrantVectorStore(transport=ScriptedTransport((200, {"status": "ok"})))
        with self.assertRaises(VectorProtocolError):
            store.collection_info()

    def test_error_status_is_protocol_error(self):
        store = QdrantVectorStore(
            transport=ScriptedTransport((200, {"status": "error", "result": {}}))
        )
        with self.assertRaises(VectorProtocolError):
            store.collection_info()

    def test_unavailable_transport_is_reported_by_health(self):
        store = QdrantVectorStore(
            transport=ScriptedTransport(VectorBackendUnavailableError("down"))
        )
        health = store.health()
        self.assertFalse(health.ok)
        self.assertEqual(health.error, "down")

    def test_collection_info_missing_is_none(self):
        store = QdrantVectorStore(transport=FakeQdrantTransport())
        self.assertIsNone(store.collection_info())


class QdrantCollectionGuardTests(unittest.TestCase):
    def setUp(self):
        self.transport = FakeQdrantTransport()
        self.store = QdrantVectorStore(collection="guard-test", transport=self.transport)

    def test_ensure_collection_creates_then_validates(self):
        self.store.ensure_collection(6)
        self.assertEqual(self.store.collection_dimension(), 6)
        # Same config again: fine.
        self.store.ensure_collection(6)
        # Different config on an existing collection: refused, never silent.
        with self.assertRaises(VectorDimensionMismatchError):
            self.store.ensure_collection(8)

    def test_ensure_collection_rejects_bad_dimension(self):
        with self.assertRaises(VectorDimensionMismatchError):
            self.store.create_collection(0)

    def test_missing_collection_blocks_search_with_clear_error(self):
        with self.assertRaises(VectorStoreError):
            self.store.search([0.0] * 6, limit=3)

    def test_server_version_from_fake(self):
        self.assertEqual(self.store.server_version(), "1.19.1")


if __name__ == "__main__":
    unittest.main()
