"""Q2.2: deterministic citation completion tests.

Locks the conservative unique-supported-only selector and the positional
claim-to-text mapping.  Completion must never rewrite factual text, never
auto-fill an ambiguous / uncertain / unsupported / invalid candidate, and never
insert a duplicate or misplaced marker.  Citation markers are inserted before
the trailing sentence punctuation, matching the engine's existing convention
("结论[1]。").
"""

from __future__ import annotations

import re
import unittest

from core.citation_completion import (
    CITATION_COMPLETION_VERSION,
    complete_citations,
)


def _strip(text: str) -> str:
    return re.sub(r"\[\d+\]", "", text)


class TestSelectorBasics(unittest.TestCase):
    def test_unique_supported_completes(self):
        answer = "GSM使用GMSK调制。"
        evidence = {1: "GSM系统使用GMSK调制，载波间隔200kHz。", 2: "WCDMA采用QPSK调制。"}
        completed, stats = complete_citations(answer, evidence)
        self.assertEqual(completed, "GSM使用GMSK调制[1]。")
        self.assertEqual(stats.autofill_success, 1)
        self.assertEqual(stats.autofill_attempts, 1)

    def test_multiple_supported_ambiguous_no_autofill(self):
        answer = "TDMA使用时分多址。"
        evidence = {1: "TDMA使用时分多址方式。", 2: "TDMA是一种多址技术。"}
        completed, stats = complete_citations(answer, evidence)
        self.assertEqual(completed, "TDMA使用时分多址。")
        self.assertEqual(stats.ambiguous_skips, 1)
        self.assertEqual(stats.autofill_success, 0)

    def test_uncertain_only_no_autofill(self):
        answer = "载波间隔为二百千赫兹。"
        evidence = {1: "载波间隔为200 kHz。"}
        completed, stats = complete_citations(answer, evidence)
        self.assertEqual(completed, "载波间隔为二百千赫兹。")
        self.assertGreaterEqual(stats.uncertain_skips, 1)

    def test_unsupported_only_no_autofill(self):
        answer = "LTE使用OFDMA调制。"
        evidence = {1: "GSM系统使用GMSK调制。"}
        completed, stats = complete_citations(answer, evidence)
        self.assertEqual(completed, "LTE使用OFDMA调制。")
        self.assertEqual(stats.autofill_success, 0)

    def test_already_cited_untouched(self):
        answer = "GSM使用GMSK调制[1]。"
        evidence = {1: "GSM系统使用GMSK调制。"}
        completed, stats = complete_citations(answer, evidence)
        self.assertEqual(completed, "GSM使用GMSK调制[1]。")
        self.assertEqual(stats.autofill_attempts, 0)


class TestAnswerMapping(unittest.TestCase):
    def test_single_sentence(self):
        answer = "GSM使用GMSK调制。"
        evidence = {1: "GSM系统使用GMSK调制。"}
        completed, _ = complete_citations(answer, evidence)
        self.assertEqual(completed, "GSM使用GMSK调制[1]。")

    def test_multi_sentence(self):
        answer = "GSM使用GMSK调制。WCDMA采用QPSK调制。"
        evidence = {1: "GSM系统使用GMSK调制。", 2: "WCDMA系统采用QPSK调制。"}
        completed, _ = complete_citations(answer, evidence)
        self.assertEqual(completed, "GSM使用GMSK调制[1]。WCDMA采用QPSK调制[2]。")

    def test_bullet_list(self):
        answer = "- GSM使用GMSK调制\n- WCDMA采用QPSK调制"
        evidence = {1: "GSM系统使用GMSK调制。", 2: "WCDMA系统采用QPSK调制。"}
        completed, _ = complete_citations(answer, evidence)
        self.assertEqual(completed, "- GSM使用GMSK调制[1]\n- WCDMA采用QPSK调制[2]")

    def test_duplicate_claim_no_cross_replace(self):
        answer = "GSM使用GMSK调制。GSM使用GMSK调制。"
        evidence = {1: "GSM系统使用GMSK调制。"}
        completed, stats = complete_citations(answer, evidence)
        self.assertEqual(completed, "GSM使用GMSK调制[1]。GSM使用GMSK调制[1]。")
        self.assertEqual(stats.autofill_success, 2)

    def test_cjk_punctuation(self):
        answer = "码片速率为3.84 Mcps。带宽为5 MHz。"
        evidence = {1: "码片速率为3.84 Mcps。", 2: "带宽为5 MHz。"}
        completed, _ = complete_citations(answer, evidence)
        self.assertEqual(completed, "码片速率为3.84 Mcps[1]。带宽为5 MHz[2]。")

    def test_newline_mapping(self):
        answer = "GSM使用GMSK调制\nWCDMA采用QPSK调制"
        evidence = {1: "GSM系统使用GMSK调制。", 2: "WCDMA系统采用QPSK调制。"}
        completed, _ = complete_citations(answer, evidence)
        self.assertEqual(completed, "GSM使用GMSK调制[1]\nWCDMA采用QPSK调制[2]")

    def test_existing_citation_preserved(self):
        answer = "GSM使用GMSK调制[1]。WCDMA采用QPSK调制。"
        evidence = {1: "GSM系统使用GMSK调制。", 2: "WCDMA系统采用QPSK调制。"}
        completed, _ = complete_citations(answer, evidence)
        self.assertEqual(completed, "GSM使用GMSK调制[1]。WCDMA采用QPSK调制[2]。")


class TestSafety(unittest.TestCase):
    def test_factual_text_invariant(self):
        answer = "GSM使用GMSK调制。WCDMA采用QPSK调制。"
        evidence = {1: "GSM系统使用GMSK调制。", 2: "WCDMA系统采用QPSK调制。"}
        completed, _ = complete_citations(answer, evidence)
        self.assertEqual(_strip(completed), _strip(answer))

    def test_never_uses_out_of_range_evidence(self):
        answer = "GSM使用GMSK调制。"
        evidence = {1: "GSM系统使用GMSK调制。"}
        completed, _ = complete_citations(answer, evidence)
        markers = re.findall(r"\[(\d+)\]", completed)
        self.assertTrue(all(int(m) in evidence for m in markers))

    def test_version(self):
        self.assertEqual(CITATION_COMPLETION_VERSION, "citation-completion-v1")


if __name__ == "__main__":
    unittest.main()
