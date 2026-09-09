"""Deterministic citation completion (Q2.2).

Conservative post-processing that attaches a citation marker to an *uncited*
factual claim only when exactly one in-scope evidence chunk is deterministically
SUPPORTED by the Q3/Q3.1 verifier.  This is NOT a second retrieval: it uses
only the evidence already sent to the model (``evidence_texts``), and never
re-fetches, expands scope, or consults an LLM / NLI / external source.

Selector contract (``citation-completion-v1``): **unique-supported-only**.

- exactly one SUPPORTED candidate (valid + in-scope) -> MAY_AUTOFILL;
- 2+ SUPPORTED candidates -> AMBIGUOUS -> NO_AUTOFILL;
- only UNCERTAIN -> NO_AUTOFILL (semantic synonymy / acronym / negation ...);
- only UNSUPPORTED -> NO_AUTOFILL (number mismatch / missing key term / true
  contradiction / true missing entity);
- invalid / out-of-scope candidate -> NO_AUTOFILL (hard gate).

The only user-visible content change is appending a legal citation marker after
an existing factual claim; no factual text / number / unit / order / refusal is
ever changed.  Claim-to-text mapping is positional (sentence offsets), never a
naive ``str.replace``.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from core.citation_verifier import (
    SUPPORTED,
    UNCERTAIN,
    DeterministicCitationVerifier,
    citation_numbers,
    is_factual_claim,
)

CITATION_COMPLETION_VERSION = "citation-completion-v1"

# Sentence boundary mirrors the verifier's claim segmentation so a "claim" here
# maps 1:1 onto a verifier claim.
_SENTENCE_BOUNDARY = re.compile(r"[。！？!?；;\n]+")


@dataclass
class CompletionStats:
    """Additive telemetry for one completion pass (JSON serializable)."""

    claims_seen: int = 0
    uncited_claims: int = 0
    autofill_attempts: int = 0
    autofill_success: int = 0
    ambiguous_skips: int = 0
    uncertain_skips: int = 0
    unsupported_skips: int = 0
    invalid_skips: int = 0
    mapping_failures: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "claims_seen": self.claims_seen,
            "uncited_claims": self.uncited_claims,
            "autofill_attempts": self.autofill_attempts,
            "autofill_success": self.autofill_success,
            "ambiguous_skips": self.ambiguous_skips,
            "uncertain_skips": self.uncertain_skips,
            "unsupported_skips": self.unsupported_skips,
            "invalid_skips": self.invalid_skips,
            "mapping_failures": self.mapping_failures,
        }


def _split_with_spans(answer: str) -> list[tuple[int, int, str]]:
    """Split into sentence-ish segments, returning (insert_pos, end_pos, text).

    ``insert_pos`` is the absolute offset of the end of the stripped claim text
    (immediately before the trailing sentence boundary), which is where a new
    citation marker should be inserted.  Positions are relative to ``answer``.
    """
    segments: list[tuple[int, int, str]] = []
    pos = 0
    for match in _SENTENCE_BOUNDARY.finditer(answer):
        raw = answer[pos:match.start()]
        stripped = raw.strip()
        if stripped:
            insert_pos = pos + len(raw.rstrip())
            segments.append((insert_pos, match.start(), stripped))
        pos = match.end()
    raw = answer[pos:]
    stripped = raw.strip()
    if stripped:
        segments.append((pos + len(raw.rstrip()), len(answer), stripped))
    return segments


def _select_unique_supported(
    claim_text: str,
    evidence_texts: dict[int, str],
    verifier: DeterministicCitationVerifier,
) -> tuple[int | None, str]:
    """Return (evidence_id, reason) for the unique-supported selector.

    reason is one of: unique_supported / multiple_supported / uncertain_only /
    unsupported_only / invalid_candidate.
    """
    supported: list[int] = []
    saw_uncertain = False
    saw_invalid = False
    for cid, evidence_text in evidence_texts.items():
        report = verifier.verify(
            f"{claim_text}[{cid}]",
            {cid: evidence_text},
            citation_count=len(evidence_texts),
        )
        if report.invalid_citation_count > 0:
            saw_invalid = True
            continue
        support = report.verifications[0].support if report.verifications else None
        if support == SUPPORTED:
            supported.append(cid)
        elif support == UNCERTAIN:
            saw_uncertain = True
    if len(supported) == 1:
        return supported[0], "unique_supported"
    if len(supported) > 1:
        return None, "multiple_supported"
    if saw_uncertain:
        return None, "uncertain_only"
    if saw_invalid:
        return None, "invalid_candidate"
    return None, "unsupported_only"


def complete_citations(
    answer: str,
    evidence_texts: dict[int, str],
    verifier: DeterministicCitationVerifier | None = None,
) -> tuple[str, CompletionStats]:
    """Attach citations to uncited factual claims (unique-supported-only).

    Returns ``(completed_answer, stats)``.  The input ``answer`` must already be
    citation-normalized (existing markers valid / ranges expanded) and use the
    same pre-renumber evidence ids as ``evidence_texts``.
    """
    verifier = verifier or DeterministicCitationVerifier()
    stats = CompletionStats()
    if not evidence_texts:
        return answer, stats

    segments = _split_with_spans(answer)
    insertions: list[tuple[int, int]] = []

    for insert_pos, _end_pos, stripped in segments:
        stats.claims_seen += 1
        if citation_numbers(stripped):
            continue  # already cited -> DO_NOT_TOUCH
        if not is_factual_claim(stripped):
            continue  # not a factual claim -> nothing to complete
        stats.uncited_claims += 1
        stats.autofill_attempts += 1

        candidate, reason = _select_unique_supported(stripped, evidence_texts, verifier)
        if candidate is None:
            if reason == "multiple_supported":
                stats.ambiguous_skips += 1
            elif reason == "uncertain_only":
                stats.uncertain_skips += 1
            elif reason == "invalid_candidate":
                stats.invalid_skips += 1
            else:
                stats.unsupported_skips += 1
            continue

        stats.autofill_success += 1
        insertions.append((insert_pos, candidate))

    # Insert from the end so earlier offsets stay valid (no string rebuild bugs).
    for insert_pos, cid in sorted(insertions, reverse=True):
        answer = answer[:insert_pos] + f"[{cid}]" + answer[insert_pos:]

    return answer, stats
