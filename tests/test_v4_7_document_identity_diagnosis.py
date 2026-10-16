"""V4.7 Document Identity Root-Cause Confirmation + Diagnosis Closure tests.

READ-ONLY and deterministic: these tests never call the answer model. They
re-derive the deterministic diagnostics from the production artifacts and assert
the invariants that make the V4.7 conclusion (and its closure corrections)
mechanical and reproducible.

Coverage:
* T1-T12  the V4.7 closure contract (Product/Measurement separation, anchor gate,
          mechanism taxonomy, raw-evidence preservation, governance).
* plus the preflight / library-identity / counterfactual / frozen-contract
  invariants carried over from the original diagnosis.
"""

from __future__ import annotations

import copy
from contextlib import closing, contextmanager
import hashlib
import json
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "scripts"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import analyze_v4_7_document_identity as dg  # noqa: E402
from product_revision import pre_product_json, pre_product_source_bytes, pre_product_tree  # noqa: E402
from inheritance_peer_fixture import materialize_inheritance_peers  # noqa: E402

ARTIFACT = ROOT / "eval" / "v4_7_document_identity_root_cause.json"
TARGET_CASES = ("md-004", "md-009", "md-015")
CANONICAL_PRODUCTION_HASH = "108fb167ee75a4b8657ad062185b51aef814e0586b9b0be60b7a4cc51141798c"


def historical_production_preflight():
    """Run the real old-stage checks against exact archived production bytes.

    Only the named filesystem inputs change. The canonical hash implementation
    is never patched; today's live product has an independent current guard.
    """
    with pre_product_tree() as historical_root, mock.patch.multiple(
        dg, ROOT=historical_root, LINEAGE=historical_root / "eval/v4_baseline_lineage.json",
    ), mock.patch.object(dg.EVB, "ROOT_DIR", historical_root):
        return dg.production_preflight()


def historical_pipeline_equivalence(*, anchor_available: bool):
    """Compare the old product to the real read-only inheritance peers.

    The diagnostic resolves its peers as siblings of ROOT. Give it a private
    sibling layout containing exact archived V4 bytes and byte-for-byte copies
    of the four files it reads from each frozen peer. Its actual region/AST
    comparison and anchor gate then run unchanged, without treating today's
    changed production source as the historical V4.7 input.
    """
    with pre_product_tree() as archived_root, tempfile.TemporaryDirectory(
        prefix="v47-historical-peers-",
    ) as directory:
        parent = Path(directory)
        historical_root = parent / ROOT.name
        shutil.copytree(archived_root, historical_root)
        # An independently bound eight-file archive preserves the actual peer
        # inputs when a fresh checkout has no siblings, or publication updates
        # the upload sibling. Current sources never impersonate frozen peers.
        origins = materialize_inheritance_peers(parent, ROOT)
        with mock.patch.object(dg, "ROOT", historical_root):
            result = dg.relevant_pipeline_equivalence(anchor_available=anchor_available)
        return {**result, "historical_peer_inputs": origins}


@contextmanager
def synthetic_identity_library():
    """Real SQL mechanics using synthetic rows, never the private C6 identity."""
    with tempfile.TemporaryDirectory(prefix="v47-synthetic-identity-") as directory:
        path = Path(directory) / "synthetic.sqlite3"
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.executescript("""
                CREATE TABLE documents(id TEXT PRIMARY KEY, title TEXT, source_name TEXT,
                                       sha256 TEXT, page_count INTEGER);
                CREATE TABLE chunks(document_id TEXT, kind TEXT, section TEXT);
                CREATE TABLE chunk_fts(heading_text TEXT);
            """)
            for index, title in enumerate(dg.ROLE_LABEL_TO_CANONICAL.values(), 1):
                document_id = f"synthetic-doc-{index}"
                connection.execute("INSERT INTO documents VALUES (?, ?, ?, ?, ?)",
                                   (document_id, title, f"synthetic-{index}.md", "0" * 64, 1))
                connection.execute("INSERT INTO chunks VALUES (?, ?, ?)",
                                   (document_id, "text", "合成章节"))
            connection.execute("INSERT INTO chunk_fts VALUES (?)", ("合成标题，与文档名称不同",))
        with mock.patch.object(dg, "LIBRARY", path):
            yield path


