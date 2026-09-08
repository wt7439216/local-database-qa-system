"""F.2 gate: deterministic citation verifier contract tests (Phase F.2 / v3.5).

Covers the full Layer-1 contract with no LLM / NLI / embedding / external IO:
validity, coverage, deterministic support (Latin / CJK / number / unit),
the four-valued support state, multi-citation claims, and the API/engine
backward-compatibility guarantees.
"""

from __future__ import annotations

import unittest

from core.citation_verifier import (
    CITATION_VERIFIER_VERSION,
    NOT_APPLICABLE,
    SUPPORTED,
    UNCERTAIN,
    UNSUPPORTED,
    CitationReport,
    DeterministicCitationVerifier,
    citation_numbers,
    is_factual_claim,
    split_claims,
    valid_citation_ids,
    verify_answer,
)


class VerifierFixture:
    def setUp(self) -> None:
        self.verifier = DeterministicCitationVerifier()
        # Deterministic evidence corpus keyed by citation number.
        self.evidence = {
            1: "GSM系统使用GMSK调制，载波间隔为200 kHz，最大数据速率约为270.833 kbit/s。",
            2: "WCDMA系统采用QPSK调制，带宽为5 MHz，码片速率为3.84 Mcps。",
            3: "香农公式 C = B log2(1 + S/N)，其中B为带宽。",
        }

    def verify(self, answer: str, evidence: dict[int, str] | None = None):
        return self.verifier.verify(answer, evidence or self.evidence)


class CitationNumberTests(VerifierFixture, unittest.TestCase):
    def test_basic_citation_numbers(self):
        self.assertEqual(citation_numbers("结论如下[1]和[2]。"), [1, 2])

    def test_unit_bracket_is_not_citation(self):
        # "[450]MHz" is a value, not a citation reference.
        self.assertEqual(citation_numbers("频率为[450]MHz。"), [])

    def test_range_is_not_expanded_here(self):
        # Deterministic citation_numbers does not expand ranges; normalize does.
        self.assertEqual(citation_numbers("见[1][2][3]。"), [1, 2, 3])


class FactualClaimTests(VerifierFixture, unittest.TestCase):
    def test_latin_claim_is_factual(self):
        self.assertTrue(is_factual_claim("GSM使用GMSK调制。"))

    def test_cjk_claim_is_factual(self):
        self.assertTrue(is_factual_claim("载波间隔为二百千赫兹。"))

    def test_number_claim_is_factual(self):
        self.assertTrue(is_factual_claim("速率为270.833。"))

    def test_connective_claim_is_not_factual(self):
        self.assertFalse(is_factual_claim("详见材料。"))
        self.assertFalse(is_factual_claim("回答如下。"))


class ClaimSegmentationTests(VerifierFixture, unittest.TestCase):
    def test_split_attaches_citation_to_preceding_claim(self):
        claims = split_claims("GSM使用GMSK调制[1]。WCDMA使用QPSK调制[2]。")
        self.assertEqual(len(claims), 2)
        self.assertEqual(claims[0].citation_ids, (1,))
        self.assertEqual(claims[1].citation_ids, (2,))

    def test_uncited_claim_has_empty_ids(self):
        claims = split_claims("这是一个没有引用的陈述。")
        self.assertEqual(claims[0].citation_ids, ())


class CitationValidityTests(VerifierFixture, unittest.TestCase):
    def test_valid_citation(self):
        valid, invalid = valid_citation_ids("结论[1]。", 3)
        self.assertEqual(valid, [1])
        self.assertEqual(invalid, [])

    def test_invalid_out_of_range_citation(self):
        valid, invalid = valid_citation_ids("结论[9]。", 3)
        self.assertEqual(valid, [])
        self.assertEqual(invalid, [9])

    def test_invalid_zero_and_negative(self):
        valid, invalid = valid_citation_ids("结论[0]和[-1]。", 3)
        self.assertEqual(valid, [])
        self.assertEqual(invalid, [0, -1])

    def test_present_ids_extra_constraint(self):
        # number 2 exists in range but not in the present evidence set.
        valid, invalid = valid_citation_ids("结论[2]。", 3, present_ids={1, 3})
        self.assertEqual(valid, [])
        self.assertEqual(invalid, [2])

    def test_duplicate_citation_counted_once(self):
        valid, invalid = valid_citation_ids("结论[1]和[1]。", 3)
        self.assertEqual(valid, [1])
        self.assertEqual(invalid, [])


