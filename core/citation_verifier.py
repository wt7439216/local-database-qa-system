"""Deterministic citation quality closure (Phase F.2 / v3.5).

Single business truth for the *Layer-1* citation quality contract.  This
module owns:

- claim segmentation (deterministic factual-claim heuristic),
- citation validity (does a citation reference a real, present evidence chunk),
- citation coverage (cited factual claims / factual claims),
- deterministic support (key-term / number / unit overlap between a claim and
  its cited evidence),
- reason codes and the verifier version.

Boundary (Phase F.2 contract): this module is **deterministic / offline /
testable / ordinary-CI-compatible**.  It never calls an LLM, a NLI model, an
embedding model, a reranker or any external service.  Anything that requires
semantic entailment (synonymy, paraphrase, unit conversion, CJK entailment
beyond deterministic token overlap) is reported as ``UNCERTAIN`` and is a
``F.3 CANDIDATE`` — never silently promoted to ``SUPPORTED``.

The support labels are strictly four-valued:

- ``SUPPORTED``     — deterministic evidence is sufficient;
- ``UNSUPPORTED``   — a deterministic conflict / absence is present;
- ``UNCERTAIN``     — requires semantic understanding (synonymy / conversion /
                      non-exact overlap that may still genuinely support);
- ``NOT_APPLICABLE``— the claim is not a factual claim at all, so support is
                      undefined.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

# Bump whenever the deterministic contract changes; recorded in telemetry and
# offline eval so stale results can be detected.
CITATION_VERIFIER_VERSION = "f2-v4"

# Support state enum.
SUPPORTED = "SUPPORTED"
UNSUPPORTED = "UNSUPPORTED"
UNCERTAIN = "UNCERTAIN"
NOT_APPLICABLE = "NOT_APPLICABLE"

SUPPORT_STATES = (SUPPORTED, UNSUPPORTED, UNCERTAIN, NOT_APPLICABLE)

# Reason codes (deterministic, stable, lowercase-with-underscore).
REASON_SUPPORTED_KEY_TERMS = "supported_key_terms"
REASON_SUPPORTED_NUMBER = "supported_number"
REASON_UNSUPPORTED_MISSING_KEY_TERM = "unsupported_missing_key_term"
REASON_UNSUPPORTED_NUMBER_MISMATCH = "unsupported_number_mismatch"
REASON_UNSUPPORTED_NO_EVIDENCE = "unsupported_no_evidence"
REASON_UNCERTAIN_PARAPHRASE = "uncertain_paraphrase"
REASON_UNCERTAIN_CJK_ONLY = "uncertain_cjk_only"
REASON_UNCERTAIN_NO_DETERMINISTIC_SIGNAL = "uncertain_no_deterministic_signal"
REASON_NOT_APPLICABLE = "not_applicable"


# Latin units (case-normalised) excluded from key-term extraction so "5 MHz"
# is treated as a number+unit check, not as a "mhz" entity.
LATIN_UNITS = {
    "db", "dbm", "dbi", "hz", "khz", "mhz", "ghz", "bit", "bits",
    "byte", "bytes", "kbps", "mbps", "gbps", "bps", "ms", "s", "km",
    "m", "cm", "mm", "um", "nm", "ghz", "khz", "dbm", "dbw",
}

# Latin document-format markers that are not technology entities.  A catalog
# line like "（PDF 第0–0页）" must not make "pdf" a required key term.
_NON_ENTITY_LATIN = {
    "pdf", "doc", "docx", "txt", "md", "markdown", "ppt", "pptx",
    "xls", "xlsx", "csv",
}

# Generic Latin words that appear in an expanded acronym ("Time Division
# Multiple Access") but are not themselves a technology entity.  Requiring
# "time"/"division"/"multiple"/"access" to appear literally in evidence that
# only carries the acronym "TDMA" is a deterministic false negative.
_GENERIC_LATIN_STOPWORDS = {
    "time", "division", "multiple", "access", "code", "frequency",
    "channel", "division", "multiplexing",
}

# A bracket group that is *not* a citation: a number glued to a Latin unit
# (e.g. "[450]MHz") is a value, not a reference.  A leading minus is allowed
# so malformed ``[-1]`` references are still recognised (and then rejected as
# invalid) rather than silently ignored.
_CITATION_TOKEN = re.compile(r"\[(-?\d+)\](?![A-Za-z])")

# A citation group / range like "[3,6-7]" or "[2][3]".  A claim consisting of
# only such tokens carries no factual content.
_CITATION_GROUP_RE = re.compile(r"\[[\d,\s\-–—]+\]")

# A sentence-ish boundary for claim splitting.
_SENTENCE_BOUNDARY = re.compile(r"[。！？!?；;\n]+")

# Number patterns: integer / decimal / with thousands separators; the capture
# keeps the raw numeric token so we can compare magnitudes, not strings.
_NUMBER_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")

# CJK character class (for key-term extraction and CJK-only detection).
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")

# Latin key-term token (alphanumeric runs, length >= 2 after unit filtering).
_LATIN_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9./+-]*")


def _normalize_compact(text: str) -> str:
    """Lowercase, strip whitespace and drop non-alphanumeric punctuation glue.

    Removing hyphens/slashes/dots lets "SC-FDMA" match "scfdma" and "S/N" match
    "sn" in evidence — these are orthographic variants, not semantic inference.
    """
    text = str(text or "")
    text = re.sub(r"\s+", "", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", text)
    return text


def _extract_numbers(text: str) -> list[float]:
    """Deterministic numeric token extraction (integer / decimal / sign)."""
    values: list[float] = []
    for match in _NUMBER_RE.finditer(str(text or "")):
        raw = match.group(0).replace(",", "")
        try:
            values.append(float(raw))
        except ValueError:
            continue
    return values


# number followed by an optional unit token: "5 MHz", "270.833 kbit/s", "3.84 Mcps".
_NUMBER_WITH_UNIT_RE = re.compile(
    r"(-?\d[\d,]*(?:\.\d+)?)\s*([A-Za-z][A-Za-z0-9/.]*)?"
)


def _extract_number_units(text: str) -> list[tuple[float, str]]:
    """Extract (magnitude, unit) pairs where a number is followed by a unit.

    A number with no following Latin unit yields an empty unit string.  The
    unit is case-normalised and symbol-stripped so "kHz"/"KHZ"/"khz" agree.
    """
    pairs: list[tuple[float, str]] = []
    for match in _NUMBER_WITH_UNIT_RE.finditer(str(text or "")):
        raw, unit = match.group(1), match.group(2) or ""
        try:
            magnitude = float(raw.replace(",", ""))
        except ValueError:
            continue
        unit_norm = re.sub(r"[^A-Za-z0-9]", "", unit).lower()
        pairs.append((magnitude, unit_norm))
    return pairs


# Non-factual number patterns.  These carry no scientific/factual numeric
# payload and must not drive a number-mismatch verdict:
#   - "材料1" / "材料1和材料2"  (material references, not values)
#   - "1." / "2、" at line start (list item numbering)
#   - "第1章" / "第10–62页" (structural locator metadata)
_MATERIAL_REF_RE = re.compile(r"材料\s*\d+(?:\s*[、,和]\s*\d+)*")
_STRUCTURAL_LOCATOR_RE = re.compile(r"第\s*\d+\s*[章页节]")
_PAGE_RANGE_RE = re.compile(r"第\s*\d+\s*[–—-]\s*\d+\s*页")
_LEADING_LIST_NUMBER_RE = re.compile(r"(?m)^\s*[-*•·]?\s*\d+[.、)）]\s*")
# SNR / ratio symbols whose trailing digit is a subscript ("E/N0", "Eb/N0"),
# not a factual magnitude.  Stripping them keeps "E/N0=0.7dB" from extracting a
# spurious "0" while still keeping the real value "0.7".
_SNR_SYMBOL_RE = re.compile(r"[A-Za-z]+\s*/\s*[A-Za-z]*\d+")


def _strip_non_factual_numbers(text: str) -> str:
    """Remove structural numbers (material refs / list numbers / locators).

    These are deterministic, context-free surface patterns — not semantic
    inference.  A claim like "第1章 …（PDF 第10–62页）[1]" carries locator
    metadata whose digits are not a factual claim about the evidence content.
    """
    text = _MATERIAL_REF_RE.sub("", str(text or ""))
    text = _STRUCTURAL_LOCATOR_RE.sub("", text)
    text = _PAGE_RANGE_RE.sub("", text)
    text = _SNR_SYMBOL_RE.sub("", text)
    text = _LEADING_LIST_NUMBER_RE.sub("", text)
    return text


def _latin_key_terms(text: str, min_length: int = 2) -> set[str]:
    """Latin technology/entity tokens that should appear in cited evidence.

    Units are excluded (they belong to the number/unit check).  Returns a
    lowercased, symbol-stripped set.
    """
    terms: set[str] = set()
    # Units glued to a number belong to the number/unit check, not key terms.
    # Without this, "270.833 kbit/s" would yield a "kbits" key term that can
    # never match the raw "kbit/s" in the evidence (which keeps its slash),
    # turning a correct claim into a spurious UNSUPPORTED.
    number_units = {unit for _magnitude, unit in _extract_number_units(text) if unit}
    for token in _LATIN_TOKEN_RE.findall(str(text or "")):
        value = re.sub(r"[^A-Za-z0-9]", "", token).lower()
        if (
            len(value) >= min_length
            and "/" not in token  # SNR symbols ("E/N0") / rate units are not entities
            and value not in LATIN_UNITS
            and value not in number_units
            and value not in _NON_ENTITY_LATIN
            and value not in _GENERIC_LATIN_STOPWORDS
        ):
            terms.add(value)
    return terms


def _cjk_key_terms(text: str) -> list[str]:
    """Extract contiguous CJK runs as key-term candidates.

    Chinese has no word boundaries, so we emit maximal CJK runs (segmented by
    punctuation / latin / digits).  These are the deterministic CJK key-term
    units; semantic synonymy is out of scope (UNCERTAIN territory).
    """
    runs = re.findall(r"[\u4e00-\u9fff]+", str(text or ""))
    # Keep runs of length >= 2; single CJK char is too ambiguous to assert.
    return [run for run in runs if len(run) >= 2]


# CJK meta-discourse / connective phrases that carry no factual content.  A
# claim consisting solely of these is NOT_APPLICABLE, not a factual claim.
_CJK_META_PHRASES = {
    "回答如下", "详见材料", "可参考", "请参考", "参见", "相关内容", "总结如下",
    "综上所述", "由此可知", "需要注意的是", "注意", "例如", "比如", "换句话说",
    "也就是说", "关于这个问题", "对于上述问题", "简单来说", "具体来说",
}


def _is_pure_meta_discourse(text: str) -> bool:
    """True when the claim text is connective/meta with no factual payload."""
    body = text.strip()
    if not body:
        return True
    # If every CJK run is a meta phrase, the claim carries no factual content.
    runs = re.findall(r"[\u4e00-\u9fff]+", body)
    if not runs:
        return False
    return all(run in _CJK_META_PHRASES for run in runs)


@dataclass(frozen=True)
class Claim:
    """A single factual claim extracted from an answer.

    ``text``        — the claim's own text (a sentence-ish fragment).
    ``citation_ids``— the citation numbers attached to this claim, in order of
                      first appearance (empty when the claim is uncited).
    ``is_factual``  — deterministic factual-claim heuristic verdict.
    """

    text: str
    citation_ids: tuple[int, ...]
    is_factual: bool


@dataclass(frozen=True)
class CitationVerification:
    """Deterministic Layer-1 verification of one claim against its evidence."""

    claim_index: int
    claim_text: str
    citation_ids: tuple[int, ...]
    support: str
    reason_codes: tuple[str, ...]
    # Deterministic signals that drove the verdict (for tests/telemetry).
    missing_key_terms: tuple[str, ...] = ()
    mismatched_numbers: tuple[str, ...] = ()


@dataclass(frozen=True)
class CitationReport:
    """Aggregate deterministic citation quality report for one answer."""

    claims: list[Claim]
    verifications: list[CitationVerification]
    verifier_version: str = CITATION_VERIFIER_VERSION
    # Raw counts (the single source of truth for the telemetry projection).
    citation_count: int = 0
    factual_claim_count: int = 0
    cited_claim_count: int = 0
    supported_claim_count: int = 0
    unsupported_claim_count: int = 0
    uncertain_claim_count: int = 0
    invalid_citation_count: int = 0
    citation_scope_violation: int = 0

    @property
    def citation_coverage(self) -> float | None:
        """cited factual claims / factual claims (None when no factual claims)."""
        if self.factual_claim_count == 0:
            return None
        return round(self.cited_claim_count / self.factual_claim_count, 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verifier_version": self.verifier_version,
            "citation_count": self.citation_count,
            "factual_claim_count": self.factual_claim_count,
            "cited_claim_count": self.cited_claim_count,
            "citation_coverage": self.citation_coverage,
            "supported_claim_count": self.supported_claim_count,
            "unsupported_claim_count": self.unsupported_claim_count,
            "uncertain_claim_count": self.uncertain_claim_count,
            "invalid_citation_count": self.invalid_citation_count,
            "citation_scope_violation": self.citation_scope_violation,
            "verifications": [
                {
                    "claim_index": v.claim_index,
                    "support": v.support,
                    "reason_codes": list(v.reason_codes),
                    "missing_key_terms": list(v.missing_key_terms),
                    "mismatched_numbers": list(v.mismatched_numbers),
                }
                for v in self.verifications
            ],
        }


def citation_numbers(answer: str) -> list[int]:
    """The ordered list of citation numbers referenced in the answer text.

    Bracket numbers glued to a Latin unit (e.g. ``[450]MHz``) are excluded —
    they are values, not citations (mirrors ``normalize_citations``).
    """
    return [int(m.group(1)) for m in _CITATION_TOKEN.finditer(str(answer or ""))]


def is_factual_claim(text: str) -> bool:
    """Deterministic factual-claim heuristic.

    A claim is treated as factual when it carries verifiable content: at least
    one Latin key term, a CJK term, or a numeric value.  Pure connective /
    meta sentences ("可参考[1]", "详见材料", "回答如下") carry no such signal
    and are NOT_APPLICABLE for support purposes.  This is deliberately a
    heuristic, not a semantic classifier; it errs toward ``factual`` only when
    there is a concrete verifiable token, keeping coverage honest.
    """
    text = str(text or "").strip()
    if not text:
        return False
    # Strip citation tokens (single + group/range) so a bare "[3,6-7][2]" is
    # not mistaken for a factual claim via its numeric digits.
    body = _CITATION_TOKEN.sub("", text)
    body = _CITATION_GROUP_RE.sub("", body)
    if not body.strip():
        return False
    if _is_pure_meta_discourse(body):
        return False
    if _latin_key_terms(body):
        return True
    if _cjk_key_terms(body):
        return True
    if _extract_numbers(body):
        return True
    return False


def split_claims(answer: str) -> list[Claim]:
    """Segment an answer into claims and attach citation numbers.

    The answer is split on sentence boundaries; each fragment becomes a claim.
    Citation numbers are attached to the claim they lexically precede, which
    mirrors how a reader maps ``...结论[1]。`` to the preceding sentence.  A
    leading citation (``[1] 结论...``) attaches to the following claim.
    """

    answer = str(answer or "")
    # Split, keeping the citation tokens inline.  We track the cursor so we
    # can assign citations to the claim that contains them.
    segments = _SENTENCE_BOUNDARY.split(answer)
    claims: list[Claim] = []
    for raw in segments:
        text = raw.strip()
        if not text:
            continue
        ids = tuple(citation_numbers(text))
        claims.append(Claim(text=text, citation_ids=ids, is_factual=is_factual_claim(text)))
    return claims


def valid_citation_ids(
    answer: str,
    citation_count: int,
    present_ids: set[int] | None = None,
) -> tuple[list[int], list[int]]:
    """Split referenced citation numbers into (valid, invalid).

    ``citation_count`` is the number of evidence chunks actually available
    (sent contexts + deterministic chapter citations).  A referenced number
    outside ``[1, citation_count]`` is invalid.  ``present_ids`` may further
    constrain validity to evidence ids that genuinely exist (e.g. after scope
    or evidence pruning); when omitted, the ``[1, citation_count]`` range is
    the only contract.
    """
    numbers = citation_numbers(answer)
    valid: list[int] = []
    invalid: list[int] = []
    for number in numbers:
        if number < 1 or number > citation_count:
            invalid.append(number)
            continue
        if present_ids is not None and number not in present_ids:
            invalid.append(number)
            continue
        if number not in valid:
            valid.append(number)
    return valid, invalid


class DeterministicCitationVerifier:
    """Deterministic Layer-1 citation verifier (no LLM / NLI / external IO)."""

    def verify(
        self,
        answer: str,
        evidence_texts: dict[int, str],
        *,
        citation_count: int | None = None,
    ) -> CitationReport:
        """Verify an answer against its cited evidence.

        ``evidence_texts`` maps citation number -> evidence text.  ``citation_count``
        bounds validity when it exceeds the keys of ``evidence_texts`` (e.g. the
        deterministic chapter citations appended after model contexts).  When
        omitted it defaults to ``max(evidence_texts)``.
        """
        evidence_texts = {int(k): str(v or "") for k, v in (evidence_texts or {}).items()}
        if citation_count is None:
            citation_count = max(evidence_texts, default=0)

        claims = split_claims(answer)
        valid, invalid = valid_citation_ids(
            answer, citation_count, present_ids=set(evidence_texts.keys())
        )

        verifications: list[CitationVerification] = []
        cited_claim_count = 0
        supported = 0
        unsupported = 0
        uncertain = 0
        not_applicable = 0

        for index, claim in enumerate(claims):
            if not claim.is_factual:
                verification = CitationVerification(
                    claim_index=index,
                    claim_text=claim.text,
                    citation_ids=claim.citation_ids,
                    support=NOT_APPLICABLE,
                    reason_codes=(REASON_NOT_APPLICABLE,),
                )
                verifications.append(verification)
                not_applicable += 1
                continue

            if claim.citation_ids:
                cited_claim_count += 1
            verification = self._verify_claim(claim, index, evidence_texts)
            verifications.append(verification)
            if verification.support == SUPPORTED:
                supported += 1
            elif verification.support == UNSUPPORTED:
                unsupported += 1
            elif verification.support == UNCERTAIN:
                uncertain += 1
            else:
                not_applicable += 1

        return CitationReport(
            claims=claims,
            verifications=verifications,
            citation_count=len(valid),
            factual_claim_count=sum(1 for c in claims if c.is_factual),
            cited_claim_count=cited_claim_count,
            supported_claim_count=supported,
            unsupported_claim_count=unsupported,
            uncertain_claim_count=uncertain,
            invalid_citation_count=len(invalid),
            citation_scope_violation=0,
        )

    def _verify_claim(
        self,
        claim: Claim,
        index: int,
        evidence_texts: dict[int, str],
    ) -> CitationVerification:
        """Deterministic support for a single factual claim.

        Strategy (Layer-1 only):
          1. no citation  -> UNSUPPORTED (factual claim with no evidence);
          2. cited evidence missing from the map -> UNSUPPORTED (no evidence);
          3. number check: every numeric magnitude in the claim must appear in
             the cited evidence, otherwise UNSUPPORTED (number mismatch);
          4. key-term check: every Latin key term must appear in the cited
             evidence, otherwise UNSUPPORTED (missing key term);
          5. CJK: when the claim has CJK key terms, require deterministic CJK
             run overlap; if a CJK run is absent from the evidence it is
             UNCERTAIN (synonymy is possible) — never UNSUPPORTED on CJK alone;
          6. otherwise SUPPORTED when at least one deterministic signal matched
             and nothing conflicted; UNCERTAIN when no deterministic signal.
        """
        cited_texts = [evidence_texts[cid] for cid in claim.citation_ids if cid in evidence_texts]
        if not claim.citation_ids:
            return CitationVerification(
                claim_index=index,
                claim_text=claim.text,
                citation_ids=(),
                support=UNSUPPORTED,
                reason_codes=(REASON_UNSUPPORTED_NO_EVIDENCE,),
            )
        if not cited_texts:
            return CitationVerification(
                claim_index=index,
                claim_text=claim.text,
                citation_ids=claim.citation_ids,
                support=UNSUPPORTED,
                reason_codes=(REASON_UNSUPPORTED_NO_EVIDENCE,),
            )

        combined = "\n".join(cited_texts)
        compact_combined = _normalize_compact(combined)

        # Strip citation markers before extracting claim signals so ``[1]`` is
        # never mistaken for a numeric value of the claim itself.
        claim_body = _CITATION_TOKEN.sub("", claim.text)

        reason_codes: list[str] = []
        mismatched: list[str] = []

        # --- number + unit check ------------------------------------------
        # Structural numbers (material refs / list numbering / locators) carry
        # no factual payload and are stripped before the numeric check.
        numeric_body = _strip_non_factual_numbers(claim_body)
        claim_numbers = _extract_numbers(numeric_body)
        evidence_numbers = _extract_numbers(combined)
        number_ok = all(number in evidence_numbers for number in claim_numbers)

        unit_conflict = False   # same magnitude, provably different unit
        unit_ambiguous = False  # same magnitude, evidence unit absent (equivalence)

        claim_pairs = _extract_number_units(numeric_body)
        evidence_pairs = _extract_number_units(combined)
        for magnitude, unit in claim_pairs:
            if not unit:
                continue
            evidence_units = {u for m, u in evidence_pairs if m == magnitude}
            if not evidence_units:
                continue  # magnitude absence is handled by number_ok below
            if unit not in evidence_units:
                if any(evidence_units):  # evidence attaches a different unit
                    unit_conflict = True
                else:  # evidence carries the bare magnitude, no unit
                    unit_ambiguous = True

        if claim_numbers and number_ok and not unit_conflict and not unit_ambiguous:
            reason_codes.append(REASON_SUPPORTED_NUMBER)

        if not number_ok or unit_conflict:
            # A deterministic numeric conflict is a hard UNSUPPORTED signal.
            mismatched.extend(str(n) for n in claim_numbers if n not in evidence_numbers)
            if unit_conflict:
                mismatched.extend(
                    f"{magnitude} {unit}".strip()
                    for magnitude, unit in claim_pairs
                    if unit
                    and {u for m, u in evidence_pairs if m == magnitude}
                    and unit not in {u for m, u in evidence_pairs if m == magnitude}
                )
            return CitationVerification(
                claim_index=index,
                claim_text=claim.text,
                citation_ids=claim.citation_ids,
                support=UNSUPPORTED,
                reason_codes=(REASON_UNSUPPORTED_NUMBER_MISMATCH,),
                mismatched_numbers=tuple(mismatched),
            )

        if unit_ambiguous:
            # Magnitude present but evidence unit absent: equivalence/omission,
            # not a provable contradiction — report UNCERTAIN, not UNSUPPORTED.
            return CitationVerification(
                claim_index=index,
                claim_text=claim.text,
                citation_ids=claim.citation_ids,
                support=UNCERTAIN,
                reason_codes=(REASON_UNCERTAIN_NO_DETERMINISTIC_SIGNAL,),
            )

        # --- Latin key-term check ----------------------------------------
        latin_terms = _latin_key_terms(claim_body)
        if latin_terms:
            missing = sorted(term for term in latin_terms if term not in compact_combined)
            if missing:
                return CitationVerification(
                    claim_index=index,
                    claim_text=claim.text,
                    citation_ids=claim.citation_ids,
                    support=UNSUPPORTED,
                    reason_codes=(REASON_UNSUPPORTED_MISSING_KEY_TERM,),
                    missing_key_terms=tuple(missing),
                )
            reason_codes.append(REASON_SUPPORTED_KEY_TERMS)

        # --- CJK key-term check ------------------------------------------
        cjk_terms = _cjk_key_terms(claim_body)
        if cjk_terms:
            # CJK runs longer than 2 chars that are absent are treated as
            # UNCERTAIN (possible synonymy), not UNSUPPORTED.  This is the
            # deterministic CJK contract: we can flag presence, but absence
            # alone is not proof of a contradiction.
            present = [term for term in cjk_terms if term in combined]
            if present and (latin_terms or claim_numbers):
                reason_codes.append(REASON_SUPPORTED_KEY_TERMS)
            if not present and not latin_terms and not claim_numbers:
                return CitationVerification(
                    claim_index=index,
                    claim_text=claim.text,
                    citation_ids=claim.citation_ids,
                    support=UNCERTAIN,
                    reason_codes=(REASON_UNCERTAIN_CJK_ONLY,),
                    missing_key_terms=tuple(cjk_terms),
                )

        # --- verdict ------------------------------------------------------
        if reason_codes:
            return CitationVerification(
                claim_index=index,
                claim_text=claim.text,
                citation_ids=claim.citation_ids,
                support=SUPPORTED,
                reason_codes=tuple(dict.fromkeys(reason_codes)),
            )
        return CitationVerification(
            claim_index=index,
            claim_text=claim.text,
            citation_ids=claim.citation_ids,
            support=UNCERTAIN,
            reason_codes=(REASON_UNCERTAIN_NO_DETERMINISTIC_SIGNAL,),
        )


# Module-level convenience to keep engine orchestration thin.
_DEFAULT_VERIFIER = DeterministicCitationVerifier()


def verify_answer(
    answer: str,
    evidence_texts: dict[int, str],
    *,
    citation_count: int | None = None,
) -> CitationReport:
    return _DEFAULT_VERIFIER.verify(answer, evidence_texts, citation_count=citation_count)