class V47ArtifactMixin:
    @classmethod
    def setUpClass(cls) -> None:
        if not ARTIFACT.is_file():
            raise unittest.SkipTest("V4.7 diagnostic artifact not generated in this workspace")
        cls.payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        cls.payload_text = ARTIFACT.read_text(encoding="utf-8")


class TestV47Preflight(unittest.TestCase):
    def test_artifact_present(self) -> None:
        if not ARTIFACT.is_file():
            self.skipTest("V4.7 diagnostic artifact not generated in this workspace")
        payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(payload["stage"], "V4.7")
        self.assertEqual(payload["mode"], "READ_ONLY_PRODUCT_DIAGNOSIS")

    def test_current_baseline_and_metrics_source(self) -> None:
        preflight = historical_production_preflight()
        self.assertEqual(preflight["current_baseline_id"], "V4_6_2_HASH_PORTABILITY_BASELINE")
        self.assertEqual(preflight["product_metrics_source"], "V4_6_1_EMBEDDING_IDENTITY_BASELINE")
        self.assertFalse(preflight["metrics_recomputed_in_v4_6_2"])
        self.assertTrue(preflight["production_hash_match"])

    def test_live_production_hash_is_canonical(self) -> None:
        preflight = historical_production_preflight()
        self.assertEqual(preflight["live_canonical_production_hash"], CANONICAL_PRODUCTION_HASH)
        self.assertEqual(preflight["canonical_hash_algorithm"], "sha256-path-content-v2-canonical-lf")


class TestV47LibraryIdentityGate(unittest.TestCase):
    def test_environment_equivalence_pass(self) -> None:
        if not dg.LIBRARY.is_file():
            self.skipTest("exact frozen private-library identity unavailable in a source-only checkout")
        gate = dg.library_identity_gate()
        self.assertEqual(gate["environment_equivalence"], "PASS")
        self.assertEqual(gate["current_library_identity"], gate["baseline_library_identity"])
        self.assertEqual(gate["current_library_identity"], gate["metrics_source_library_identity"])

    def test_identity_uses_canonical_implementation(self) -> None:
        with synthetic_identity_library() as path:
            raw = path.read_bytes()
            identity = dg.EVB._library_identity(path)
            self.assertEqual(identity, f"{len(raw)}:{hashlib.sha256(raw).hexdigest()[:16]}")
            self.assertRegex(identity, r"^\d+:[0-9a-f]{16}$")


class TestV47DocumentIdentitySemantics(unittest.TestCase):
    def test_canonical_title_source_is_documents_title(self) -> None:
        with synthetic_identity_library():
            source = dg.canonical_identity_source()
        self.assertEqual(source["canonical_field"], "documents.title")
        self.assertEqual(len(source["documents"]), 2)
        self.assertTrue(all(item["id"].startswith("synthetic-") for item in source["documents"]))

    def test_material_index_semantics_is_chunk_index(self) -> None:
        # V4.7's conclusion belongs to the archived 108f product. Later prompt
        # changes are tested separately as new production behavior.
        source = pre_product_source_bytes("core/engine_v2.py").decode("utf-8")
        self.assertIn("for index, chunk in enumerate(contexts, 1):", source)
        self.assertIn('header = f"[材料{index}｜{chunk.location}]\\n"', source)

    def test_chunk_location_carries_document_title(self) -> None:
        with synthetic_identity_library():
            chunks = dg.canonical_identity_source()["chunk_document_title_join"]
        self.assertEqual(len(chunks), 2)
        self.assertTrue(all(item["document_title"] for item in chunks))

    def test_golden_to_canonical_relations(self) -> None:
        with synthetic_identity_library():
            mapping = dg.golden_to_canonical(
                {d["id"]: d["title"] for d in dg.canonical_identity_source()["documents"]}
            )
        self.assertEqual(mapping["md-004"]["fact_relations"]["教材"]["relation"], "SEMANTIC_ROLE")
        self.assertFalse(mapping["md-004"]["fact_relations"]["教材"]["lexically_in_canonical_title"])
        self.assertEqual(mapping["md-004"]["fact_relations"]["测试文档"]["relation"], "SUBSTRING")
        self.assertEqual(mapping["md-009"]["fact_relations"]["教材"]["relation"], "SEMANTIC_ROLE")
        self.assertEqual(mapping["md-015"]["fact_relations"]["测试文档"]["relation"], "SUBSTRING")


