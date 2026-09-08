"""Phase D security closure tests: web import/relink path policy + disclosure.

Covers the closure-audit matrix:
- allowed root import PASS via the Web API;
- traversal / absolute-outside / relative-outside / junction-or-symlink
  escape / relink-outside all rejected;
- no roots configured -> web path import disabled by default;
- CLI (no policy attached) keeps Phase C local-user behavior;
- parser security chain still applies INSIDE an allowed root;
- API responses disclose no absolute server paths (list/detail/overview/
  import/relink/duplicate-candidates);
- pairing/auth regression: unauthenticated v3 calls stay 401.
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import json
import re
import sqlite3
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import core.config as config
from core.library_service import LibraryService
from core.path_policy import (
    ImportPathPolicy,
    ImportPathPolicyError,
    canonical_source_path,
    policy_from_roots_value,
)
from desktop.web_server import WebQAServer
from tests.test_importer import fake_embedder

DRIVE_PATH_RE = re.compile(r"[A-Za-z]:[\\/]")


def markdown(title: str, sections: dict[str, str]) -> str:
    parts = [f"# {title}", ""]
    for heading, body in sections.items():
        parts.append(f"## {heading}")
        parts.append(body)
    return "\n".join(parts) + "\n"


class ImportPathPolicyUnitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.docs = self.root / "docs"
        self.docs.mkdir()
        self.outside = self.root / "outside"
        self.outside.mkdir()

    def test_inside_root_allowed_with_case_and_separator_variants(self):
        import os

        from core.path_policy import canonical_source_path

        policy = ImportPathPolicy((self.docs,))
        allowed = policy.check(self.docs / "a.txt")
        self.assertTrue(allowed.is_absolute())
        # alternate spellings of the same location are accepted
        self.assertEqual(policy.check(str(self.docs) + "/"), canonical_source_path(self.docs))
        self.assertEqual(
            policy.check(str(self.docs / "b.txt").replace("\\", "/")),
            canonical_source_path(self.docs / "b.txt"),
        )
        if os.name == "nt":
            case_variant = policy.check(str(self.docs).upper() + "\\C.TXT")
            self.assertEqual(
                os.path.normcase(str(case_variant)),
                os.path.normcase(str(canonical_source_path(self.docs / "c.txt"))),
            )

    def test_traversal_escaping_root_rejected(self):
        policy = ImportPathPolicy((self.docs,))
        escape = self.docs / "sub" / ".." / ".." / "outside" / "private.txt"
        with self.assertRaises(ImportPathPolicyError):
            policy.check(escape)

    def test_absolute_outside_and_other_drive_rejected(self):
        policy = ImportPathPolicy((self.docs,))
        with self.assertRaises(ImportPathPolicyError):
            policy.check(self.outside / "private.txt")
        with self.assertRaises(ImportPathPolicyError):
            policy.check("ZZ:\\somewhere\\else.txt" if __import__("os").name != "nt" else "Q:\\somewhere\\else.txt")

    def test_relative_outside_rejected_after_resolution(self):
        policy = ImportPathPolicy((self.docs,))
        with self.assertRaises(ImportPathPolicyError):
            policy.check("private.txt")

    def test_no_roots_denies_everything(self):
        policy = ImportPathPolicy(())
        with self.assertRaises(ImportPathPolicyError) as ctx:
            policy.check(self.docs / "a.txt")
        self.assertIn("已禁用", str(ctx.exception))

    def test_policy_from_roots_value(self):
        import os

        policy = policy_from_roots_value(f"{self.docs}{os.pathsep}  {self.outside} ")
        self.assertEqual(len(policy), 2)
        self.assertEqual(len(policy_from_roots_value("")), 0)
        self.assertEqual(len(policy_from_roots_value(None)), 0)

    def test_display_relative_and_fallback(self):
        policy = ImportPathPolicy((self.docs,))
        target = self.docs / "sub" / "a.txt"
        self.assertEqual(policy.display_relative(target), "sub/a.txt")
        self.assertIsNone(policy.display_relative(self.outside / "b.txt"))


class WebPathPolicyTests(unittest.TestCase):
    """Web API behavior with a configured root and with no roots at all."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.import_root = self.root / "imports"
        self.import_root.mkdir()
        self.logs = self.root / "logs"
        telemetry = patch.object(config, "LOG_DIR", self.logs)
        telemetry.start()
        self.addCleanup(telemetry.stop)
        self.library = self.root / "managed.sqlite3"

    def _service(self, roots) -> LibraryService:
        return LibraryService(
            self.library,
            embedding_model="test-embed",
            ollama=fake_embedder(),
            log_dir=self.logs,
            path_policy=ImportPathPolicy(roots),
        )

    def _server(self, service: LibraryService) -> WebQAServer:
        server = WebQAServer(
            object(), host="127.0.0.1", port=0, pairing_code="123456",
            web_root=self.root, library_service=service,
        )
        server.start()
        self.addCleanup(server.stop)
        return server

    def _token(self, server: WebQAServer) -> str:
        token, _ = server.pair("123456", "127.0.0.1")
        return token

    def _request(self, server: WebQAServer, token: str, method: str, path: str, payload: dict | None = None):
        import urllib.error
        import urllib.request

        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            f"{server.local_url}{path}", data=data, method=method,
            headers={
                "Host": f"127.0.0.1:{server.port}",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def test_allowed_root_import_passes(self):
        source = self.import_root / "sample.txt"
        source.write_text(markdown("根内文档", {"多径传播": "多径传播是移动信道的主要现象，需要专门章节详细说明。"}), encoding="utf-8")
        service = self._service((self.import_root,))
        server = self._server(service)
        token = self._token(server)
        status, body = self._request(server, token, "POST", "/api/v3/library/documents",
                                     {"action": "import", "path": str(source)})
        self.assertEqual(status, 201, body)
        self.assertEqual(body["import_status"], "READY")

    def test_traversal_escape_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "private.txt").write_text("机密", encoding="utf-8")
        service = self._service((self.import_root,))
        server = self._server(service)
        token = self._token(server)
        traversal = str(self.import_root / "sub" / ".." / ".." / "outside" / "private.txt")
        status, body = self._request(server, token, "POST", "/api/v3/library/documents",
                                     {"action": "import", "path": traversal})
        self.assertEqual(status, 400)
        self.assertIn("拒绝", body["error"])

    def test_absolute_outside_rejected(self):
        outside = self.root / "elsewhere.txt"
        outside.write_text(markdown("外部", {"多径传播": "外部路径的正文内容，不允许通过 Web 导入。"}), encoding="utf-8")
        service = self._service((self.import_root,))
        server = self._server(service)
        token = self._token(server)
        status, body = self._request(server, token, "POST", "/api/v3/library/documents",
                                     {"action": "import", "path": str(outside)})
        self.assertEqual(status, 400)
        self.assertIn("拒绝", body["error"])

    def test_relative_outside_rejected(self):
        service = self._service((self.import_root,))
        server = self._server(service)
        token = self._token(server)
        status, body = self._request(server, token, "POST", "/api/v3/library/documents",
                                     {"action": "import", "path": "private.txt"})
        self.assertEqual(status, 400)

    def test_no_roots_disables_web_import_by_default(self):
        service = self._service(())
        server = self._server(service)
        token = self._token(server)
        status, body = self._request(server, token, "POST", "/api/v3/library/documents",
                                     {"action": "import", "path": str(self.import_root / "x.txt")})
        self.assertEqual(status, 400)
        self.assertIn("已禁用", body["error"])

    def test_relink_outside_root_rejected_and_inside_allowed(self):
        source = self.import_root / "doc.txt"
        source.write_text(markdown("relink 文档", {"多径传播": "多径传播是移动信道的主要现象，需要专门章节详细说明。"}), encoding="utf-8")
        outside = self.root / "outside.docx"
        outside.write_text("外部目标", encoding="utf-8")
        moved = self.import_root / "archive"
        moved.mkdir()
        moved_target = moved / "doc.txt"
        moved_target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

        service = self._service((self.import_root,))
        server = self._server(service)
        token = self._token(server)
        document_id = self._request(server, token, "POST", "/api/v3/library/documents",
                                    {"action": "import", "path": str(source)})[1]["document_id"]

        status, body = self._request(server, token, "POST", f"/api/v3/library/documents/{document_id}/relink",
                                     {"path": str(outside), "update_if_changed": True})
        self.assertEqual(status, 400, "relink 不得成为路径策略后门")

        status, body = self._request(server, token, "POST", f"/api/v3/library/documents/{document_id}/relink",
                                     {"path": str(moved_target)})
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "RELINKED")

    def test_junction_or_symlink_escape_rejected(self):
        # resolve() must follow the link and land OUTSIDE the root -> rejected.
        outside = self.root / "outside-dir"
        outside.mkdir()
        (outside / "secret.txt").write_text(markdown("机密", {"多径传播": "机密内容不应可导入。"}), encoding="utf-8")
        service = self._service((self.import_root,))
        server = self._server(service)
        token = self._token(server)

        link = self.import_root / "link"
        created_kind = None
        try:
            link.symlink_to(outside, target_is_directory=True)
            created_kind = "symlink"
        except (OSError, NotImplementedError):
            # Windows without symlink privilege: junctions need no elevation.
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            if result.returncode != 0:
                self.skipTest(f"测试环境无法创建 symlink/junction：{result.stderr.strip()[:120]}")
            created_kind = "junction"
        self.addCleanup(self._remove_link, link)

        self.assertIsNotNone(created_kind)
        status, body = self._request(server, token, "POST", "/api/v3/library/documents",
                                     {"action": "import", "path": str(link / "secret.txt")})
        self.assertEqual(status, 400, f"{created_kind} 逃逸必须被拒绝")

    @staticmethod
    def _remove_link(link: Path):
        try:
            link.rmdir()  # junctions/symlinks to dirs remove as empty
        except OSError:
            try:
                link.unlink()
            except OSError:
                pass

    def test_parser_security_still_applies_inside_root(self):
        bad = self.import_root / "malware.exe"
        bad.write_bytes(b"MZ not a document")
        service = self._service((self.import_root,))
        server = self._server(service)
        token = self._token(server)
        status, body = self._request(server, token, "POST", "/api/v3/library/documents",
                                     {"action": "import", "path": str(bad)})
        self.assertEqual(status, 200)  # policy passed; the PARSER rejected it
        self.assertEqual(body["import_status"], "FAILED")
        self.assertIn("unsupported_format", body["error"])

    def test_cli_service_without_policy_keeps_local_permissions(self):
        # CLI 代表本机用户：不附加策略时可导入任意路径（Phase C 兼容）。
        service = LibraryService(
            self.library.with_name("cli.sqlite3"),
            embedding_model="test-embed", ollama=fake_embedder(), log_dir=self.logs,
        )
        outside = self.root / "outside.txt"
        outside.write_text(markdown("CLI 导入", {"多径传播": "CLI 以本机用户权限执行，不受 Web 导入目录限制。"}), encoding="utf-8")
        result = service.import_document(outside)
        self.assertEqual(result["import_status"], "READY")


class SourcePathDisclosureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.import_root = self.root / "imports"
        self.logs = self.root / "logs"
        telemetry = patch.object(config, "LOG_DIR", self.logs)
        telemetry.start()
        self.addCleanup(telemetry.stop)
        self.library = self.root / "managed.sqlite3"
        self.service = LibraryService(
            self.library, embedding_model="test-embed", ollama=fake_embedder(),
            log_dir=self.logs, path_policy=ImportPathPolicy((self.import_root,)),
        )
        self.import_root.mkdir()
        self.source = self.import_root / "sub" / "sample.md"
        self.source.parent.mkdir()
        self.source.write_text(markdown("泄露测试", {"多径传播": "多径传播是移动信道的主要现象，需要专门章节详细说明。"}), encoding="utf-8")
        self.document_id = self.service.import_document(self.source)["document_id"]

    def _body(self, payload) -> str:
        return json.dumps(payload, ensure_ascii=False)

    def test_api_responses_disclose_no_absolute_paths(self):
        # The web layer wraps every library payload in redact_source_paths;
        # verify that composition for the payload shapes it emits.
        from desktop.library_api_safety import redact_source_paths

        for payload in (
            self.service.list_documents(),
            self.service.get_document(self.document_id),
            self.service.duplicate_candidates(self.document_id),
            {"statistics": self.service.statistics(), "documents": self.service.list_documents()},
        ):
            redacted = redact_source_paths(payload, self.service.source_display)
            body = self._body(redacted)
            self.assertNotIn(str(self.source), body, "完整绝对路径不得出现在 API 响应")
            self.assertNotIn(str(self.root), body)
            self.assertFalse(DRIVE_PATH_RE.search(body), f"响应包含盘符绝对路径：{body[:200]}")

    def test_list_and_detail_carry_safe_display_fields(self):
        from desktop.library_api_safety import redact_source_paths

        for row in self.service.list_documents():
            redacted = redact_source_paths(dict(row), self.service.source_display)
            self.assertEqual(redacted["source_display"], "sub/sample.md", "根内文件应给出相对显示路径")
            self.assertEqual(redacted["source_name"], "sample.md")
            self.assertNotIn("source_path", redacted)
        detail = redact_source_paths(self.service.get_document(self.document_id), self.service.source_display)
        self.assertEqual(detail["source_display"], "sub/sample.md")
        self.assertNotIn("source_path", detail)

    def test_sqlite_retains_full_source_path(self):
        with closing(sqlite3.connect(self.library)) as connection:
            stored = connection.execute(
                "SELECT source_path FROM document_sources WHERE document_id = ?",
                (self.document_id,),
            ).fetchone()[0]
        self.assertEqual(stored, canonical_source_path(self.source).as_posix())

    def test_library_api_http_responses_are_redacted(self):
        server = WebQAServer(
            object(), host="127.0.0.1", port=0, pairing_code="123456",
            web_root=self.root, library_service=self.service,
        )
        server.start()
        self.addCleanup(server.stop)
        token, _ = server.pair("123456", "127.0.0.1")
        import urllib.error
        import urllib.request

        def get(path: str) -> str:
            request = urllib.request.Request(
                f"{server.local_url}{path}", method="GET",
                headers={"Host": f"127.0.0.1:{server.port}", "Authorization": f"Bearer {token}"},
            )
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    return response.read().decode("utf-8")
            except urllib.error.HTTPError as exc:
                return exc.read().decode("utf-8")

        for path in ("/api/v3/library", "/api/v3/library/documents", f"/api/v3/library/documents/{self.document_id}"):
            body = get(path)
            self.assertNotIn(str(self.source), body, f"{path} 泄露绝对路径")
            self.assertFalse(DRIVE_PATH_RE.search(body), f"{path} 泄露盘符绝对路径")
            self.assertIn("source_display", body)
        status_body = get("/api/v3/library")
        self.assertIn("sub/sample.md", status_body)

    def test_unauthenticated_v3_import_stays_401(self):
        server = WebQAServer(
            object(), host="127.0.0.1", port=0, pairing_code="123456",
            web_root=self.root, library_service=self.service,
        )
        server.start()
        self.addCleanup(server.stop)
        import urllib.error
        import urllib.request

        request = urllib.request.Request(
            f"{server.local_url}/api/v3/library/documents",
            data=json.dumps({"action": "import", "path": "x.txt"}).encode(),
            method="POST", headers={"Host": f"127.0.0.1:{server.port}", "Content-Type": "application/json"},
        )
        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(request, timeout=10)
        self.assertEqual(raised.exception.code, 401, "新增路径策略不得绕过既有认证")


if __name__ == "__main__":
    unittest.main()