class CoverageTests(VerifierFixture, unittest.TestCase):
    def test_full_coverage(self):
        report = self.verify("GSM使用GMSK调制[1]。WCDMA使用QPSK调制[2]。")
        self.assertEqual(report.factual_claim_count, 2)
        self.assertEqual(report.cited_claim_count, 2)
        self.assertEqual(report.citation_coverage, 1.0)

    def test_partial_coverage(self):
        report = self.verify("GSM使用GMSK调制[1]。这是一个未引用的事实陈述。")
        self.assertEqual(report.factual_claim_count, 2)
        self.assertEqual(report.cited_claim_count, 1)
        self.assertEqual(report.citation_coverage, 0.5)

    def test_no_citation(self):
        report = self.verify("GSM使用GMSK调制。")
        self.assertEqual(report.citation_coverage, 0.0)

    def test_no_factual_claims_coverage_is_none(self):
        report = self.verify("回答如下。")
        self.assertIsNone(report.citation_coverage)


class SupportStateTests(VerifierFixture, unittest.TestCase):
    def test_supported_latin_key_term(self):
        report = self.verify("GSM使用GMSK调制[1]。")
        self.assertEqual(report.verifications[0].support, SUPPORTED)

    def test_unsupported_wrong_evidence(self):
        # The claim is about GSM but cites the WCDMA chunk (2).
        report = self.verify("GSM使用GMSK调制[2]。")
        self.assertEqual(report.verifications[0].support, UNSUPPORTED)

    def test_unsupported_wrong_document_like_entity(self):
        # "LTE" appears nowhere in the cited evidence.
        report = self.verify("LTE使用OFDMA调制[1]。")
        self.assertEqual(report.verifications[0].support, UNSUPPORTED)

    def test_unsupported_uncited_factual_claim(self):
        report = self.verify("GSM使用GMSK调制。")
        self.assertEqual(report.verifications[0].support, UNSUPPORTED)

    def test_not_applicable_connective(self):
        report = self.verify("详见材料[1]。")
        self.assertEqual(report.verifications[0].support, NOT_APPLICABLE)

    def test_supported_number_match(self):
        report = self.verify("码片速率为3.84 Mcps[2]。")
        self.assertEqual(report.verifications[0].support, SUPPORTED)

    def test_supported_slash_unit(self):
        # A number glued to a slash unit ("kbit/s") is a unit check, not a key
        # term: the raw slash in the evidence must not cause a spurious
        # missing-key-term UNSUPPORTED.
        report = self.verify("最大数据速率为270.833 kbit/s[1]。")
        self.assertEqual(report.verifications[0].support, SUPPORTED)

    def test_unsupported_wrong_number(self):
        report = self.verify("码片速率为3.84 Mcps[1]。")  # chunk 1 has 270.833
        self.assertEqual(report.verifications[0].support, UNSUPPORTED)

    def test_unsupported_wrong_unit(self):
        # The number matches the cited chunk but the unit conflicts: chunk 2
        # states "3.84 Mcps", not "3.84 kbps".  The deterministic unit check
        # turns this into a hard UNSUPPORTED signal (never UNCERTAIN).
        report = self.verify("码片速率为3.84 kbps[2]。")
        self.assertEqual(report.verifications[0].support, UNSUPPORTED)
        self.assertEqual(report.verifications[0].mismatched_numbers, ("3.84 kbps",))

    def test_uncertain_cjk_only(self):
        # CJK claim whose run is absent -> uncertain (possible synonymy).
        report = self.verify("载波间隔为二百千赫兹[1]。")
        self.assertEqual(report.verifications[0].support, UNCERTAIN)

    def test_multi_citation_mixed(self):
        # Two claims separated by a sentence boundary; each carries its own
        # citation and verdict (mixed supported / unsupported).
        report = self.verify("GSM使用GMSK调制[1]。WCDMA使用GMSK调制[2]。")
        self.assertEqual(report.verifications[0].support, SUPPORTED)
        self.assertEqual(report.verifications[1].support, UNSUPPORTED)

    def test_multi_citation_single_claim(self):
        # A single claim citing multiple evidence chunks (multi-citation).
        report = self.verify("GSM使用GMSK调制，载波间隔为200 kHz[1][2]。")
        self.assertEqual(report.verifications[0].citation_ids, (1, 2))
        # Chunk 1 contains both "GSM" and "GMSK" and the 200 kHz number, so the
        # union of the cited evidence supports the claim.
        self.assertEqual(report.verifications[0].support, SUPPORTED)

    def test_reason_codes_present(self):
        report = self.verify("GSM使用GMSK调制[1]。")
        self.assertIn("supported_key_terms", report.verifications[0].reason_codes)


class ReportContractTests(VerifierFixture, unittest.TestCase):
    def test_report_to_dict_serializable(self):
        report = self.verify("GSM使用GMSK调制[1]。")
        data = report.to_dict()
        self.assertEqual(data["verifier_version"], CITATION_VERIFIER_VERSION)
        self.assertEqual(data["citation_count"], 1)
        self.assertIn("citation_coverage", data)

    def test_module_level_verify_answer(self):
        report = verify_answer("GSM使用GMSK调制[1]。", self.evidence)
        self.assertIsInstance(report, CitationReport)


if __name__ == "__main__":
    unittest.main()