class TestV47CounterfactualProbe(unittest.TestCase):
    def test_counterfactual_uses_canonical_matcher(self) -> None:
        probe = dg.counterfactual_probe()
        for case_id in TARGET_CASES:
            self.assertIn("_build_row", probe[case_id]["evaluator_fact_matcher"])

    def test_canonical_title_only_does_not_satisfy_md004_md009(self) -> None:
        probe = dg.counterfactual_probe()
        self.assertEqual(probe["md-004"]["CANONICAL_TITLE_ONLY_SATISFIES_GOLDEN"], "PARTIAL")
        self.assertEqual(probe["md-009"]["CANONICAL_TITLE_ONLY_SATISFIES_GOLDEN"], "PARTIAL")

    def test_canonical_title_only_satisfies_md015(self) -> None:
        probe = dg.counterfactual_probe()
        self.assertEqual(probe["md-015"]["CANONICAL_TITLE_ONLY_SATISFIES_GOLDEN"], "YES")

    def test_role_label_plus_title_satisfies_all(self) -> None:
        probe = dg.counterfactual_probe()
        for case_id in TARGET_CASES:
            self.assertEqual(
                probe[case_id]["ROLE_LABEL_PLUS_CANONICAL_TITLE_SATISFIES_GOLDEN"], "YES"
            )


# --------------------------------------------------------------------------- #
# T1-T12: V4.7 diagnosis closure contract
# --------------------------------------------------------------------------- #
class TestT1MeasurementDoesNotImplyMixedProduct(V47ArtifactMixin, unittest.TestCase):
    def test_measurement_supported_but_product_not_mixed(self) -> None:
        self.assertEqual(self.payload["measurement_semantic_issue"], "SUPPORTED")
        self.assertEqual(self.payload["mixed_product_root_cause_families"], "NO")
        self.assertEqual(self.payload["product_root_cause_family_shared"], "YES")


class TestT2SharedFamilyDoesNotImplySharedMechanism(V47ArtifactMixin, unittest.TestCase):
    def test_derivation_is_per_case_not_copied_from_family(self) -> None:
        replay = copy.deepcopy(self.payload["per_case_layer_trace"]["md-015"])
        # same family evidence (title visible) but no material-index phrasing:
        replay["raw_vs_final_answer"]["raw_uses_材料N"] = False
        replay["raw_vs_final_answer"]["final_uses_材料N"] = False
        replay["raw_vs_final_answer"]["raw_contains_canonical_title"] = False
        derived = dg.derive_case_generation_mechanism(replay)
        self.assertEqual(derived["primary_mechanism"], "PURE_GENERATION_SYNTHESIS")
        self.assertNotIn("MATERIAL_INDEX_BIAS", derived["mechanism_signature"])

    def test_fields_are_separately_decided(self) -> None:
        self.assertIn("shared_product_root_cause_family", self.payload)
        self.assertIn("shared_generation_mechanism", self.payload)
        self.assertNotEqual(
            self.payload.get("shared_product_root_cause_family"),
            None,
        )


class TestT3DocumentIdentityNotApplicable(V47ArtifactMixin, unittest.TestCase):
    def test_identity_mechanism_not_applicable(self) -> None:
        self.assertEqual(self.payload["document_identity_root_cause"], "NOT_PROVEN")
        self.assertEqual(self.payload["document_identity_mechanism_applicable"], "NO")
        self.assertEqual(self.payload["document_identity_single_mechanism"], "NOT_APPLICABLE")


