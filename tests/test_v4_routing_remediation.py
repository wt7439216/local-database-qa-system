"""V4.5 Routing over-trigger remediation tests.

Root cause proven mechanically from the frozen V4.3 attribution evidence:
``LOCATION_WORDS`` matched the substrings "在哪" / "出处" inside questions
whose primary intent is NOT a position request, so four cases were routed to
the deterministic ``locate`` template instead of ``qa``:

    md-004  "分集接收在哪些文档中被提到？"        ("在哪" inside "在哪些文档")
    md-019  "…这一结论在哪个文档中？"             ("在哪" inside "在哪个文档")
    cit-001 "GSM 使用 GMSK 调制，请指出出处。"     ("出处")
    cit-007 "循环前缀的作用？请引用出处。"          ("出处")

The correction separates a *positional* intent from (a) a document/collection
container reference ("which document") and (b) provenance ("source" ->
citation).  These tests pin BOTH directions:

* the four targets leave the locate route,
* every genuine locate query keeps its locate / locate_chapter route
  (NEW_GENUINE_LOCATE_MISROUTES == 0), and
* the frozen ``LOCATION_WORDS`` inventory itself is untouched, so
  ``engine_v2.clean_location_query`` (locate answer scaffolding) is unchanged.

Fully offline: no model, no library, no network.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from core.query_router import (
    LOCATION_WORDS,
    QueryRouter,
    classify_route,
    is_location_intent,
)

_ROOT = Path(__file__).resolve().parent.parent
_EVAL = _ROOT / "eval"
_GOLDEN = _EVAL / "v3_final_golden.json"

_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import eval_v4_baseline as baseline  # noqa: E402

# The four proven V4.5 routing targets (frozen golden `expected_route` = qa).
TARGETS = {
    "md-004": "分集接收在哪些文档中被提到？",
    "md-019": "GSM 和 WCDMA 需要对抗多径衰落，这一结论在哪个文档中？",
    "cit-001": "GSM 使用 GMSK 调制，请指出出处。",
    "cit-007": "循环前缀的作用？请引用出处。",
}

# Genuine locate queries that ALREADY routed to locate / locate_chapter before
# the patch (frozen pre-patch behavior).  A patch that moves any of these away
# from the locate family is a regression by definition.
PRE_PATCH_LOCATE_ROUTED = (
    "loc-001", "loc-002", "loc-003", "loc-004", "loc-005", "loc-006",
    "loc-007", "loc-008", "loc-011", "loc-012", "loc-013", "loc-014",
    "loc-015", "loc-016", "loc-017", "loc-018", "loc-019", "loc-020",
)

LOCATE_ROUTES = {"locate", "locate_chapter"}


class TestTargetsLeaveLocateRoute(unittest.TestCase):
    """G2-G5: the four proven over-triggers no longer enter the locate route."""

    def setUp(self) -> None:
        self.router = QueryRouter()

    def test_targets_route_to_qa(self):
        for case_id, query in TARGETS.items():
            decision = self.router.route(query)
            self.assertEqual(decision.route, "qa", f"{case_id}: {query}")
            self.assertEqual(decision.reason_code, "DEFAULT_QA", case_id)

    def test_targets_are_not_location_intent(self):
        for case_id, query in TARGETS.items():
            self.assertFalse(is_location_intent(query), f"{case_id}: {query}")

    def test_golden_expects_qa_for_the_targets(self):
        # Guards the premise: the targets are golden `expected_route == qa`.
        cases = {c["id"]: c for c in json.loads(_GOLDEN.read_text(encoding="utf-8"))["cases"]}
        for case_id, query in TARGETS.items():
            self.assertEqual(cases[case_id]["query"], query, case_id)
            self.assertEqual(cases[case_id]["expected_route"], "qa", case_id)


class TestGenuineLocateProtected(unittest.TestCase):
    """G6: no new genuine-locate misroutes."""

    def setUp(self) -> None:
        self.router = QueryRouter()
        self.cases = {c["id"]: c for c in json.loads(_GOLDEN.read_text(encoding="utf-8"))["cases"]}

    def test_pre_patch_locate_routes_are_preserved(self):
        for case_id in PRE_PATCH_LOCATE_ROUTED:
            query = self.cases[case_id]["query"]
            self.assertIn(
                self.router.route(query).route, LOCATE_ROUTES,
                f"{case_id} regressed away from the locate family: {query}",
            )

    def test_golden_locate_baseline_ids_exist(self):
        for case_id in PRE_PATCH_LOCATE_ROUTED:
            self.assertIn(case_id, self.cases)

    def test_page_and_section_phrasings_stay_locate(self):
        for query in (
            "多径衰落在哪一页",
            "多径衰落在哪一页？",
            "在哪一页讲了OFDM",
            "哪里提到过多径",
            "在哪里讲了多径衰落",
            "它在哪里提到？",
            "哪一节讲了循环前缀",
            "RAKE 接收机在哪一节？",
            "在测试文档里，多径传播是第几节？",
            "抗衰落技术是测试文档的第几节？",
            "参数表在测试文档的哪个位置？",
            "为我找一下讲扩频技术的地方",
            "多径衰落在什么地方",
        ):
            self.assertEqual(self.router.route(query).route, "locate", query)

    def test_chapter_phrasings_stay_locate_chapter(self):
        for query in (
            "OFDM在哪一章",
            "软切换在哪一章？",
            "扩频技术在哪个章节",
            "多径衰落在哪个章节",
            "切换相关的内容在教材哪一章？",
        ):
            self.assertEqual(self.router.route(query).route, "locate_chapter", query)

    def test_location_words_inventory_is_unchanged(self):
        # clean_location_query() consumes this exact tuple; the V4.5 fix lives in
        # the routing decision only and must not alter locate answer scaffolding.
        self.assertEqual(
            LOCATION_WORDS,
            ("哪页", "第几页", "哪里", "在哪里", "位置", "出处", "来源", "在哪", "找一下",
             "找到", "找找", "什么地方", "哪些地方", "第几节", "哪一节", "哪些节"),
        )

    def test_pre_existing_under_trigger_is_out_of_scope_for_v4_5(self):
        # "香农公式在书里的哪个部分？" carries a locate intent but never carried
        # a LOCATION_WORDS hit, so it was already routed to qa before V4.5.  That
        # pre-existing UNDER-trigger is NOT part of this phase's proven
        # over-trigger defect; V4.5 deliberately leaves it untouched so the diff
        # stays limited to removing the four over-triggers.
        self.assertEqual(self.router.route("香农公式在书里的哪个部分？").route, "qa")


class TestAdversarialBoundary(unittest.TestCase):
    """Both failure directions from the authorization (G7 boundary intent)."""

    def setUp(self) -> None:
        self.router = QueryRouter()

    def test_location_words_do_not_swallow_qa_questions(self):
        # Container ("which document") and provenance ("source") phrasings are qa.
        for query in (
            "分集接收在哪些文档中被提到？",
            "GSM 和 WCDMA 需要对抗多径衰落，这一结论在哪个文档中？",
            "分别出现在哪些文档里？",
            "这个结论的出处是什么？",
            "GSM 使用 GMSK 调制，请指出出处。",
            "循环前缀的作用？请引用出处。",
            "这段话的来源是什么？",
        ):
            self.assertEqual(self.router.route(query).route, "qa", query)

    def test_qa_does_not_swallow_genuine_locate(self):
        for query in (
            "书中在哪解释了这个公式为什么成立？",
            "在哪里可以看到它的定义？",
            "公式在书中什么地方推导过？",
        ):
            self.assertIn(self.router.route(query).route, LOCATE_ROUTES, query)


class TestPositionIntentClassification(unittest.TestCase):
    """Unit-level contract of the new predicate."""

    def test_position_units_are_positional(self):
        for query in ("在哪一页", "哪个位置", "哪里", "哪一章节", "哪些地方", "第几节"):
            self.assertTrue(is_location_intent(query), query)

    def test_container_reference_is_not_positional(self):
        for query in ("在哪些文档中", "在哪个文档中", "在哪本书里", "在哪份资料里"):
            self.assertFalse(is_location_intent(query), query)

    def test_provenance_is_not_positional(self):
        self.assertFalse(is_location_intent("请指出出处"))
        self.assertFalse(is_location_intent("请引用来源"))

    def test_provenance_with_explicit_position_stays_positional(self):
        # "出处在哪里" still asks for a position of the source.
        self.assertTrue(is_location_intent("这段内容的出处在哪里？"))

    def test_bare_where_is_positional(self):
        self.assertTrue(is_location_intent("在哪"))

    def test_classify_route_reflects_the_predicate(self):
        self.assertEqual(classify_route("分集接收在哪些文档中被提到？"), "qa")
        self.assertEqual(classify_route("多径衰落在哪一页？"), "locate")


class TestV45BaselineGovernance(unittest.TestCase):
    """G14-G17: new child baseline, immutable history, untouched golden."""

    # V4.6.2 identity anchors are CANONICAL (line-ending portable).  The raw
    # Windows-CRLF byte anchors recorded by V4.4.1 / V4.2 are preserved below as
    # historical provenance only (platform-specific; no longer the cross-platform
    # acceptance contract).
    INITIAL_BASELINE_CANONICAL_SHA256 = "43907c9844594f2820c60d527cbf6c3a7732be8936a224c6258632ac5e8ae73a"
    GOLDEN_CANONICAL_SHA256 = "872cf0604d0e31dce02ee8d9f7be02a6c63f671a443496194d9b5f056f9e1171"
    INITIAL_BASELINE_RAW_CRLF_SHA256 = "371506a99ec7094cad486acb108f33fb66e6a357f31e9ed9e23fcd6ac1f5870f"
    GOLDEN_RAW_CRLF_SHA256 = "31a68507456714c9a4a55a2aeefaa8ac68dd567ff343b49dfe688cb7791a83fb"

    def _load(self, name: str) -> dict:
        return json.loads((_EVAL / name).read_text(encoding="utf-8"))

    def test_initial_baseline_is_canonically_identical(self):
        digest = baseline.canonical_sha256_file(_EVAL / "v4_initial_baseline.json")
        self.assertEqual(digest, self.INITIAL_BASELINE_CANONICAL_SHA256)

    def test_golden_is_canonically_identical(self):
        digest = baseline.canonical_sha256_file(_GOLDEN)
        self.assertEqual(digest, self.GOLDEN_CANONICAL_SHA256)

    def test_historical_raw_anchors_are_documented_provenance(self):
        self.assertNotEqual(self.INITIAL_BASELINE_RAW_CRLF_SHA256, self.INITIAL_BASELINE_CANONICAL_SHA256)
        self.assertNotEqual(self.GOLDEN_RAW_CRLF_SHA256, self.GOLDEN_CANONICAL_SHA256)

    def test_v4_5_stage_baseline_identity(self):
        stage = self._load("v4_5_routing_baseline.json")
        self.assertEqual(stage["baseline_identity"]["baseline_id"], "V4_5_ROUTING_BASELINE")
        self.assertEqual(stage["baseline_identity"]["baseline_role"], "POST_V4_5_ROUTING_BASELINE")
        self.assertEqual(stage["stage_identity"]["parent_baseline"], "V4_4_SCOPE_REMEDIATION_BASELINE")
        self.assertEqual(stage["metrics"]["invalid_citation_count"], 0)
        self.assertEqual(stage["metrics"]["citation_scope_violation"], 0)

    def test_lineage_chain(self):
        lineage = self._load("v4_baseline_lineage.json")
        by_id = {b["baseline_id"]: b for b in lineage["baselines"]}
        # V4.5 remains an immutable historical stage; V4.6.1 / V4.6.2 later appended
        # their children and advanced the current pointer
        # (see test_live_production_hash_guard.py).
        self.assertEqual(
            [b["baseline_id"] for b in lineage["baselines"]],
            [
                "V4_INITIAL_BASELINE",
                "V4_4_SCOPE_REMEDIATION_BASELINE",
                "V4_5_ROUTING_BASELINE",
                "V4_6_1_EMBEDDING_IDENTITY_BASELINE",
                "V4_6_2_HASH_PORTABILITY_BASELINE",
            ],
        )
        self.assertEqual(lineage["current_baseline_id"], "V4_6_2_HASH_PORTABILITY_BASELINE")
        self.assertEqual(
            by_id["V4_5_ROUTING_BASELINE"]["parent_baseline"], "V4_4_SCOPE_REMEDIATION_BASELINE"
        )
        self.assertEqual(
            by_id["V4_6_1_EMBEDDING_IDENTITY_BASELINE"]["parent_baseline"],
            "V4_5_ROUTING_BASELINE",
        )
        self.assertTrue(by_id["V4_INITIAL_BASELINE"]["immutable"])
        self.assertTrue(by_id["V4_4_SCOPE_REMEDIATION_BASELINE"]["immutable"])
        self.assertTrue(by_id["V4_5_ROUTING_BASELINE"]["immutable"])

    def test_v4_5_production_hash_differs_from_parent(self):
        stage = self._load("v4_5_routing_baseline.json")
        parent = self._load("v4_4_scope_remediation_baseline.json")
        self.assertNotEqual(
            stage["artifact_hashes"]["production_source_sha256"],
            parent["artifact_hashes"]["production_source_sha256"],
        )

    def test_remediation_evidence_gate_passed(self):
        evidence = self._load("v4_routing_remediation.json")
        self.assertTrue(evidence["gate_results"]["V4_5_GATE_PASS"])
        self.assertEqual(evidence["before_after_route_traces"]["changed_cases"], list(TARGETS))
        self.assertEqual(evidence["genuine_locate_controls"]["new_genuine_locate_misroutes"], [])


if __name__ == "__main__":
    unittest.main()
