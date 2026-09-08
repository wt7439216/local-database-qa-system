"""Normalized Document Model contract tests (Phase C / v3.2)."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from core.document_model import (
    NormalizedBlock,
    NormalizedDocument,
    SourceLocation,
    compute_document_content_hash,
    document_id_for_source,
    finalize_document,
)
from core.chunking import build_chunks, build_sections, build_vector_input


class DocumentIdentityTests(unittest.TestCase):
    def test_document_id_stable_across_content_change(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "通信原理.docx"
            source.write_bytes(b"v1")
            first = document_id_for_source(source)
            source.write_bytes(b"v2-content-changed")
            second = document_id_for_source(source)
            self.assertEqual(first, second, "内容编辑不得改变 document identity")

    def test_document_id_distinguishes_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a").mkdir()
            (root / "b").mkdir()
            self.assertNotEqual(
                document_id_for_source(root / "a" / "doc.docx"),
                document_id_for_source(root / "b" / "doc.docx"),
            )

    def test_content_hash_tracks_block_content(self):
        blocks_a = [NormalizedBlock(text="多径传播导致衰落。")]
        blocks_b = [NormalizedBlock(text="多径传播导致衰落。")]
        blocks_c = [NormalizedBlock(text="内容被修改。")]
        self.assertEqual(compute_document_content_hash(blocks_a), compute_document_content_hash(blocks_b))
        self.assertNotEqual(compute_document_content_hash(blocks_a), compute_document_content_hash(blocks_c))

    def test_finalize_document_fills_content_hash(self):
        document = NormalizedDocument(
            document_id="doc-x", source_path="/tmp/x.md", source_type="markdown",
            title="t", blocks=[NormalizedBlock(text="正文")],
        )
        finalize_document(document)
        self.assertTrue(document.content_hash)


class SectionBuilderTests(unittest.TestCase):
    def make_document(self, blocks) -> NormalizedDocument:
        document = NormalizedDocument(
            document_id="doc-sec", source_path="/tmp/sections.md",
            source_type="markdown", title="层级文档", blocks=list(blocks),
        )
        build_sections(document)
        return document

    def test_hierarchy_nests_by_heading_level(self):
        document = self.make_document([
            NormalizedBlock(text="第一章 总论", block_type="heading", heading_level=1, heading="第一章 总论"),
            NormalizedBlock(text="总论正文。"),
            NormalizedBlock(text="1.1 背景", block_type="heading", heading_level=2, heading="1.1 背景"),
            NormalizedBlock(text="背景正文。"),
            NormalizedBlock(text="1.2 目标", block_type="heading", heading_level=2, heading="1.2 目标"),
            NormalizedBlock(text="目标正文。"),
        ])
        self.assertEqual(len(document.root_sections), 1)
        root = document.root_sections[0]
        self.assertEqual(root.heading, "第一章 总论")
        self.assertEqual([child.heading for child in root.children], ["1.1 背景", "1.2 目标"])
        self.assertEqual(root.blocks[0].text, "总论正文。")
        self.assertEqual(root.children[0].blocks[0].text, "背景正文。")

    def test_blocks_before_first_heading_form_implicit_section(self):
        document = self.make_document([
            NormalizedBlock(text="导语正文，位于任何标题之前。"),
            NormalizedBlock(text="第一章", block_type="heading", heading_level=1, heading="第一章"),
            NormalizedBlock(text="章内正文。"),
        ])
        # 导语 → 隐式根节（持有序言内容）；首个标题成为新的根节
        self.assertEqual(len(document.root_sections), 2)
        implicit = document.root_sections[0]
        self.assertEqual(implicit.heading, "层级文档")
        self.assertTrue(implicit.blocks[0].text.startswith("导语正文"))
        self.assertEqual(document.root_sections[1].heading, "第一章")

    def test_level_skips_are_tolerated(self):
        document = self.make_document([
            NormalizedBlock(text="H1", block_type="heading", heading_level=1, heading="H1"),
            NormalizedBlock(text="H3", block_type="heading", heading_level=3, heading="H3"),
            NormalizedBlock(text="deep body"),
        ])
        root = document.root_sections[0]
        self.assertEqual(root.children[0].heading, "H3")
        self.assertEqual(root.children[0].blocks[0].text, "deep body")


class ChunkBuilderTests(unittest.TestCase):
    def make_document_and_chunks(self, blocks):
        document = NormalizedDocument(
            document_id="doc-chunk", source_path="/tmp/chunks.md",
            source_type="markdown", title="分块文档", blocks=list(blocks),
        )
        build_sections(document)
        return document, build_chunks(document)

    def test_chunk_ids_deterministic_and_content_sensitive(self):
        blocks = [
            NormalizedBlock(text="第一章 多径", block_type="heading", heading_level=1, heading="第一章 多径"),
            NormalizedBlock(text="多径传播导致衰落。" * 3),
        ]
        _, first = self.make_document_and_chunks(blocks)
        _, second = self.make_document_and_chunks(blocks)
        self.assertEqual([c.chunk_id for c in first], [c.chunk_id for c in second])
        changed = [NormalizedBlock(text="第一章 多径", block_type="heading", heading_level=1, heading="第一章 多径"),
                   NormalizedBlock(text="内容被改变了。" * 3)]
        _, third = self.make_document_and_chunks(changed)
        self.assertNotEqual([c.chunk_id for c in first], [c.chunk_id for c in third])

    def test_unrelated_section_insertion_does_not_shift_other_ids(self):
        base_blocks = [
            NormalizedBlock(text="1. 多径", block_type="heading", heading_level=1, heading="1. 多径"),
            NormalizedBlock(text="多径正文内容，足够长以通过最小长度要求。" * 2),
            NormalizedBlock(text="2. 分集", block_type="heading", heading_level=1, heading="2. 分集"),
            NormalizedBlock(text="分集正文内容，足够长以通过最小长度要求。" * 2),
        ]
        _, base_chunks = self.make_document_and_chunks(base_blocks)
        inserted_blocks = [
            base_blocks[0], base_blocks[1],
            NormalizedBlock(text="1.5 插入节", block_type="heading", heading_level=1, heading="1.5 插入节"),
            NormalizedBlock(text="新插入的独立小节内容。" * 2),
            base_blocks[2], base_blocks[3],
        ]
        _, inserted_chunks = self.make_document_and_chunks(inserted_blocks)
        base_ids = {c.chunk_id for c in base_chunks}
        inserted_ids = {c.chunk_id for c in inserted_chunks}
        # 原有节（多径/分集）的 chunk id 不漂移；仅新增节带来新 id
        self.assertTrue(base_ids <= inserted_ids)

    def test_unified_vector_input_and_hash(self):
        blocks = [
            NormalizedBlock(text="第一章", block_type="heading", heading_level=1, heading="第一章"),
            NormalizedBlock(text="多径传播正文。" * 4),
        ]
        document, chunks = self.make_document_and_chunks(blocks)
        chunk = chunks[0]
        self.assertIn("分块文档", chunk.vector_input)
        self.assertIn("第一章", chunk.vector_input)
        self.assertIn("多径传播正文", chunk.vector_input)
        self.assertTrue(chunk.vector_input_hash)
        self.assertTrue(chunk.content_hash)
        self.assertNotEqual(chunk.vector_input_hash, chunk.content_hash)

    def test_legacy_embedding_input_is_reproduced_by_unified_function(self):
        # 旧教材路径: embedding_input = f"{chapter} {section}\n{text}"
        legacy_chapter, legacy_section, legacy_text = "第1章 移动通信概述", "1.6.2 频率复用", "频率复用正文。"
        legacy_input = f"{legacy_chapter} {legacy_section}\n{legacy_text}"
        self.assertEqual(build_vector_input("", f"{legacy_chapter} {legacy_section}", legacy_text), legacy_input)

    def test_source_location_describe(self):
        self.assertEqual(SourceLocation(kind="page", page=31).describe(), "PDF 第31页")
        self.assertEqual(SourceLocation(kind="slide", slide=12).describe(), "Slide 12")
        self.assertEqual(SourceLocation(kind="paragraph", paragraph=84).describe(), "段落 84")
        self.assertEqual(SourceLocation(kind="line", line_start=120, line_end=138).describe(), "行 120-138")


if __name__ == "__main__":
    unittest.main()
