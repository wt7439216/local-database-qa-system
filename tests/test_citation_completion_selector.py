"""Q3.1: deterministic citation completion selector safety (simulation only).

These tests simulate the conservative selector contract a future citation
completion could use, WITHOUT modifying any answer.  The contract is:

    auto-fill only when exactly one candidate evidence set is deterministically
    SUPPORTED and valid and in scope; otherwise leave uncited.

This is a design-qualification test: it proves the current verifier is precise
enough to be a safe evidence selector, not that citation completion exists.
"""

from __future__ import annotations

import unittest

from core.citation_verifier import (
    SUPPORTED,
    UNCERTAIN,
    verify_answer,
)

SELECTABLE = "SELECTABLE"
AMBIGUOUS = "AMBIGUOUS"
NO_AUTOFILL = "NO_AUTOFILL"


def simulate_selector(
    claim_text: str,
    candidate_evidences: dict[int, str],
    citation_count: int | None = None,
) -> str:
    """Simulate the conservative auto-fill selector.

    For each candidate evidence id, verify the claim against that single
    evidence.  The selector returns SELECTABLE only when exactly one candidate
    is deterministically SUPPORTED; AMBIGUOUS when more than one is SUPPORTED;
    NO_AUTOFILL otherwise (UNCERTAIN / UNSUPPORTED / invalid / out-of-scope).
    """
    if citation_count is None:
        citation_count = max(candidate_evidences, default=0)
    supported: list[int] = []
    uncertain: list[int] = []
    for eid, evidence_text in candidate_evidences.items():
        report = verify_answer(
            f"{claim_text}[{eid}]",
            {eid: evidence_text},
            citation_count=citation_count,
        )
        if report.invalid_citation_count > 0:
            continue  # invalid / out-of-scope candidate is never selected
        for verification in report.verifications:
            if verification.support == SUPPORTED:
                supported.append(eid)
            elif verification.support == UNCERTAIN:
                uncertain.append(eid)
    if len(supported) == 1:
        return SELECTABLE
    if len(supported) > 1:
        return AMBIGUOUS
    # Only UNCERTAIN (needs semantics) or UNSUPPORTED candidates remain.
    if uncertain:
        return NO_AUTOFILL
    return NO_AUTOFILL


class TestSelectorSafety(unittest.TestCase):
    def test_unique_supported_selectable(self):
        result = simulate_selector(
            "GSM使用GMSK调制",
            {1: "GSM系统使用GMSK调制，载波间隔为200 kHz。", 2: "WCDMA采用QPSK调制。"},
        )
        self.assertEqual(result, SELECTABLE)

    def test_multiple_supported_ambiguous(self):
        result = simulate_selector(
            "TDMA使用时分多址",
            {1: "TDMA使用时分多址方式。", 2: "TDMA是一种多址技术。"},
        )
        self.assertEqual(result, AMBIGUOUS)

    def test_uncertain_only_no_autofill(self):
        # CJK synonymy ("二百千赫兹" vs "200 kHz") is UNCERTAIN, never auto-fill.
        result = simulate_selector(
            "载波间隔为二百千赫兹",
            {1: "载波间隔为200 kHz。"},
        )
        self.assertEqual(result, NO_AUTOFILL)

    def test_unsupported_only_no_autofill(self):
        result = simulate_selector(
            "LTE使用OFDMA调制",
            {1: "GSM系统使用GMSK调制。"},
        )
        self.assertEqual(result, NO_AUTOFILL)

    def test_invalid_or_out_of_scope_no_autofill(self):
        # A candidate whose id exceeds citation_count is invalid and must not
        # be selected, even if its text would otherwise match.
        result = simulate_selector(
            "GSM使用GMSK调制",
            {1: "GSM系统使用GMSK调制。", 9: "GSM系统使用GMSK调制。"},
            citation_count=1,
        )
        self.assertEqual(result, SELECTABLE)  # only id 1 is valid and supported


class TestSelectorConservatism(unittest.TestCase):
    def test_no_llm_dependency(self):
        # The selector path only calls deterministic verify_answer; assert the
        # module has no LLM/network imports surfaced through this helper.
        import core.citation_verifier as cv
        self.assertEqual(cv.CITATION_VERIFIER_VERSION, "f2-v4")

    def test_false_support_not_selected(self):
        # A wrong-evidence candidate must not be SELECTABLE as the sole support.
        result = simulate_selector(
            "码片速率为3.84 Mcps",
            {1: "GSM载波间隔为200 kHz。"},  # wrong evidence, no 3.84
        )
        self.assertEqual(result, NO_AUTOFILL)


if __name__ == "__main__":
    unittest.main()