class TestT4ProvenEquivalentRequiresAnchor(unittest.TestCase):
    def test_without_anchor_grade_is_not_established(self) -> None:
        equivalence = historical_pipeline_equivalence(anchor_available=False)
        self.assertEqual(equivalence["RELEVANT_PIPELINE_EQUIVALENCE"], "NOT_ESTABLISHED")
        # the byte-identity observation survives, but as supporting evidence only
        self.assertEqual(equivalence["supporting_observation_only_grade"], "PROVEN_EQUIVALENT")
        self.assertFalse(equivalence["supporting_observation_is_binding"])

    def test_with_anchor_the_observation_would_be_binding(self) -> None:
        equivalence = historical_pipeline_equivalence(anchor_available=True)
        self.assertEqual(equivalence["RELEVANT_PIPELINE_EQUIVALENCE"], "PROVEN_EQUIVALENT")


class TestT5NoAnchorMeansNotEstablished(V47ArtifactMixin, unittest.TestCase):
    def test_anchor_audit_and_grade(self) -> None:
        self.assertEqual(
            self.payload["historical_source_anchor"]["historical_source_anchor_available"], "NO"
        )
        self.assertEqual(self.payload["relevant_pipeline_equivalence"], "NOT_ESTABLISHED")

    def test_anchor_audit_is_mechanical(self) -> None:
        audit = dg.historical_source_anchor_audit()
        methods = audit["candidate_methods"]
        self.assertIn("publish_workspace_git", methods)
        self.assertIn("local_immutable_snapshot", methods)
        self.assertFalse(methods["production_hash_only"]["sufficient"])


class TestT6NotEstablishedCoexistsWithStronglySupported(V47ArtifactMixin, unittest.TestCase):
    def test_both_hold(self) -> None:
        self.assertEqual(self.payload["relevant_pipeline_equivalence"], "NOT_ESTABLISHED")
        self.assertEqual(self.payload["historical_failure_compatibility"], "STRONGLY_SUPPORTED")


class TestT7NoHistoricalOverclaim(V47ArtifactMixin, unittest.TestCase):
    def test_no_overturn_wording_in_artifact(self) -> None:
        lowered = self.payload_text.lower()
        for forbidden in (
            "mechanically_overturned",
            "mechanically overturned",
            "机械推翻",
            "exact historical request",
            "mechanically confirmed historical",
        ):
            self.assertNotIn(forbidden, lowered, forbidden)

    def test_historical_attribution_only_challenged(self) -> None:
        self.assertEqual(
            self.payload["historical_v4_6_document_identity_attribution"], "STRONGLY_CHALLENGED"
        )

    def test_no_confirmed_grade_without_anchor(self) -> None:
        self.assertNotEqual(self.payload["historical_failure_compatibility"], "CONFIRMED")


class TestT8MeasurementDoesNotAlterProductFamily(V47ArtifactMixin, unittest.TestCase):
    def test_per_case_families_uniform_despite_measurement_difference(self) -> None:
        per_case_measurement = self.payload["per_case_measurement_issue"]
        self.assertEqual(per_case_measurement["md-015"], "NOT_OBSERVED")
        self.assertEqual(per_case_measurement["md-004"], "SUPPORTED")
        for case_id in TARGET_CASES:
            self.assertEqual(
                self.payload["per_case_product_root_cause"][case_id]["family"], "GENERATION"
            )


class TestT9MechanismFieldConsistency(unittest.TestCase):
    def test_handshake_mapping(self) -> None:
        self.assertEqual(
            dg.handshake_mechanism_fields("YES"),
            {"SHARED_GENERATION_MECHANISM": "YES", "MIXED_PRODUCT_MECHANISMS": "NO"},
        )
        self.assertEqual(
            dg.handshake_mechanism_fields("NO"),
            {"SHARED_GENERATION_MECHANISM": "NO", "MIXED_PRODUCT_MECHANISMS": "YES"},
        )
        self.assertEqual(
            dg.handshake_mechanism_fields("NOT_ESTABLISHED"),
            {"SHARED_GENERATION_MECHANISM": "NOT_ESTABLISHED", "MIXED_PRODUCT_MECHANISMS": "NOT_ESTABLISHED"},
        )

    def test_artifact_combination_is_consistent(self) -> None:
        if not ARTIFACT.is_file():
            self.skipTest("artifact missing")
        payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        shared = payload["shared_generation_mechanism"]
        mixed = payload["mixed_product_mechanisms"]
        expected = {"YES": "NO", "NO": "YES", "NOT_ESTABLISHED": "NOT_ESTABLISHED"}[shared]
        self.assertEqual(mixed, expected)


class TestT10RawEvidencePreserved(V47ArtifactMixin, unittest.TestCase):
    def test_before_equals_after(self) -> None:
        preservation = self.payload["raw_evidence_preservation"]
        self.assertEqual(
            preservation["RAW_EVIDENCE_DIGEST_BEFORE"], preservation["RAW_EVIDENCE_DIGEST_AFTER"]
        )
        self.assertTrue(preservation["raw_evidence_preserved"])
        self.assertEqual(preservation["RAW_EVIDENCE_PRESERVATION"], "VERIFIED_BY_SEMANTIC_DIGEST")

    def test_digest_recomputes_from_the_artifact(self) -> None:
        preservation = self.payload["raw_evidence_preservation"]
        recomputed = dg.canonical_json_digest(dg.extract_raw_evidence(self.payload))
        self.assertEqual(recomputed, preservation["raw_evidence_digest_after"])

    def test_derived_fields_are_excluded_from_the_raw_subset(self) -> None:
        raw = dg.extract_raw_evidence(self.payload)
        for derived in (
            "per_case_product_root_cause",
            "per_case_generation_mechanisms",
            "layer_matrix",
            "closure_gate_results",
            "historical_source_anchor",
        ):
            self.assertNotIn(derived, raw)


class TestT11NoIdentityRemediationAuthorization(V47ArtifactMixin, unittest.TestCase):
    def test_authorizations_denied(self) -> None:
        self.assertEqual(self.payload["ready_for_document_identity_remediation"], "NO")
        self.assertEqual(self.payload["ready_for_minimal_document_identity_remediation"], "NO")
        self.assertEqual(self.payload["product_code_change_authorized"], "NO")


class TestT12NoNewProductBaseline(V47ArtifactMixin, unittest.TestCase):
    def test_no_new_baseline_artifact(self) -> None:
        self.assertFalse((ROOT / "eval" / "v4_7_document_identity_baseline.json").exists())
        lineage = pre_product_json("eval/v4_baseline_lineage.json")
        self.assertEqual(lineage["current_baseline_id"], "V4_6_2_HASH_PORTABILITY_BASELINE")


class TestV47ReplayEvidence(V47ArtifactMixin, unittest.TestCase):
    def test_title_visible_at_application_request_for_all_targets(self) -> None:
        for case_id in TARGET_CASES:
            replay = self.payload["per_case_layer_trace"][case_id]
            self.assertTrue(replay["title_visibility_at_application_request"])
            self.assertTrue(replay["material_header_contains_canonical_title"])
            self.assertTrue(replay["APPLICATION_LEVEL_REQUEST_CAPTURED"])
            self.assertFalse(replay["OLLAMA_RENDERED_TOKEN_PROMPT_CAPTURED"])

    def test_no_identity_loss_layer(self) -> None:
        for case_id in TARGET_CASES:
            matrix = self.payload["layer_matrix"][case_id]
            for layer in (
                "DB canonical title",
                "ChunkRecord document_title",
                "serialized material header title",
                "application request title",
            ):
                self.assertEqual(matrix[layer], "YES", f"{case_id}:{layer}")

    def test_title_absent_only_from_model_output(self) -> None:
        for case_id in TARGET_CASES:
            matrix = self.payload["layer_matrix"][case_id]
            self.assertEqual(matrix["raw answer title"], "NO")
            self.assertEqual(matrix["final answer title"], "NO")
            self.assertEqual(matrix["final answer uses 材料N"], "YES")

    def test_post_processing_does_not_touch_identity(self) -> None:
        for case_id in TARGET_CASES:
            replay = self.payload["per_case_layer_trace"][case_id]
            self.assertFalse(replay["raw_vs_final_answer"]["post_processing_changed_identity"])
        self.assertEqual(self.payload["post_processing_cause"], "EXCLUDED")

    def test_current_pipeline_finding(self) -> None:
        self.assertEqual(self.payload["current_pipeline_root_cause"], "GENERATION")
        self.assertEqual(self.payload["current_pipeline_document_identity_loss"], "DISPROVEN")
        self.assertEqual(self.payload["document_identity_root_cause"], "NOT_PROVEN")
        self.assertEqual(self.payload["application_request_title_visibility"], "YES_FOR_ALL_TARGETS")
        self.assertEqual(self.payload["evidence_continuity"], "PRESERVED_FOR_ALL_TARGETS")

    def test_evidence_continuity_preserved(self) -> None:
        for case_id in TARGET_CASES:
            self.assertTrue(
                self.payload["per_case_layer_conclusion"][case_id][
                    "target_documents_present_in_sent_materials"
                ]
            )

    def test_all_gates_pass(self) -> None:
        failed = [n for n, ok in self.payload["gate_results"].items() if not ok]
        self.assertEqual(failed, [], f"failed gates: {failed}")

    def test_all_closure_gates_pass(self) -> None:
        failed = [n for n, ok in self.payload["closure_gate_results"].items() if not ok]
        self.assertEqual(failed, [], f"failed closure gates: {failed}")

    def test_closure_gates_cover_the_required_set(self) -> None:
        expected = {f"C{i}" for i in range(1, 38)}
        actual = {name.split()[0] for name in self.payload["closure_gate_results"]}
        self.assertEqual(expected - actual, set())


class TestV47FrozenContractUntouched(unittest.TestCase):
    def test_golden_cases_hash_unchanged(self) -> None:
        baseline = json.loads(
            (ROOT / "eval" / "v4_6_2_hash_portability_baseline.json").read_text(encoding="utf-8")
        )
        self.assertEqual(dg.EVB._golden_cases_hash(), baseline["golden_identity"]["cases_sha256"])

    def test_golden_file_hash_unchanged(self) -> None:
        baseline = json.loads(
            (ROOT / "eval" / "v4_6_2_hash_portability_baseline.json").read_text(encoding="utf-8")
        )
        self.assertEqual(dg.EVB._golden_hash(), baseline["golden_identity"]["file_sha256"])

    def test_evaluator_version_unchanged(self) -> None:
        self.assertEqual(dg.EVB.EVALUATOR_VERSION, "v4-baseline-v1")

    def test_baseline_lineage_pointer_unchanged(self) -> None:
        lineage = pre_product_json("eval/v4_baseline_lineage.json")
        self.assertEqual(lineage["current_baseline_id"], "V4_6_2_HASH_PORTABILITY_BASELINE")

    def test_historical_artifacts_still_present(self) -> None:
        for name in (
            "v4_6_post_routing_attribution.json",
            "v4_6_post_routing_evidence.json",
            "v4_6_2_hash_portability_baseline.json",
            "v4_6_1_embedding_identity_baseline.json",
            "v4_baseline_lineage.json",
            "v3_final_golden.json",
        ):
            self.assertTrue((ROOT / "eval" / name).is_file(), name)

    def test_production_source_hash_unchanged(self) -> None:
        with pre_product_tree() as historical_root:
            self.assertEqual(dg.EVB.production_source_hash(historical_root), CANONICAL_PRODUCTION_HASH)


if __name__ == "__main__":
    unittest.main()
