"""WS-13 G2 observer tests: static / synthetic only (zero real calls).

Every test in this module runs without a model call, without an embedding call
and without a production retrieval.  The real-call boundaries of the canonical
pipeline (Ollama HTTP request, query embedding, answer-model chat, canonical
engine prepare/answer, library retrieval) are patched in ``setUpModule`` to
raise if any of them is touched, so an accidental real call fails loudly.

Test-only doubles are confined to this module: the observer's live path
contains no fake fallback, and no synthetic value produced here is ever
described as current cit-001 evidence.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import io
import json
import os
import re
import sys
import threading
import types
import unittest
import unittest.mock
from contextlib import ExitStack, closing, redirect_stderr, redirect_stdout
from pathlib import Path
from urllib.parse import urlsplit

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"
for _path in (str(ROOT_DIR), str(SCRIPTS_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import observe_v4_ws13_citation_fresh_attribution as O  # noqa: E402
from product_revision import pre_product_tree, public_analysis_tree  # noqa: E402
from publication_evidence import load_public_manifest  # noqa: E402

OBSERVER_PATH = SCRIPTS_DIR / "observe_v4_ws13_citation_fresh_attribution.py"
TEST_PATH = Path(__file__).resolve()
ACCEPTED_G1_BASE_ARTIFACT = ROOT_DIR / O.ACCEPTED_G1_BASE_PATH
ACCEPTED_G1_A001_ARTIFACT = ROOT_DIR / O.ACCEPTED_G1_A001_PATH
ACCEPTED_G1_A001_FC1_ARTIFACT = ROOT_DIR / O.ACCEPTED_G1_A001_FC1_PATH
G0_PREFLIGHT_ARTIFACT = ROOT_DIR / O.G0_PREFLIGHT_PATH

# --------------------------------------------------------------------------- #
# Real-call boundaries: patched in setUpModule, any touch raises loudly
# --------------------------------------------------------------------------- #
_REAL_CALL_ATTEMPTS: list[str] = []


def _forbidden_real_call(name: str):
    def _fail(*_args, **_kwargs):
        _REAL_CALL_ATTEMPTS.append(name)
        raise AssertionError("REAL CALL BOUNDARY TRIGGERED: " + name)

    return _fail


_ACTIVE_PATCHERS: list[unittest.mock._patch] = []
_HISTORICAL_REPLAY_STACK = None
_PRIVATE_RUNTIME_DB_AVAILABLE = True


def setUpModule() -> None:  # noqa: N802 (unittest API)
    global _HISTORICAL_REPLAY_STACK, _PRIVATE_RUNTIME_DB_AVAILABLE
    import core.engine_v2 as engine_v2
    import core.library_store as library_store
    import core.ollama_http as ollama_http
    import eval_v4_baseline as evaluator

    # These synthetic observer mechanics belong to the pre-product WS-13
    # protocol. Materialize its real old files and run the real hash functions
    # over them. Only the unchanged runtime database is read from the live
    # workspace, by its already frozen full-byte identity. No old producer's
    # default boundary is relaxed and no historical observation is rerun.
    stack = ExitStack()
    try:
        private_database = ROOT_DIR / O.RUNTIME_DB_RELATIVE_PATH
        _PRIVATE_RUNTIME_DB_AVAILABLE = private_database.is_file()
        actual_database = str(private_database)
        historical_root = stack.enter_context(
            public_analysis_tree() if load_public_manifest(ROOT_DIR) is not None
            else pre_product_tree(include_inputs=True)
        )
        if not _PRIVATE_RUNTIME_DB_AVAILABLE:
            # Public source distributions intentionally contain no private
            # library. Pure observer mechanics use a real temporary empty DB
            # and its actual bytes, under an explicitly synthetic binding.
            import sqlite3

            synthetic_database = historical_root / "data/library/synthetic_runtime_identity.sqlite3"
            synthetic_database.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(synthetic_database)) as connection:
                connection.execute("CREATE TABLE synthetic_test_identity (role TEXT)")
                connection.execute("INSERT INTO synthetic_test_identity VALUES (?)", (
                    "SYNTHETIC_TEST_ONLY_NOT_PRIVATE_LIBRARY_EVIDENCE",
                ))
                connection.commit()
            actual_database = str(synthetic_database)
            synthetic_bytes = synthetic_database.read_bytes()
            synthetic_expected_sha256 = hashlib.sha256(synthetic_bytes).hexdigest()
            synthetic_expected_identity = "%d:%s" % (
                len(synthetic_bytes), synthetic_expected_sha256[:16],
            )
        stack.enter_context(unittest.mock.patch.object(O, "ROOT_DIR", historical_root))
        stack.enter_context(unittest.mock.patch.object(
            O, "RUNTIME_DB_RELATIVE_PATH", actual_database,
        ))
        stack.enter_context(unittest.mock.patch.object(evaluator, "ROOT_DIR", historical_root))
        stack.enter_context(unittest.mock.patch(__name__ + ".ROOT_DIR", historical_root))
        if not _PRIVATE_RUNTIME_DB_AVAILABLE:
            actual_role_a = O.recompute_role_a_identities

            def synthetic_runtime_role_a(current_master_binding=None):
                # The production implementation still hashes real fixture bytes
                # and reports the original private G1 mismatch. Only this test
                # double supplies a synthetic expected binding for mechanics;
                # original G1 files and frozen constants remain unchanged.
                report = actual_role_a(current_master_binding)
                runtime = report["ROLE_A_IDENTITIES"]["runtime_db_identity"]
                reference_keys = (
                    "accepted_identity", "accepted_full_sha256",
                    "g1_frozen_identity", "g1_frozen_full_sha256",
                )
                runtime["PRIVATE_FROZEN_REFERENCE_NOT_REPLAYED"] = {
                    key: runtime[key] for key in reference_keys
                }
                for key in ("accepted_identity", "g1_frozen_identity"):
                    runtime[key] = synthetic_expected_identity
                for key in ("accepted_full_sha256", "g1_frozen_full_sha256"):
                    runtime[key] = synthetic_expected_sha256
                runtime["EXPECTED_BINDING_ROLE"] = "SYNTHETIC_TEST_ONLY_ACTUAL_TEMPORARY_DATABASE"
                runtime["MATCH"] = O._role_a_matches("runtime_db_identity", runtime)
                report["ROLE_A_ALL_MATCH"] = all(
                    value["MATCH"] for value in report["ROLE_A_IDENTITIES"].values()
                )
                report["ROLE_A_COMPARISON_MODE"] = (
                    "SYNTHETIC_RUNTIME_BINDING_NOT_PRIVATE_G1_REPLAY__"
                    + report["ROLE_A_COMPARISON_MODE"]
                )
                return report

            stack.enter_context(unittest.mock.patch.object(
                O, "recompute_role_a_identities", synthetic_runtime_role_a,
            ))
    except BaseException:
        stack.close()
        raise
    _HISTORICAL_REPLAY_STACK = stack

    targets = [
        (ollama_http.OllamaClient, "_request", "OllamaClient._request"),
        (ollama_http.OllamaClient, "embed", "OllamaClient.embed"),
        (ollama_http.OllamaClient, "chat", "OllamaClient.chat"),
        (ollama_http.OllamaClient, "chat_stream", "OllamaClient.chat_stream"),
        (library_store.LibraryStore, "retrieve", "LibraryStore.retrieve"),
        (engine_v2.StructuredQAEngine, "prepare", "StructuredQAEngine.prepare"),
        (engine_v2.StructuredQAEngine, "answer", "StructuredQAEngine.answer"),
    ]
    for owner, attribute, label in targets:
        patcher = unittest.mock.patch.object(
            owner, attribute, _forbidden_real_call(label)
        )
        patcher.start()
        _ACTIVE_PATCHERS.append(patcher)


def tearDownModule() -> None:  # noqa: N802 (unittest API)
    global _HISTORICAL_REPLAY_STACK
    while _ACTIVE_PATCHERS:
        _ACTIVE_PATCHERS.pop().stop()
    if _HISTORICAL_REPLAY_STACK is not None:
        _HISTORICAL_REPLAY_STACK.close()
        _HISTORICAL_REPLAY_STACK = None


# --------------------------------------------------------------------------- #
# AST / static scan helpers
# --------------------------------------------------------------------------- #
def _observer_tree() -> ast.Module:
    return ast.parse(OBSERVER_PATH.read_text(encoding="utf-8"))


def _test_tree() -> ast.Module:
    return ast.parse(TEST_PATH.read_text(encoding="utf-8"))


def _call_nodes(tree: ast.AST) -> list[ast.Call]:
    return [node for node in ast.walk(tree) if isinstance(node, ast.Call)]


def _callable_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return (prefix + "." + node.attr) if prefix else node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


FORBIDDEN_WRITER_ATTRIBUTES = frozenset(
    {
        "write",
        "write_text",
        "write_bytes",
        "writelines",
        "touch",
        "mkdir",
        "makedirs",
        "unlink",
        "rmdir",
        "rename",
        "remove",
        "rmtree",
        "copy",
        "copy2",
        "copyfile",
        "copytree",
        "move",
        "chmod",
        "symlink",
        "link",
        "truncate",
    }
)
FORBIDDEN_WRITER_FUNCTIONS = frozenset(
    {"dump", "putenv", "setenv", "system", "popen", "run", "call", "check_call"}
)
FORBIDDEN_WRITE_MODES = frozenset(
    {"w", "wb", "wt", "a", "ab", "at", "x", "xb", "xt", "r+", "rb+", "w+", "a+"}
)
FORBIDDEN_MODULES = frozenset({"sqlite3", "shutil", "tempfile", "subprocess", "pickle"})
FORBIDDEN_CLASSIFIER_TOKENS = (
    "CURRENT_CONFIRMED_CITATION_DEFECT",
    "NO_CURRENT_CITATION_DEFECT_ESTABLISHED",
    "STALE_ATTRIBUTION_REQUIRES_REFRESH",
    "RESOLVED_OR_CLOSED",
    "CITATION_DEFECT_MECHANICALLY_ESTABLISHED",
    "ATTRIBUTION_FRESHNESS",
    "CURRENT_UNRESOLVED_ISSUE_ESTABLISHED",
    "LATEST_PRODUCT_STATE_COMPATIBLE",
    "READINESS_CLASS",
    "NEXT_PERMISSIBLE_ACTION",
    "SEPARATE_EXECUTION",
    "FRESH_ATTRIBUTION",
    "EVIDENCE_RECONCILIATION",
    "DEFER_PENDING_UPSTREAM",
    "NO_SUPPORTED_ACTION",
    "CITATION_STATUS",
    "GENERATION_CONFOUND",
    "RETRIEVAL_CONFOUND",
    "MEASUREMENT_CONFOUND",
    "CITATION_SPECIFIC_FAILURE",
    "SUPPORTING_EVIDENCE_PRESENT",
    "CLAIM_PRESENT",
    "CITATION_EXPECTED",
    "CITATION_EMITTED",
    "CITATION_TARGET_VALID",
    "CITATION_ALIGNMENT_VALID",
    "INVALID_CITATION_PRESENT",
    "SCOPE_VIOLATION_PRESENT",
    "RUN_VARIABILITY",
    "DETERMINATE_ALL_RUNS_AGREE",
    "NOT_ESTABLISHED_DUE_TO_VARIABILITY",
    "NOT_ESTABLISHED_DUE_TO_INCOMPLETE_RUN",
    "NOT_ESTABLISHED_DUE_TO_MISSING_EVIDENCE",
    "NOT_ESTABLISHED_DUE_TO_CONFOUND",
)


def _writer_violations(tree: ast.AST) -> list[str]:
    """Mechanical scan for any governed-workspace writer path."""
    violations: list[str] = []
    for node in _call_nodes(tree):
        name = _callable_name(node.func)
        dotted = _dotted_name(node.func)
        if name in FORBIDDEN_WRITER_ATTRIBUTES:
            violations.append("writer call: " + dotted)
        if name in FORBIDDEN_WRITER_FUNCTIONS:
            violations.append("writer call: " + dotted)
        if name == "open":
            modes = [
                argument.value
                for argument in list(node.args)[1:2]
                if isinstance(argument, ast.Constant)
            ]
            modes.extend(
                keyword.value
                for keyword in node.keywords
                if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant)
            )
            for mode in modes:
                if str(mode) in FORBIDDEN_WRITE_MODES:
                    violations.append("open() with write mode: " + str(mode))
                elif str(mode) not in ("r", "rb", "rt", "rU"):
                    violations.append("open() with unexpected mode: " + str(mode))
            if not modes:
                violations.append("open() without an explicit read-only mode")
        if name in ("dump",) and dotted.endswith("json.dump"):
            violations.append("json.dump to file: " + dotted)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in FORBIDDEN_MODULES:
                    violations.append("forbidden import: " + alias.name)
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in FORBIDDEN_MODULES:
                violations.append("forbidden import: " + str(node.module))
    return violations


def _attribute_assignment_violations(tree: ast.AST) -> list[str]:
    """No attribute assignment anywhere plus no os.environ subscript write."""
    violations: list[str] = []
    for node in ast.walk(tree):
        targets: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            targets = [node.target]
        for target in targets:
            if isinstance(target, ast.Attribute):
                violations.append(
                    "attribute assignment: " + _dotted_name(target)
                )
            if isinstance(target, ast.Subscript):
                base = _dotted_name(target.value)
                if base.endswith("environ") or base.endswith("sys.modules"):
                    violations.append(
                        "environment/module subscript assignment: " + base
                    )
    return violations


NON_STREAM_WRITE_CALLABLE_NAMES = frozenset({"write_telemetry"})


def _stdout_contract_violations(tree: ast.AST) -> list[str]:
    violations: list[str] = []
    for node in _call_nodes(tree):
        name = _callable_name(node.func)
        if name in NON_STREAM_WRITE_CALLABLE_NAMES:
            # The canonical governed telemetry append is a canonical operation
            # (G2_EQ4 FIX_3), never an observer stream write.
            continue
        if name.startswith("write") or name == "writelines":
            violations.append("direct stream write: " + _dotted_name(node.func))
        if name == "print":
            for keyword in node.keywords:
                if keyword.arg == "file":
                    target = _dotted_name(keyword.value)
                    if target not in ("sys.stdout", "sys.stderr"):
                        violations.append("print to non-std stream: " + target)
        if name == "add_argument":
            for argument in node.args:
                if isinstance(argument, ast.Constant) and isinstance(
                    argument.value, str
                ):
                    if re.match(r"^--(out|output|write|log|artifact)", argument.value):
                        violations.append(
                            "output-file option declared: " + argument.value
                        )
    return violations


def _reads_only_input_sources(tree: ast.AST) -> bool:
    return not _writer_violations(tree) and not _attribute_assignment_violations(tree)


# --------------------------------------------------------------------------- #
# Test-only synthetic canonical-shaped doubles (never real cit-001 evidence)
# --------------------------------------------------------------------------- #
SYNTHETIC_SYSTEM_MESSAGE = "SYNTHETIC_TEST_ONLY_SYSTEM_PROMPT"
SYNTHETIC_TASK_HINT = "直接回答概念、原理、条件或工程作用。"
SYNTHETIC_QUERY = O.CANONICAL_QUERY
SYNTHETIC_CHUNK_ID = "synthetic-test-only-chunk-1"
SYNTHETIC_DOCUMENT_ID = "synthetic-test-only-document-1"
SYNTHETIC_LOCATION = "SYNTHETIC-TEST-ONLY · PDF 第1页"
SYNTHETIC_EVIDENCE_TEXT = "  GSM 使用 GMSK 调制。  \n\n  第二行  "
SYNTHETIC_RAW_ANSWER = " GSM 使用 GMSK 调制[1]。附加结论[9]。 "
SYNTHETIC_CLASSIFIER_SHA256 = "0" * 63 + "1"
SYNTHETIC_FUTURE_TESTS_SHA256 = "0" * 63 + "2"
SYNTHETIC_G4_AUTHORIZATION = "SYNTHETIC_TEST_ONLY_G4_AUTHORIZATION"
SYNTHETIC_G4_SIDE_EFFECT_POLICY = "SYNTHETIC_TEST_ONLY_RESOLVED_POLICY"
# G2_EQ4 FIX_3 test-only invocation-time accepted-rule identity.  The rule bytes
# live in memory only (no workspace file is created), its source bindings are
# recomputed read-only from the current workspace, and its immutable-surface
# baseline is served by the test-only in-memory manifest provider.  These values
# are synthetic test fixtures: they are never current cit-001 evidence and they
# never make a rule governance-accepted.
SYNTHETIC_ACCEPTED_RULE_PATH = "eval/SYNTHETIC_TEST_ONLY_FUTURE_ACCEPTED_RULE.json"
SYNTHETIC_ACCEPTED_RULE_MANIFEST_DIGEST = "9" * 64
SYNTHETIC_ACCEPTED_RULE_MANIFEST_ENTRY_COUNT = 7
SYNTHETIC_ACCEPTED_RULE_SCOPE_FINGERPRINT = "SYNTHETIC_TEST_ONLY_SCOPE_FINGERPRINT"
# Boundaries of the accepted rules whose exact identities must never be pinned
# inside the observer production source (Phase A static identity report inputs).
ACCEPTED_TPR1_RULE_RELATIVE_PATH = "eval/v4_ws13_canonical_telemetry_permission_rule.json"
ACCEPTED_TPR1_RULE_RAW_SHA256 = (
    "16075fedf3bb8424d6df6562fe902f8d52509b9b9009b80b30a8ee8e26550f8f"
)
ACCEPTED_TPR1_RULE_SEMANTIC_DIGEST = (
    "4231856b8a66b7d31970fb3795e1cc8041c052e92e80a963b20c38ab1efa4f81"
)
ACCEPTED_TPR1_RULE_EXCLUDED_PATHS = (
    "data/logs/qa_log.jsonl",
    "eval/v4_ws13_canonical_telemetry_permission_rule.json",
)
SYNTHETIC_RULE_BOUND_SOURCES = (
    "core/engine_v2.py",
    "core/config.py",
    "scripts/eval_v4_baseline.py",
    "scripts/observe_v4_ws13_citation_fresh_attribution.py",
    "tests/test_v4_ws13_citation_fresh_attribution.py",
)


def _raw_sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _synthetic_accepted_rule_object() -> dict:
    """A synthetic future accepted rule (test-only; never governance-accepted)."""
    files = {
        Path(relative_path).stem: relative_path
        + "|"
        + _raw_sha256_file(ROOT_DIR / relative_path)
        for relative_path in SYNTHETIC_RULE_BOUND_SOURCES
    }
    rule = {
        "schema_version": "1.0",
        "short_id": "SYNTHETIC_TEST_ONLY_FUTURE_ACCEPTED_RULE",
        "permission_rule": {
            "authorized_telemetry_operation_multiplicity": (
                O.AUTHORIZED_TELEMETRY_OPERATION_MULTIPLICITY
            ),
            "authorized_successful_append_delta": (
                O.AUTHORIZED_SUCCESSFUL_APPEND_DELTA
            ),
            "canonical_telemetry_io_failure_propagates": "NO",
            "telemetry_append_success_required_for_run_acceptance": "NO",
        },
        "measurement_contract": {
            "measurement_contract_change": "NO",
            "telemetry_operation_remains_inside_measured_interval": "YES",
        },
        "filesystem_scope": {
            "authorized_mutable_path": "data/logs/qa_log.jsonl",
            "authorized_mutation_type": "APPEND_ONLY",
        },
        "runtime_configuration": {
            "telemetry_enabled": "TRUE",
            "telemetry_suppression": "NONE",
            "telemetry_redirection": "NONE",
        },
        "source_bindings": {"files": files},
        "immutable_surface_binding": {
            "baseline_digest": SYNTHETIC_ACCEPTED_RULE_MANIFEST_DIGEST,
            "baseline_entry_count": SYNTHETIC_ACCEPTED_RULE_MANIFEST_ENTRY_COUNT,
            "excluded_paths": [],
        },
    }
    # Positive synthetic runs use an explicit current navigation binding;
    # default/static G1 comparison remains strict about the historical Master.
    master_sha = _raw_sha256_file(ROOT_DIR / O.FROZEN_MASTER_PATH)
    if master_sha != O.FROZEN_MASTER_SHA256:
        archive_path = "tests/fixtures/ws13_20261014/pre_stage_sources.zip"
        archive_sha = _raw_sha256_file(ROOT_DIR / archive_path)
        rule["current_state_binding"] = {
            "mode": O.CURRENT_MASTER_NAVIGATION_MODE,
            "path": O.FROZEN_MASTER_PATH,
            "current_raw_sha256": master_sha,
            "g1_frozen_raw_sha256": O.FROZEN_MASTER_SHA256,
            "preserved_effective_ws13_design_digest": O.OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST,
            "historical_master": {
                "archive_path": archive_path,
                "archive_sha256": archive_sha,
                "member": O.FROZEN_MASTER_PATH,
                "raw_sha256": O.FROZEN_MASTER_SHA256,
            },
        }
        rule["telemetry_validation_boundary"] = dict(O.CURRENT_TELEMETRY_VALIDATION_BOUNDARY)
        for role, relative_path in (
            ("current_master", O.FROZEN_MASTER_PATH),
            ("historical_master_archive", archive_path),
            ("classifier", "scripts/classify_v4_ws13_citation_fresh_attribution.py"),
            ("future_tests", "tests/test_ws13_classifier.py"),
        ):
            files[role] = relative_path + "|" + _raw_sha256_file(ROOT_DIR / relative_path)
    return rule


def _synthetic_rule_bytes() -> bytes:
    return json.dumps(
        _synthetic_accepted_rule_object(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _synthetic_rule_identity() -> tuple[str, str, str]:
    rule = _synthetic_accepted_rule_object()
    return (
        SYNTHETIC_ACCEPTED_RULE_PATH,
        hashlib.sha256(_synthetic_rule_bytes()).hexdigest(),
        O.rule_semantic_digest(rule),
    )


def _in_memory_rule_reader(_path: Path) -> bytes:
    """Test-only read-only rule source: the synthetic rule bytes, from memory."""
    return _synthetic_rule_bytes()


def _in_memory_manifest_provider(paths) -> dict:  # noqa: ANN001
    """Test-only in-memory manifest provider for the synthetic rule baseline."""
    return {
        "RULE": O.WORKSPACE_MANIFEST_RULE,
        "ENTRY_COUNT": SYNTHETIC_ACCEPTED_RULE_MANIFEST_ENTRY_COUNT,
        "DIGEST": SYNTHETIC_ACCEPTED_RULE_MANIFEST_DIGEST,
        "EXCLUDED_PATHS": sorted(str(path) for path in paths),
    }


def _synthetic_report(answer: str, sent_count: int) -> dict:
    numbers = [
        int(match.group(1))
        for match in re.finditer(r"\[(-?\d+)\](?![A-Za-z])", answer)
    ]
    invalid = [n for n in numbers if n < 1 or n > sent_count]
    valid = sorted({n for n in numbers if 1 <= n <= sent_count})
    supports = ["SUPPORTED" for _ in valid] or ["UNCERTAIN"]
    return {
        "verifier_version": O.FROZEN_CITATION_VERIFIER_VERSION,
        "citation_count": len(valid),
        "factual_claim_count": len(supports),
        "cited_claim_count": len(valid),
        "citation_coverage": 1.0,
        "supported_claim_count": len(supports),
        "unsupported_claim_count": 0,
        "uncertain_claim_count": 0,
        "invalid_citation_count": len(invalid),
        "citation_scope_violation": 0,
        "verifications": [
            {
                "claim_index": index,
                "support": support,
                "reason_codes": ["supported_key_terms"],
                "missing_key_terms": [],
                "mismatched_numbers": [],
            }
            for index, support in enumerate(supports)
        ],
    }


class SyntheticChunk:
    """Synthetic canonical-shaped chunk identity (test-only)."""

    def __init__(
        self,
        chunk_id: str = SYNTHETIC_CHUNK_ID,
        document_id: str = SYNTHETIC_DOCUMENT_ID,
        text: str = SYNTHETIC_EVIDENCE_TEXT,
        location: str = SYNTHETIC_LOCATION,
        chapter: str = "SYNTHETIC_CHAPTER",
        section: str = "SYNTHETIC_SECTION",
    ) -> None:
        self.id = chunk_id
        self.document_id = document_id
        self.text = text
        self.location = location
        self.chapter = chapter
        self.section = section

    def citation(self, number: int) -> dict:
        return {
            "id": number,
            "chunk_id": self.id,
            "document_id": self.document_id,
            "location": self.location,
        }


class SyntheticDecision:
    def __init__(
        self,
        route: str = O.CANONICAL_SUPPORTED_ROUTE,
        scope_conflict: bool = False,
        resolution_status: str = "none",
    ) -> None:
        self.route = route
        self.confidence = "medium"
        self.reason_code = "DEFAULT_QA"
        self.original_question = SYNTHETIC_QUERY
        self.normalized_question = SYNTHETIC_QUERY
        self.resolution_status = resolution_status
        self.referent = ""
        self.follow_up = False
        self.scope_conflict = scope_conflict


class SyntheticResolution:
    def __init__(self) -> None:
        self.document_ids = frozenset({SYNTHETIC_DOCUMENT_ID})
        self.mode = "default"
        self.requested = None
        self.note = "SYNTHETIC_TEST_ONLY_RESOLUTION"


class SyntheticPrepared:
    def __init__(
        self,
        contexts: list | None = None,
        route: str = O.CANONICAL_SUPPORTED_ROUTE,
        chapters: list | None = None,
        out_of_scope: bool = False,
        decision: SyntheticDecision | None = None,
    ) -> None:
        self.question = SYNTHETIC_QUERY
        self.route = route
        self.contexts = [SyntheticChunk()] if contexts is None else contexts
        self.retrieval_mode = "hybrid"
        self.confidence = "medium"
        self.out_of_scope = out_of_scope
        self.chapters = [] if chapters is None else chapters
        self.decision = SyntheticDecision(route=route) if decision is None else decision


class SyntheticLibrary:
    def __init__(self) -> None:
        self.has_vectors = True
        self.documents = [types.SimpleNamespace(id=SYNTHETIC_DOCUMENT_ID)]
        self.embedding_model = O.FROZEN_EMBEDDING_MODEL
        self.dimension = O.FROZEN_EMBEDDING_DIMENSION
        self.resolve_scope_calls = 0

    def resolve_scope(self, scope):  # noqa: ANN001
        self.resolve_scope_calls += 1
        return SyntheticResolution()

    def effective_allowed_ids(self, resolution):  # noqa: ANN001
        return None


class SyntheticResult:
    def __init__(self, answer: str, citations: list, citation_report, verified) -> None:  # noqa: ANN001
        self.answer = answer
        self.citations = citations
        self.sources = [item.get("location", "") for item in citations]
        self.route = O.CANONICAL_SUPPORTED_ROUTE
        self.retrieval_mode = "hybrid"
        self.confidence = "medium"
        self.out_of_scope = False
        self.citation_verified = verified
        self.elapsed_ms = 0
        self.history_entry = None
        self.citation_report = citation_report


class SyntheticVerifier:
    VERSION = O.FROZEN_CITATION_VERIFIER_VERSION

    def __init__(self, recorder: dict) -> None:
        self.recorder = recorder

    def verify(self, answer: str, evidence_texts: dict, *, citation_count=None):  # noqa: ANN001
        self.recorder["verify_calls"].append(
            {
                "answer": answer,
                "evidence_text_keys": sorted(evidence_texts),
                "citation_count": citation_count,
            }
        )
        sent_count = citation_count if citation_count is not None else 0
        report = _synthetic_report(answer, sent_count)
        return types.SimpleNamespace(to_dict=lambda: report)


class SyntheticEngineV2:
    """Synthetic canonical-shaped engine_v2 module (test-only)."""

    def __init__(self, recorder: dict) -> None:
        self.recorder = recorder

    def normalize_history(self, history):  # noqa: ANN001
        """Canonical-shaped history normalization (None -> empty list)."""
        self.recorder["normalize_history_calls"].append(
            {"history": history}
        )
        return [] if not history else list(history)

    def build_messages(self, question, contexts, route, history):  # noqa: ANN001
        self.recorder["build_messages_calls"].append(
            {
                "question": question,
                "context_count": len(contexts),
                "route": route,
                "history": history,
            }
        )
        blocks = []
        for index, chunk in enumerate(contexts, 1):
            body = re.sub(r"\s+", " ", chunk.text).strip()
            blocks.append("[材料%d｜%s]\n%s" % (index, chunk.location, body))
        user = (
            "任务要求："
            + SYNTHETIC_TASK_HINT
            + "\n\n"
            + "\n\n".join(blocks)
            + "\n\n问题："
            + question
        )
        messages = [
            {"role": "system", "content": SYNTHETIC_SYSTEM_MESSAGE},
            {"role": "user", "content": user},
        ]
        self.recorder["sent_contexts"] = list(contexts)
        return messages, list(contexts)

    def normalize_citations(self, answer: str, citation_count: int):  # noqa: ANN001
        self.recorder["normalize_citations_calls"].append(
            {"answer": answer, "citation_count": citation_count}
        )
        cleaned = answer.strip()
        cited = [
            int(match.group(1))
            for match in re.finditer(r"\[(\d+)\](?![A-Za-z])", cleaned)
        ]
        invalid = [n for n in cited if n < 1 or n > citation_count]
        if invalid:
            cleaned = re.sub(
                r"\[(\d+)\](?![A-Za-z])",
                lambda match: (
                    match.group(0)
                    if 1 <= int(match.group(1)) <= citation_count
                    else ""
                ),
                cleaned,
            )
        valid = [n for n in cited if 1 <= n <= citation_count]
        return cleaned, bool(valid) and not invalid

    def citation_support_verified(self, answer, contexts, chapters):  # noqa: ANN001
        self.recorder["citation_support_verified_calls"].append(
            {"answer": answer, "context_count": len(contexts)}
        )
        return True

    def scope_fingerprint(self, resolution):  # noqa: ANN001
        """Canonical-shaped scope fingerprint (test-only, read-only)."""
        self.recorder["scope_fingerprint_calls"].append(
            {"mode": getattr(resolution, "mode", None),
             "after_canonical_measurement": bool(self.recorder["evaluator_rows"])}
        )
        return SYNTHETIC_ACCEPTED_RULE_SCOPE_FINGERPRINT

    def write_telemetry(self, record):  # noqa: ANN001
        """Synthetic canonical-shaped telemetry recorder (test-only).

        The observer mirrors exactly one canonical ``write_telemetry``
        invocation inside its measured interval; this double records that
        invocation in memory, models at most one successful append and performs
        no filesystem write.  The synthetic IO-failure branch is provided by a
        separate double.
        """
        self.recorder["telemetry_calls"].append(copy.deepcopy(record))
        self.recorder.setdefault("telemetry_append_results", []).append(True)

    def renumber_citations(self, answer: str, citations: list):  # noqa: ANN001
        self.recorder["renumber_citations_calls"].append(
            {"answer": answer, "citation_ids": [item["id"] for item in citations]}
        )
        by_id = {int(item["id"]): item for item in citations}
        mapping: dict[int, int] = {}

        def replace(match: re.Match) -> str:
            old = int(match.group(1))
            if old not in mapping and old in by_id:
                mapping[old] = len(mapping) + 1
            return "[%d]" % mapping[old] if old in mapping else ""

        text = re.sub(r"\[(\d+)\](?![A-Za-z])", replace, answer)
        used = []
        for old, new in sorted(mapping.items(), key=lambda item: item[1]):
            item = dict(by_id[old])
            item["id"] = new
            used.append(item)
        return text, used


class SyntheticCitationVerifierModule:
    CITATION_VERIFIER_VERSION = O.FROZEN_CITATION_VERIFIER_VERSION

    @staticmethod
    def citation_numbers(answer: str) -> list[int]:
        return [
            int(match.group(1))
            for match in re.finditer(r"\[(-?\d+)\](?![A-Za-z])", str(answer or ""))
        ]

    @staticmethod
    def valid_citation_ids(answer: str, citation_count: int, present_ids=None):  # noqa: ANN001
        valid: list[int] = []
        invalid: list[int] = []
        for number in SyntheticCitationVerifierModule.citation_numbers(answer):
            if number < 1 or number > citation_count:
                invalid.append(number)
                continue
            if present_ids is not None and number not in present_ids:
                invalid.append(number)
                continue
            if number not in valid:
                valid.append(number)
        return valid, invalid


class SyntheticEvaluator:
    EVALUATOR_VERSION = O.FROZEN_EVALUATOR_VERSION

    def __init__(self, recorder: dict) -> None:
        self.recorder = recorder

    def _build_row(self, case: dict, result, elapsed_ms: int) -> dict:  # noqa: ANN001
        facts = case.get("expected_answer_facts") or []
        answer = result.answer or ""
        present = [fact for fact in facts if fact in answer]
        missing = [fact for fact in facts if fact not in answer]
        row = {
            "id": case["id"],
            "category": case["category"],
            "elapsed_ms": elapsed_ms,
            "fact_present": len(present),
            "fact_total": len(facts),
            "missing_facts": missing,
            "answer_state": "ANSWERED",
            "refused": False,
            "out_of_scope": bool(result.out_of_scope),
            "raw_answer": answer,
            "citation_report": result.citation_report,
            "citation_verified": result.citation_verified,
            "evaluator_version": self.EVALUATOR_VERSION,
            "citation_verifier_version": SyntheticCitationVerifierModule.CITATION_VERIFIER_VERSION,
        }
        self.recorder["evaluator_rows"].append(row)
        return row


class SyntheticConfig:
    ANSWER_NUM_PREDICT = 800
    ANSWER_CONTEXT_WINDOW = 8192


class SyntheticEngine:
    def __init__(self, recorder: dict, prepared: SyntheticPrepared | None = None) -> None:
        self.recorder = recorder
        self.library = SyntheticLibrary()
        # Canonical-shaped answer-model client surface: the canonical
        # ``OllamaClient`` exposes ``chat`` (core/ollama_http.py), so the
        # synthetic client mirrors that attribute and the mirrored canonical
        # non-streaming branch predicate selects the canonical chat branch.  The
        # generation itself goes through the bound canonical ``resolved.chat``
        # seam, never through this attribute.
        self.ollama = types.SimpleNamespace(
            name="SYNTHETIC_TEST_ONLY_OLLAMA_CLIENT",
            chat=lambda *_args, **_kwargs: "SYNTHETIC_TEST_ONLY_UNUSED",
        )
        self.answer_model = O.FROZEN_ANSWER_MODEL
        self.citation_verifier = SyntheticVerifier(recorder)
        self.prepared = prepared if prepared is not None else SyntheticPrepared()
        self.result = None
        # Canonical-shaped instance state the mirrored canonical operations read
        # (core/engine_v2.py#StructuredQAEngine.__init__): the per-engine model
        # lock and the last-retrieval/telemetry timing attributes.
        self._model_lock = threading.Lock()
        self._last_embedding_ms = None
        self._last_retrieval_timings: dict = {}

    def prepare(self, question, history, scope):  # noqa: ANN001
        self.recorder["prepare_calls"].append(
            {"question": question, "history": history, "scope": scope}
        )
        return self.prepared

    def _assert_citations_in_scope(self, citations, resolution, known):  # noqa: ANN001
        self.recorder["scope_assertion_calls"].append(
            {
                "citation_ids": [item["id"] for item in citations],
                "resolution_mode": getattr(resolution, "mode", None),
                "known_document_count": len(known),
            }
        )

    def _result(
        self,
        answer,
        citations,
        prepared,
        started,
        citation_verified,
        citation_report=None,
    ):  # noqa: ANN001
        # Canonical-shaped consumer semantics: core/engine_v2.py
        # #StructuredQAEngine._result computes
        # `elapsed_ms=round((time.perf_counter() - started) * 1000)` from the
        # engine-result timer it is handed.  The synthetic double mirrors that
        # exactly so the tests can prove which timer reaches the consumer.
        elapsed_ms = round((O.time.perf_counter() - started) * 1000)
        self.recorder["result_calls"].append(
            {
                "answer": answer,
                "citation_ids": [item["id"] for item in citations],
                "citation_verified": citation_verified,
                "citation_report": citation_report,
                "engine_timer_started": started,
                "engine_result_elapsed_ms": elapsed_ms,
            }
        )
        self.result = SyntheticResult(
            answer, citations, citation_report, citation_verified
        )
        self.result.elapsed_ms = elapsed_ms
        return self.result


class SyntheticBindings:
    __slots__ = ("record", "bindings", "engine_holder")

    def __init__(
        self,
        prepared: SyntheticPrepared | None = None,
        raw_answer: str = SYNTHETIC_RAW_ANSWER,
        clock=None,  # noqa: ANN001 - test-only deterministic perf_counter
        engine_v2=None,  # noqa: ANN001 - optional synthetic engine_v2 double
    ) -> None:
        self.record: dict = {
            "normalize_history_calls": [],
            "prepare_calls": [],
            "build_messages_calls": [],
            "normalize_citations_calls": [],
            "citation_support_verified_calls": [],
            "renumber_citations_calls": [],
            "scope_assertion_calls": [],
            "result_calls": [],
            "verify_calls": [],
            "evaluator_rows": [],
            "chat_calls": [],
            "engine_constructions": [],
            "engine_construction_clock_call_counts": [],
            "sent_contexts": [],
            "telemetry_calls": [],
            "scope_fingerprint_calls": [],
        }
        if engine_v2 is None:
            engine_v2 = SyntheticEngineV2(self.record)
        self.engine_holder: dict = {}

        def engine_factory(path):  # noqa: ANN001
            self.record["engine_constructions"].append(str(path))
            if clock is not None:
                # Number of canonical timer reads already performed when the
                # engine object is constructed: 0 proves no canonical timer
                # covers the construction.
                self.record["engine_construction_clock_call_counts"].append(
                    len(clock.calls)
                )
            engine = SyntheticEngine(self.record, prepared)
            self.engine_holder["engine"] = engine
            return engine

        def chat(client, messages, model):  # noqa: ANN001
            """Canonical-shaped NON-STREAMING synthetic chat (test-only).

            Returns the padded synthetic raw text verbatim so the observer's raw
            answer capture can be proven to be a direct passthrough of the
            canonical non-streaming return value.
            """
            self.record["chat_calls"].append(
                {
                    "client": client,
                    "messages": messages,
                    "model": model,
                    "kwargs": None,
                }
            )
            return raw_answer

        self.bindings = O.CanonicalBindings(
            engine_factory=engine_factory,
            engine_v2=engine_v2,
            citation_verifier=SyntheticCitationVerifierModule,
            evaluator=SyntheticEvaluator(self.record),
            config=SyntheticConfig,
            library_store=types.SimpleNamespace(),
            query_scope=types.SimpleNamespace(),
            chat=chat,
            rule_identity_reader=_in_memory_rule_reader,
            rule_identity_manifest_provider=_in_memory_manifest_provider,
        )


class SentinelBindings:
    """Bindings whose every real-call boundary raises if reached."""

    def __init__(self) -> None:
        self.reached: list[str] = []

        def _raise(name: str):
            def _inner(*_args, **_kwargs):
                self.reached.append(name)
                raise AssertionError("real-call boundary reached: " + name)

            return _inner

        self.bindings = O.CanonicalBindings(
            engine_factory=_raise("engine_factory"),
            engine_v2=types.SimpleNamespace(
                normalize_history=_raise("normalize_history"),
                build_messages=_raise("build_messages"),
                normalize_citations=_raise("normalize_citations"),
                citation_support_verified=_raise("citation_support_verified"),
                renumber_citations=_raise("renumber_citations"),
                scope_fingerprint=_raise("scope_fingerprint"),
                write_telemetry=_raise("write_telemetry"),
            ),
            citation_verifier=types.SimpleNamespace(
                CITATION_VERIFIER_VERSION=O.FROZEN_CITATION_VERIFIER_VERSION,
                citation_numbers=_raise("citation_numbers"),
                valid_citation_ids=_raise("valid_citation_ids"),
            ),
            evaluator=types.SimpleNamespace(
                EVALUATOR_VERSION=O.FROZEN_EVALUATOR_VERSION,
                _build_row=_raise("_build_row"),
            ),
            config=types.SimpleNamespace(
                ANSWER_NUM_PREDICT=0, ANSWER_CONTEXT_WINDOW=0
            ),
            library_store=types.SimpleNamespace(),
            query_scope=types.SimpleNamespace(),
            chat=_raise("chat"),
        )


def live_request(**overrides) -> O.LiveObservationRequest:  # noqa: ANN003
    rule_path, rule_raw_sha, rule_digest = _synthetic_rule_identity()
    bound_rule = _synthetic_accepted_rule_object()
    files = bound_rule["source_bindings"]["files"]
    values = {
        "case_id": O.CANONICAL_GOLDEN_CASE_ID,
        "run_ordinal": 1,
        "g4_authorization": SYNTHETIC_G4_AUTHORIZATION,
        "g4_side_effect_policy": SYNTHETIC_G4_SIDE_EFFECT_POLICY,
        "effective_ws13_design_digest": O.OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST,
        "accepted_g1_base_sha256": O.ACCEPTED_G1_BASE_SHA256,
        "accepted_g1_a001_sha256": O.ACCEPTED_G1_A001_SHA256,
        "accepted_g1_a001_fc1_sha256": O.ACCEPTED_G1_A001_FC1_SHA256,
        "expected_observer_sha256": O.observer_file_raw_sha256(),
        "classifier_sha256": (
            files["classifier"].split("|")[1]
            if "current_state_binding" in bound_rule else SYNTHETIC_CLASSIFIER_SHA256
        ),
        "tests_sha256": (
            files["future_tests"].split("|")[1]
            if "current_state_binding" in bound_rule else SYNTHETIC_FUTURE_TESTS_SHA256
        ),
        "run_id": "SYNTHETIC_TEST_ONLY_RUN_ID",
        "observation_timestamp": "SYNTHETIC_TEST_ONLY_TIMESTAMP",
        "accepted_rule_relative_path": rule_path,
        "accepted_rule_raw_sha256": rule_raw_sha,
        "accepted_rule_semantic_digest": rule_digest,
    }
    values.update(overrides)
    return O.LiveObservationRequest(**values)


def run_synthetic(**overrides) -> tuple[dict, SyntheticBindings]:
    harness = SyntheticBindings(overrides.pop("prepared", None))
    payload = O.run_live_observation(live_request(**overrides), harness.bindings)
    return payload, harness


def run_blocked(**overrides) -> dict:
    sentinel = SentinelBindings()
    payload = O.run_live_observation(live_request(**overrides), sentinel.bindings)
    if sentinel.reached:  # pragma: no cover - a guard leak fails loudly
        raise AssertionError(
            "blocked request reached real-call boundaries: %s" % sentinel.reached
        )
    return payload


_PAYLOAD_CACHE: dict = {}


def base_payload() -> dict:
    if "payload" not in _PAYLOAD_CACHE:
        payload, harness = run_synthetic()
        _PAYLOAD_CACHE["payload"] = payload
        _PAYLOAD_CACHE["harness"] = harness
    return _PAYLOAD_CACHE["payload"]


def base_payload_entry() -> tuple[dict, "SyntheticBindings"]:
    base_payload()
    return _PAYLOAD_CACHE["payload"], _PAYLOAD_CACHE["harness"]


def base_payload_for_validation() -> dict:
    return copy.deepcopy(base_payload())


def _base_observation() -> dict:
    return base_payload_for_validation()["OBSERVATION"]


def accepted_schema_groups() -> dict:
    base = json.loads(ACCEPTED_G1_BASE_ARTIFACT.read_text(encoding="utf-8"))
    return base["design_semantic_payload"]["observation_schema"]["field_groups"]


def accepted_base_semantic_keys() -> list[str]:
    base = json.loads(ACCEPTED_G1_BASE_ARTIFACT.read_text(encoding="utf-8"))
    return list(
        base["design_semantic_payload"]["semantic_vs_provenance_field_contract"][
            "OBSERVATION_SEMANTIC_KEY_SET"
        ]
    )


def a001_evidence_key_change() -> dict:
    amendment = json.loads(ACCEPTED_G1_A001_ARTIFACT.read_text(encoding="utf-8"))
    return amendment["amendment_semantic_payload"][
        "fix_4_canonical_sent_evidence_representation"
    ]["FROZEN_RULE"]["OBSERVATION_SEMANTIC_KEY_SET_CHANGE"]


def effective_semantic_keys_from_artifacts() -> list[str]:
    change = a001_evidence_key_change()
    keys: list[str] = []
    for key in accepted_base_semantic_keys():
        if key in change["REMOVE"]:
            keys.extend(change["ADD"])
        else:
            keys.append(key)
    return keys


def effective_group_fields_from_artifacts() -> dict:
    """The effective group field map derived mechanically from base + A001.

    The A001 ADD entries are *key-set* keys of the frozen record shape
    (``retrieval.sent_evidence_records[].<sub-field>``); the corresponding
    record field is therefore the single field ``sent_evidence_records``, which
    replaces the superseded ambiguous single-value field in place.
    """
    change = a001_evidence_key_change()
    added_names: list[str] = []
    for key in change["ADD"]:
        # "retrieval.sent_evidence_records[].<sub-field>" -> "sent_evidence_records"
        name = key.split(".")[-2].split("[")[0]
        if name not in added_names:
            added_names.append(name)
    result: dict[str, list[str]] = {}
    for group, fields in accepted_schema_groups().items():
        names: list[str] = []
        for name in fields:
            if (group + "." + name) in change["REMOVE"]:
                names.extend(added_names)
            else:
                names.append(name)
        result[group] = names
    return result


# --------------------------------------------------------------------------- #
# 01 accepted G1-chain SHA / digest bindings
# --------------------------------------------------------------------------- #
class G2AcceptedChainBindingTest(unittest.TestCase):
    def test_g0_preflight_raw_sha256_matches_the_accepted_identity(self) -> None:
        self.assertEqual(
            hashlib.sha256(G0_PREFLIGHT_ARTIFACT.read_bytes()).hexdigest(),
            O.G0_PREFLIGHT_SHA256,
        )

    def test_accepted_g1_base_raw_sha256_matches(self) -> None:
        self.assertEqual(
            hashlib.sha256(ACCEPTED_G1_BASE_ARTIFACT.read_bytes()).hexdigest(),
            O.ACCEPTED_G1_BASE_SHA256,
        )

    def test_accepted_g1_a001_raw_sha256_matches(self) -> None:
        self.assertEqual(
            hashlib.sha256(ACCEPTED_G1_A001_ARTIFACT.read_bytes()).hexdigest(),
            O.ACCEPTED_G1_A001_SHA256,
        )

    def test_accepted_g1_a001_fc1_raw_sha256_matches(self) -> None:
        self.assertEqual(
            hashlib.sha256(ACCEPTED_G1_A001_FC1_ARTIFACT.read_bytes()).hexdigest(),
            O.ACCEPTED_G1_A001_FC1_SHA256,
        )

    def test_base_design_semantic_payload_digest_recomputes(self) -> None:
        base = json.loads(ACCEPTED_G1_BASE_ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(
            O.canonical_digest(base["design_semantic_payload"]),
            O.BASE_EFFECTIVE_DESIGN_DIGEST,
        )

    def test_amendment_semantic_payload_digest_recomputes(self) -> None:
        amendment = json.loads(
            ACCEPTED_G1_A001_ARTIFACT.read_text(encoding="utf-8")
        )
        self.assertEqual(
            O.canonical_digest(amendment["amendment_semantic_payload"]),
            amendment["amendment_semantic_digest"],
        )

    def test_effective_design_chain_digest_recomputes_to_the_operative_value(
        self,
    ) -> None:
        amendment = json.loads(
            ACCEPTED_G1_A001_ARTIFACT.read_text(encoding="utf-8")
        )
        self.assertEqual(
            O.canonical_digest(amendment["effective_design_chain_payload"]),
            O.OPERATIVE_EFFECTIVE_WS13_DESIGN_DIGEST,
        )

    def test_fc1_boundary_correction_payload_digest_recomputes(self) -> None:
        correction = json.loads(
            ACCEPTED_G1_A001_FC1_ARTIFACT.read_text(encoding="utf-8")
        )
        self.assertEqual(
            O.canonical_digest(correction["boundary_correction_payload"]),
            correction["boundary_correction_digest"],
        )

    def test_observer_chain_recomputation_reports_every_check_matching(self) -> None:
        chain = O.recompute_accepted_g1_chain()
        self.assertTrue(chain["ACCEPTED_G1_CHAIN_VALID"])
        self.assertTrue(chain["BASE_DESIGN_DIGEST_RECOMPUTE_MATCH"])
        self.assertTrue(chain["AMENDMENT_DIGEST_RECOMPUTE_MATCH"])
        self.assertTrue(chain["EFFECTIVE_DESIGN_CHAIN_DIGEST_RECOMPUTE_MATCH"])
        self.assertTrue(chain["FC1_BOUNDARY_DIGEST_RECOMPUTE_MATCH"])

    def test_validate_bindings_mode_reports_valid(self) -> None:
        if not _PRIVATE_RUNTIME_DB_AVAILABLE:
            self.skipTest("exact frozen runtime-library identity requires private database; public mechanics use a synthetic binding")
        payload = O.validate_bindings()
        historical_master_is_live = (
            _raw_sha256_file(ROOT_DIR / O.FROZEN_MASTER_PATH) == O.FROZEN_MASTER_SHA256
        )
        self.assertEqual(payload["BINDINGS_VALID"], historical_master_is_live)
        self.assertTrue(payload["ACCEPTED_G1_CHAIN"]["ACCEPTED_G1_CHAIN_VALID"])
        self.assertEqual(payload["ROLE_A"]["ROLE_A_ALL_MATCH"], historical_master_is_live)
        for name, value in payload["ROLE_A"]["ROLE_A_IDENTITIES"].items():
            self.assertEqual(value["MATCH"], historical_master_is_live if name == "master_identity" else True)
        self.assertTrue(payload["SOURCE_BINDING_MAP"]["COMPLETE"])
        self.assertEqual(payload["MODEL_CALLS"], 0)


# --------------------------------------------------------------------------- #
# 02 target allowlist
# --------------------------------------------------------------------------- #
class G2TargetAllowlistTest(unittest.TestCase):
    def test_primary_target_case_ids_is_the_frozen_singleton(self) -> None:
        self.assertEqual(O.PRIMARY_TARGET_CASE_IDS, ("cit-001",))

    def test_guard_accepts_the_frozen_primary_target(self) -> None:
        # G2_EQ4 FIX_3: a live guard evaluation now also validates the
        # invocation-time accepted-rule identity, so the test-only in-memory
        # rule source and manifest provider are supplied here.
        guards = O.evaluate_live_guards(
            live_request(), _in_memory_rule_reader, _in_memory_manifest_provider
        )
        checks = {item["CHECK"]: item["PASS"] for item in guards["CHECKS"]}
        self.assertTrue(checks["TARGET_CASE_ALLOWLIST"])
        self.assertTrue(checks["FUTURE_G4_ACCEPTED_RULE_IDENTITY_VALIDATED"])
        self.assertTrue(guards["LIVE_GUARDS_PASSED"])
        if not _PRIVATE_RUNTIME_DB_AVAILABLE:
            runtime = guards["ROLE_A"]["ROLE_A_IDENTITIES"]["runtime_db_identity"]
            actual = hashlib.sha256(Path(O.RUNTIME_DB_RELATIVE_PATH).read_bytes()).hexdigest()
            self.assertEqual(runtime["live_full_sha256"], actual)
            self.assertNotEqual(actual, O.FROZEN_RUNTIME_DB_FULL_SHA256)
            self.assertEqual(runtime["accepted_full_sha256"], actual)
            self.assertEqual(runtime["EXPECTED_BINDING_ROLE"], "SYNTHETIC_TEST_ONLY_ACTUAL_TEMPORARY_DATABASE")
            self.assertEqual(runtime["PRIVATE_FROZEN_REFERENCE_NOT_REPLAYED"]["accepted_full_sha256"],
                             O.FROZEN_RUNTIME_DB_FULL_SHA256)
            fixture = Path(O.RUNTIME_DB_RELATIVE_PATH)
            original_bytes = fixture.read_bytes()
            try:
                fixture.write_bytes(original_bytes + b"synthetic identity drift")
                drift = O.recompute_role_a_identities()
                changed_runtime = drift["ROLE_A_IDENTITIES"]["runtime_db_identity"]
                self.assertFalse(changed_runtime["MATCH"])
                self.assertFalse(drift["ROLE_A_ALL_MATCH"])
                self.assertNotEqual(changed_runtime["live_full_sha256"], actual)
                self.assertEqual(changed_runtime["accepted_full_sha256"], actual)
                self.assertEqual(changed_runtime["g1_frozen_full_sha256"], actual)
            finally:
                fixture.write_bytes(original_bytes)
            self.assertTrue(O.recompute_role_a_identities()["ROLE_A_IDENTITIES"]["runtime_db_identity"]["MATCH"])

    def test_live_guard_rejects_a_non_allowlisted_case_with_zero_calls(self) -> None:
        payload = run_blocked(case_id="cit-002")
        self.assertEqual(payload["STATUS"], "BLOCKED_BEFORE_INVOCATION")
        self.assertFalse(payload["LIVE_GUARDS_PASSED"])
        self.assertEqual(payload["TARGET_OBSERVATION_RUNS"], 0)
        checks = {item["CHECK"]: item["PASS"] for item in payload["LIVE_GUARD_CHECKS"]}
        self.assertFalse(checks["TARGET_CASE_ALLOWLIST"])


# --------------------------------------------------------------------------- #
# 03 control denylist
# --------------------------------------------------------------------------- #
class G2ControlDenylistTest(unittest.TestCase):
    def test_control_case_ids_is_empty(self) -> None:
        self.assertEqual(O.CONTROL_CASE_IDS, ())

    def test_guard_evaluates_the_control_denylist_for_the_target(self) -> None:
        guards = O.evaluate_live_guards(live_request())
        checks = {item["CHECK"]: item["PASS"] for item in guards["CHECKS"]}
        self.assertTrue(checks["CONTROL_CASE_DENYLIST"])

    def test_live_guard_rejects_any_control_case_with_zero_calls(self) -> None:
        payload = run_blocked(case_id="SYNTHETIC_TEST_ONLY_CONTROL_CASE")
        self.assertEqual(payload["STATUS"], "BLOCKED_BEFORE_INVOCATION")
        self.assertEqual(payload["MODEL_CALLS"], 0)
        checks = {item["CHECK"]: item["PASS"] for item in payload["LIVE_GUARD_CHECKS"]}
        self.assertFalse(checks["TARGET_CASE_ALLOWLIST"])


# --------------------------------------------------------------------------- #
# 04 run ordinal allowlist
# --------------------------------------------------------------------------- #
class G2RunOrdinalAllowlistTest(unittest.TestCase):
    def test_run_ordinals_are_the_frozen_triple(self) -> None:
        self.assertEqual(O.RUN_ORDINALS, (1, 2, 3))
        self.assertEqual(O.RUN_MULTIPLICITY, 3)

    def test_guard_allows_every_authorized_ordinal(self) -> None:
        for ordinal in O.RUN_ORDINALS:
            with self.subTest(ordinal=ordinal):
                guards = O.evaluate_live_guards(live_request(run_ordinal=ordinal))
                checks = {
                    item["CHECK"]: item["PASS"] for item in guards["CHECKS"]
                }
                self.assertTrue(checks["RUN_ORDINAL_ALLOWLIST"])

    def test_live_guard_rejects_ordinals_outside_the_allowlist(self) -> None:
        for ordinal in (0, 4, -1, 99):
            with self.subTest(ordinal=ordinal):
                payload = run_blocked(run_ordinal=ordinal)
                self.assertEqual(payload["STATUS"], "BLOCKED_BEFORE_INVOCATION")
                checks = {
                    item["CHECK"]: item["PASS"]
                    for item in payload["LIVE_GUARD_CHECKS"]
                }
                self.assertFalse(checks["RUN_ORDINAL_ALLOWLIST"])
                self.assertEqual(payload["PRODUCTION_RETRIEVAL_RUNS"], 0)
                self.assertEqual(payload["EMBEDDING_CALLS"], 0)
                self.assertEqual(payload["MODEL_CALLS"], 0)


# --------------------------------------------------------------------------- #
# 05 static / schema mode zero-call
# --------------------------------------------------------------------------- #
class G2StaticModeZeroCallTest(unittest.TestCase):
    def test_describe_contract_is_static_and_authorizes_no_live_execution(
        self,
    ) -> None:
        payload = O.describe_contract()
        self.assertEqual(payload["MODE"], "STATIC_CONTRACT")
        self.assertEqual(payload["checkpoint"], O.CHECKPOINT)
        self.assertEqual(payload["observer_role"], "RAW_OBSERVATION_ONLY")
        self.assertEqual(payload["primary_target_case_ids"], ["cit-001"])
        self.assertEqual(payload["control_case_ids"], [])
        self.assertEqual(payload["run_ordinals"], [1, 2, 3])
        self.assertEqual(payload["observation_equivalence_required"], "YES")
        self.assertEqual(payload["observer_self_write_free"], "YES")
        self.assertEqual(payload["live_execution_authorized_in_g2"], "NO")
        self.assertEqual(payload["stdout_only"], "YES")
        self.assertEqual(payload["MODEL_CALLS"], 0)
        self.assertEqual(payload["EMBEDDING_CALLS"], 0)
        self.assertEqual(payload["PRODUCTION_RETRIEVAL_RUNS"], 0)
        self.assertEqual(payload["TARGET_OBSERVATION_RUNS"], 0)
        self.assertEqual(
            payload["static_schema_self_check"]["ISSUES"],
            [],
        )

    def test_validate_bindings_is_static_and_reports_zero_calls(self) -> None:
        payload = O.validate_bindings()
        self.assertEqual(payload["MODE"], "STATIC_BINDINGS_VALIDATION")
        self.assertEqual(payload["MODEL_CALLS"], 0)
        self.assertEqual(payload["EMBEDDING_CALLS"], 0)
        self.assertEqual(payload["PRODUCTION_RETRIEVAL_RUNS"], 0)
        self.assertEqual(payload["TARGET_OBSERVATION_RUNS"], 0)
        self.assertEqual(payload["counters"]["FULL_144_RUNS"], 0)

    def test_cli_static_modes_emit_json_on_stdout(self) -> None:
        for arguments in (["--describe-contract"], ["--validate-bindings"]):
            with self.subTest(arguments=arguments):
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    code = O.main(arguments)
                self.assertEqual(code, 0 if arguments == ["--describe-contract"] else 3)
                parsed = json.loads(buffer.getvalue())
                self.assertEqual(parsed["MODE"].split("_")[0], "STATIC")
                if arguments == ["--validate-bindings"]:
                    self.assertFalse(parsed["BINDINGS_VALID"])
                    mismatches = [
                        name for name, value in parsed["ROLE_A"]["ROLE_A_IDENTITIES"].items()
                        if not value["MATCH"]
                    ]
                    self.assertEqual(mismatches, ["master_identity"])

    def test_static_modes_never_trigger_a_real_call_boundary(self) -> None:
        O.describe_contract()
        O.validate_bindings()
        self.assertEqual(_REAL_CALL_ATTEMPTS, [])

    def test_validate_observation_mode_is_static_and_zero_call(self) -> None:
        payload = base_payload_for_validation()
        result = O.validate_observation_payload(payload)
        self.assertTrue(result["VALID"])
        self.assertEqual(result["MODEL_CALLS"], 0)
        self.assertEqual(result["TARGET_OBSERVATION_RUNS"], 0)


# --------------------------------------------------------------------------- #
# 06 missing G4 authorization zero-call fail
# --------------------------------------------------------------------------- #
class G2G4AuthorizationGuardTest(unittest.TestCase):
    def test_live_without_g4_authorization_blocks_with_zero_calls(self) -> None:
        payload = run_blocked(g4_authorization="")
        self.assertEqual(payload["STATUS"], "BLOCKED_BEFORE_INVOCATION")
        self.assertEqual(payload["REJECTION_CLASS"], "BLOCKED_BEFORE_ANY_REAL_CALL")
        self.assertEqual(payload["MODEL_CALLS"], 0)
        self.assertEqual(payload["EMBEDDING_CALLS"], 0)
        self.assertEqual(payload["PRODUCTION_RETRIEVAL_RUNS"], 0)
        self.assertEqual(payload["TARGET_OBSERVATION_RUNS"], 0)
        self.assertIsNone(payload["OBSERVATION"])
        self.assertIsNone(payload["OBSERVATION_SEMANTIC_DIGEST"])
        checks = {item["CHECK"]: item["PASS"] for item in payload["LIVE_GUARD_CHECKS"]}
        self.assertFalse(checks["G4_EXPLICIT_AUTHORIZATION_MARKER"])

    def test_blank_g4_authorization_blocks_with_zero_calls(self) -> None:
        payload = run_blocked(g4_authorization="   ")
        self.assertEqual(payload["STATUS"], "BLOCKED_BEFORE_INVOCATION")
        self.assertEqual(payload["MODEL_CALLS"], 0)

    def test_g4_authorization_absent_skips_every_deep_check(self) -> None:
        payload = run_blocked(g4_authorization="")
        checks = {item["CHECK"]: item["PASS"] for item in payload["LIVE_GUARD_CHECKS"]}
        self.assertNotIn("ACCEPTED_G1_CHAIN_RECOMPUTATION", checks)
        self.assertNotIn("ROLE_A_STATE_IDENTITIES", checks)


# --------------------------------------------------------------------------- #
# 07 missing external binding zero-call fail
# --------------------------------------------------------------------------- #
class G2ExternalBindingGuardTest(unittest.TestCase):
    def test_missing_observer_sha256_blocks_with_zero_calls(self) -> None:
        payload = run_blocked(expected_observer_sha256="")
        self.assertEqual(payload["STATUS"], "BLOCKED_BEFORE_INVOCATION")
        self.assertEqual(payload["MODEL_CALLS"], 0)
        checks = {item["CHECK"]: item["PASS"] for item in payload["LIVE_GUARD_CHECKS"]}
        self.assertFalse(checks["BINDING_FORMAT_EXPECTED_OBSERVER_SHA256"])

    def test_mismatching_observer_sha256_blocks_with_zero_calls(self) -> None:
        payload = run_blocked(expected_observer_sha256="9" * 64)
        self.assertEqual(payload["STATUS"], "BLOCKED_BEFORE_INVOCATION")
        checks = {item["CHECK"]: item["PASS"] for item in payload["LIVE_GUARD_CHECKS"]}
        self.assertFalse(checks["OBSERVER_SHA_EXTERNAL_BINDING"])
        self.assertEqual(payload["PRODUCTION_RETRIEVAL_RUNS"], 0)

    def test_missing_classifier_sha256_blocks_with_zero_calls(self) -> None:
        payload = run_blocked(classifier_sha256="")
        self.assertEqual(payload["STATUS"], "BLOCKED_BEFORE_INVOCATION")
        checks = {item["CHECK"]: item["PASS"] for item in payload["LIVE_GUARD_CHECKS"]}
        self.assertFalse(checks["BINDING_FORMAT_CLASSIFIER_SHA256"])
        self.assertEqual(payload["MODEL_CALLS"], 0)

    def test_missing_future_tests_sha256_blocks_with_zero_calls(self) -> None:
        payload = run_blocked(tests_sha256="")
        self.assertEqual(payload["STATUS"], "BLOCKED_BEFORE_INVOCATION")
        checks = {item["CHECK"]: item["PASS"] for item in payload["LIVE_GUARD_CHECKS"]}
        self.assertFalse(checks["BINDING_FORMAT_TESTS_SHA256"])
        self.assertEqual(payload["MODEL_CALLS"], 0)

    def test_missing_effective_design_digest_blocks_with_zero_calls(self) -> None:
        payload = run_blocked(effective_ws13_design_digest="")
        self.assertEqual(payload["STATUS"], "BLOCKED_BEFORE_INVOCATION")
        self.assertEqual(payload["MODEL_CALLS"], 0)

    def test_mismatching_effective_design_digest_blocks_with_zero_calls(self) -> None:
        payload = run_blocked(effective_ws13_design_digest="a" * 64)
        self.assertEqual(payload["STATUS"], "BLOCKED_BEFORE_INVOCATION")
        checks = {item["CHECK"]: item["PASS"] for item in payload["LIVE_GUARD_CHECKS"]}
        self.assertFalse(checks["BINDING_EFFECTIVE_DESIGN_DIGEST"])
        self.assertEqual(payload["EMBEDDING_CALLS"], 0)

    def test_mismatching_accepted_g1_chain_sha256_blocks_with_zero_calls(self) -> None:
        payload = run_blocked(accepted_g1_base_sha256="b" * 64)
        self.assertEqual(payload["STATUS"], "BLOCKED_BEFORE_INVOCATION")
        checks = {item["CHECK"]: item["PASS"] for item in payload["LIVE_GUARD_CHECKS"]}
        self.assertFalse(checks["BINDING_ACCEPTED_G1_BASE_SHA256"])
        self.assertEqual(payload["TARGET_OBSERVATION_RUNS"], 0)

    def test_every_blocked_payload_reports_all_counters_zero(self) -> None:
        blocked_overrides = (
            {"expected_observer_sha256": ""},
            {"classifier_sha256": ""},
            {"tests_sha256": ""},
            {"effective_ws13_design_digest": ""},
            {"accepted_g1_base_sha256": ""},
            {"accepted_g1_a001_sha256": ""},
            {"accepted_g1_a001_fc1_sha256": ""},
            {"g4_authorization": ""},
            {"g4_side_effect_policy": ""},
        )
        for overrides in blocked_overrides:
            with self.subTest(overrides=sorted(overrides)):
                payload = run_blocked(**overrides)
                for field_name in O.COUNTER_FIELDS:
                    self.assertEqual(payload["COUNTERS"][field_name], 0)
                self.assertEqual(payload["MODEL_CALLS"], 0)
                self.assertEqual(payload["EMBEDDING_CALLS"], 0)
                self.assertEqual(payload["PRODUCTION_RETRIEVAL_RUNS"], 0)
                self.assertEqual(payload["TARGET_OBSERVATION_RUNS"], 0)


# --------------------------------------------------------------------------- #
# 08 required observation groups / fields
# --------------------------------------------------------------------------- #
class G2ObservationSchemaTest(unittest.TestCase):
    def test_group_order_equals_the_accepted_g1_schema(self) -> None:
        self.assertEqual(
            list(O.FIELD_GROUP_ORDER), list(accepted_schema_groups().keys())
        )
        self.assertEqual(len(O.FIELD_GROUP_ORDER), 10)

    def test_group_field_map_equals_the_effective_superseded_schema(self) -> None:
        expected = effective_group_fields_from_artifacts()
        for group, names in expected.items():
            with self.subTest(group=group):
                self.assertEqual(list(O.GROUP_FIELDS[group]), names)

    def test_field_contract_metadata_equals_the_accepted_g1_schema(self) -> None:
        groups = accepted_schema_groups()
        change = a001_evidence_key_change()

        def normalized(entry: dict) -> tuple:
            # The artifact carries the frozen vocabulary token plus an optional
            # parenthetical explanation; the contract stores the token itself.
            return (
                entry["capture_phase"],
                entry["semantic_role"],
                str(entry["missing_field_behavior"]).split(" ")[0],
            )

        removed_metadata = None
        removed_name = ""
        for group, fields in groups.items():
            for name, entry in fields.items():
                if (group + "." + name) in change["REMOVE"]:
                    removed_metadata = normalized(entry)
                    removed_name = name
                    continue
                with self.subTest(field=name):
                    self.assertEqual(O.FIELD_CONTRACT[name], normalized(entry))
        self.assertIsNotNone(removed_metadata)
        self.assertEqual(removed_name, "sent_evidence_text_or_governed_content_hash")
        with self.subTest(added_field=O.SENT_EVIDENCE_RECORDS_KEY):
            self.assertEqual(
                O.FIELD_CONTRACT[O.SENT_EVIDENCE_RECORDS_KEY], removed_metadata
            )
        self.assertNotIn(removed_name, O.FIELD_CONTRACT)
        self.assertEqual(
            tuple(O.SENT_EVIDENCE_RECORD_SHAPE),
            tuple(
                key.split("[].")[-1] for key in change["ADD"]
            ),
        )

    def test_field_entry_key_order_is_the_frozen_order(self) -> None:
        self.assertEqual(
            list(O.FIELD_ENTRY_KEY_ORDER),
            ["source", "capture_phase", "semantic_role", "missing_field_behavior"],
        )

    def test_observation_record_carries_exactly_the_frozen_groups(self) -> None:
        observation = _base_observation()
        for group in O.FIELD_GROUP_ORDER:
            self.assertIn(group, observation)
        expected_keys = set(O.FIELD_GROUP_ORDER) | {
            "observation_schema_version",
            O.PROVENANCE_ONLY_BLOCK_KEY,
        }
        self.assertEqual(set(observation), expected_keys)

    def test_every_frozen_field_is_present_in_a_synthetic_observation(self) -> None:
        observation = _base_observation()
        for group in O.FIELD_GROUP_ORDER:
            for name in O.GROUP_FIELDS[group]:
                with self.subTest(field=group + "." + name):
                    self.assertIn(name, observation[group])

    def test_observation_schema_version_is_the_frozen_version(self) -> None:
        observation = _base_observation()
        self.assertEqual(
            observation["observation_schema_version"],
            "v4-ws13-citation-fresh-attribution-observation-schema-v1",
        )


# --------------------------------------------------------------------------- #
# 09 semantic / provenance separation
# --------------------------------------------------------------------------- #
class G2SemanticProvenanceSeparationTest(unittest.TestCase):
    def test_effective_semantic_key_set_equals_the_artifact_derived_62(self) -> None:
        expected = effective_semantic_keys_from_artifacts()
        self.assertEqual(list(O.OBSERVATION_SEMANTIC_KEY_SET), expected)
        self.assertEqual(len(expected), 62)

    def test_base_and_effective_key_counts_match_the_amendment_declaration(
        self,
    ) -> None:
        change = a001_evidence_key_change()
        self.assertEqual(len(accepted_base_semantic_keys()), 60)
        self.assertEqual(change["OBSERVATION_SEMANTIC_KEY_COUNT_BEFORE"], 60)
        self.assertEqual(change["OBSERVATION_SEMANTIC_KEY_COUNT_EFFECTIVE"], 62)
        self.assertEqual(change["OTHER_OBSERVATION_KEYS_UNCHANGED"], "YES")

    def test_provenance_key_set_equals_the_frozen_eight(self) -> None:
        base = json.loads(ACCEPTED_G1_BASE_ARTIFACT.read_text(encoding="utf-8"))
        artifact_keys = base["design_semantic_payload"][
            "semantic_vs_provenance_field_contract"
        ]["OBSERVATION_PROVENANCE_ONLY_KEY_SET"]
        self.assertEqual(list(O.OBSERVATION_PROVENANCE_ONLY_KEY_SET), artifact_keys)
        self.assertEqual(len(artifact_keys), 8)

    def test_semantic_and_provenance_sets_are_disjoint(self) -> None:
        self.assertEqual(
            set(O.OBSERVATION_SEMANTIC_KEY_SET)
            & set(O.OBSERVATION_PROVENANCE_ONLY_KEY_SET),
            set(),
        )

    def test_removed_ambiguous_key_is_absent_and_the_three_new_keys_present(
        self,
    ) -> None:
        self.assertNotIn(
            O.REMOVED_AMBIGUOUS_EVIDENCE_KEY, O.OBSERVATION_SEMANTIC_KEY_SET
        )
        for key in (
            "retrieval.sent_evidence_records[].sent_context_id",
            "retrieval.sent_evidence_records[].sent_evidence_text",
            "retrieval.sent_evidence_records[].sent_evidence_content_sha256",
        ):
            self.assertIn(key, O.OBSERVATION_SEMANTIC_KEY_SET)
        self.assertEqual(
            set(O.SENT_EVIDENCE_KEYS),
            {
                "retrieval.sent_evidence_records[].sent_context_id",
                "retrieval.sent_evidence_records[].sent_evidence_text",
                "retrieval.sent_evidence_records[].sent_evidence_content_sha256",
            },
        )

    def test_digest_payload_keys_equal_the_frozen_semantic_key_set(self) -> None:
        payload = O.select_observation_semantic_payload(_base_observation())
        self.assertEqual(set(payload), set(O.OBSERVATION_SEMANTIC_KEY_SET))
        self.assertEqual(len(payload), 62)

    def test_provenance_only_keys_never_enter_the_semantic_payload(self) -> None:
        payload = O.select_observation_semantic_payload(_base_observation())
        for key in O.OBSERVATION_PROVENANCE_ONLY_KEY_SET:
            self.assertNotIn(key, payload)
        self.assertNotIn("run_identity.run_id", payload)
        self.assertNotIn("run_identity.observation_timestamp", payload)

    def test_run_ordinal_is_semantic_while_run_id_is_provenance(self) -> None:
        self.assertIn("run_identity.run_ordinal", O.OBSERVATION_SEMANTIC_KEY_SET)
        self.assertIn("run_identity.run_id", O.OBSERVATION_PROVENANCE_ONLY_KEY_SET)
        self.assertEqual(
            O.FIELD_CONTRACT["run_ordinal"][1], "SEMANTIC_EXECUTION_POSITION"
        )
        self.assertEqual(O.FIELD_CONTRACT["run_id"][1], "PROVENANCE_ONLY")

    def test_provenance_block_carries_only_the_bare_provenance_fields(self) -> None:
        observation = _base_observation()
        block = observation[O.PROVENANCE_ONLY_BLOCK_KEY]
        self.assertEqual(set(block), set(O.PROVENANCE_ONLY_BLOCK_FIELDS))
        for name in O.PROVENANCE_ONLY_BLOCK_FIELDS:
            self.assertIn(name, O.OBSERVATION_PROVENANCE_ONLY_KEY_SET)


# --------------------------------------------------------------------------- #
# 10 sent evidence text + hash contract
# --------------------------------------------------------------------------- #
def synthetic_record(
    text: str = "SYNTHETIC_TEST_ONLY_EVIDENCE",
    sha256: str | None = None,
    context_id: str = SYNTHETIC_CHUNK_ID,
) -> dict:
    return {
        "sent_context_id": context_id,
        "sent_evidence_text": text,
        "sent_evidence_content_sha256": (
            O.exact_text_sha256(text) if sha256 is None else sha256
        ),
    }


class G2SentEvidenceContractTest(unittest.TestCase):
    def test_correct_text_and_hash_pair_is_accepted(self) -> None:
        result = O.validate_sent_evidence_records([synthetic_record()])
        self.assertTrue(result["VALID"])
        self.assertEqual(result["RECORD_COUNT"], 1)
        self.assertEqual(result["ORDERING"], O.SENT_EVIDENCE_ORDER_RULE)

    def test_text_only_record_is_rejected(self) -> None:
        result = O.validate_sent_evidence_records(
            [synthetic_record(sha256="")]
        )
        self.assertFalse(result["VALID"])
        self.assertTrue(
            any("sha256" in issue for issue in result["ISSUES"]), result["ISSUES"]
        )

    def test_hash_only_record_is_rejected(self) -> None:
        record = synthetic_record(text="")
        result = O.validate_sent_evidence_records([record])
        self.assertFalse(result["VALID"])
        self.assertTrue(
            any("hash-only" in issue for issue in result["ISSUES"]), result["ISSUES"]
        )

    def test_hash_mismatch_is_rejected(self) -> None:
        result = O.validate_sent_evidence_records(
            [synthetic_record(sha256="0" * 64)]
        )
        self.assertFalse(result["VALID"])
        self.assertTrue(
            any("mismatch" in issue for issue in result["ISSUES"]), result["ISSUES"]
        )

    def test_record_shape_violation_is_rejected(self) -> None:
        record = synthetic_record()
        record["unexpected_extra_field"] = value = "SYNTHETIC"
        del record["sent_context_id"]
        result = O.validate_sent_evidence_records([record])
        self.assertFalse(result["VALID"])
        self.assertTrue(
            any("record shape" in issue for issue in result["ISSUES"]),
            result["ISSUES"],
        )
        self.assertEqual(value, "SYNTHETIC")

    def test_non_hex_hash_is_rejected(self) -> None:
        result = O.validate_sent_evidence_records(
            [synthetic_record(sha256="NOT_A_HEX_SHA256")]
        )
        self.assertFalse(result["VALID"])

    def test_exact_text_hashing_is_preserved_without_normalization(self) -> None:
        text = "  前导空格\r\n换行\t制表  "
        record = synthetic_record(text=text)
        self.assertEqual(
            record["sent_evidence_content_sha256"],
            hashlib.sha256(text.encode("utf-8")).hexdigest(),
        )
        self.assertNotEqual(
            record["sent_evidence_content_sha256"],
            hashlib.sha256(text.strip().encode("utf-8")).hexdigest(),
        )
        self.assertNotEqual(
            record["sent_evidence_content_sha256"],
            hashlib.sha256(
                text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
            ).hexdigest(),
        )

    def test_order_preservation_is_checked_against_sent_context_ids(self) -> None:
        observation = _base_observation()
        records = list(observation["retrieval"]["sent_evidence_records"])
        observation["retrieval"]["sent_evidence_records"] = [
            {
                "sent_context_id": "SYNTHETIC_OUT_OF_ORDER_CONTEXT",
                "sent_evidence_text": records[0]["sent_evidence_text"],
                "sent_evidence_content_sha256": records[0][
                    "sent_evidence_content_sha256"
                ],
            }
        ]
        result = O.validate_observation(observation)
        self.assertFalse(result["VALID"])
        self.assertTrue(
            any("order or identity" in issue for issue in result["ISSUES"]),
            result["ISSUES"],
        )

    def test_synthetic_observation_satisfies_the_contract(self) -> None:
        observation = _base_observation()
        records = observation["retrieval"]["sent_evidence_records"]
        self.assertEqual(len(records), 1)
        self.assertEqual(
            [record["sent_context_id"] for record in records],
            observation["generation_input"]["sent_context_ids"],
        )
        result = O.validate_observation(observation)
        self.assertTrue(result["VALID"], result["ISSUES"])
        self.assertTrue(result["SENT_EVIDENCE"]["VALID"])


# --------------------------------------------------------------------------- #
# 11 observation semantic digest canonicalization
# --------------------------------------------------------------------------- #
class G2ObservationSemanticDigestTest(unittest.TestCase):
    def test_canonical_json_rule_matches_the_frozen_serialization(self) -> None:
        value = {"b": 1, "a": "中文", "c": [3, 2, 1]}
        self.assertEqual(
            O.canonical_json(value),
            json.dumps(
                value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ),
        )

    def test_canonical_rule_does_not_escape_non_ascii(self) -> None:
        value = {"中文键": "中文值"}
        self.assertIn("中文", O.canonical_json(value))
        self.assertNotIn("\\u", O.canonical_json(value))
        escaped = json.dumps(
            value, sort_keys=True, ensure_ascii=True, separators=(",", ":")
        )
        self.assertNotEqual(
            O.canonical_digest(value),
            hashlib.sha256(escaped.encode("utf-8")).hexdigest(),
        )

    def test_digest_is_stable_across_repeated_computations(self) -> None:
        observation = _base_observation()
        first = O.compute_observation_semantic_digest(observation)
        second = O.compute_observation_semantic_digest(observation)
        self.assertEqual(first, second)
        self.assertTrue(O.is_hex64(first))

    def test_digest_is_independent_of_record_key_order(self) -> None:
        observation = _base_observation()
        reordered = {
            key: observation[key] for key in reversed(list(observation))
        }
        self.assertEqual(
            O.compute_observation_semantic_digest(observation),
            O.compute_observation_semantic_digest(reordered),
        )

    def test_changing_run_ordinal_changes_the_digest(self) -> None:
        observation = _base_observation()
        before = O.compute_observation_semantic_digest(observation)
        observation["run_identity"]["run_ordinal"] = 2
        self.assertNotEqual(
            O.compute_observation_semantic_digest(observation), before
        )

    def test_changing_a_semantic_field_changes_the_digest(self) -> None:
        mutations = (
            ("routing", "route", "locate"),
            ("scope", "confidence", "low"),
            ("generation_output", "final_application_answer", "改写的答案"),
            ("measurement", "evaluator_version", "SYNTHETIC_OTHER_VERSION"),
        )
        for group, field_name, value in mutations:
            with self.subTest(field=group + "." + field_name):
                observation = _base_observation()
                before = O.compute_observation_semantic_digest(observation)
                observation[group][field_name] = value
                self.assertNotEqual(
                    O.compute_observation_semantic_digest(observation), before
                )

    def test_changing_sent_evidence_text_changes_the_digest(self) -> None:
        observation = _base_observation()
        before = O.compute_observation_semantic_digest(observation)
        observation["retrieval"]["sent_evidence_records"][0][
            "sent_evidence_text"
        ] = "SYNTHETIC_ALTERED_EVIDENCE"
        self.assertNotEqual(
            O.compute_observation_semantic_digest(observation), before
        )

    def test_changing_sent_evidence_content_sha256_changes_the_digest(self) -> None:
        observation = _base_observation()
        before = O.compute_observation_semantic_digest(observation)
        observation["retrieval"]["sent_evidence_records"][0][
            "sent_evidence_content_sha256"
        ] = "f" * 64
        self.assertNotEqual(
            O.compute_observation_semantic_digest(observation), before
        )

    def test_changing_sent_context_id_changes_the_digest(self) -> None:
        observation = _base_observation()
        before = O.compute_observation_semantic_digest(observation)
        observation["retrieval"]["sent_evidence_records"][0][
            "sent_context_id"
        ] = "SYNTHETIC_OTHER_CONTEXT"
        self.assertNotEqual(
            O.compute_observation_semantic_digest(observation), before
        )

    def test_digest_matches_the_envelope_declared_digest(self) -> None:
        payload = base_payload()
        self.assertEqual(
            payload["OBSERVATION_SEMANTIC_DIGEST"],
            O.compute_observation_semantic_digest(payload["OBSERVATION"]),
        )
        self.assertEqual(payload["OBSERVATION_SEMANTIC_KEY_COUNT"], 62)


# --------------------------------------------------------------------------- #
# 12 provenance digest invariance
# --------------------------------------------------------------------------- #
class G2ProvenanceDigestInvarianceTest(unittest.TestCase):
    def test_changing_run_id_leaves_the_digest_unchanged(self) -> None:
        observation = _base_observation()
        before = O.compute_observation_semantic_digest(observation)
        observation["run_identity"]["run_id"] = "SYNTHETIC_OTHER_RUN_ID"
        observation["run_identity"]["observation_timestamp"] = (
            "2099-12-31T23:59:59"
        )
        self.assertEqual(
            O.compute_observation_semantic_digest(observation), before
        )

    def test_changing_the_provenance_block_leaves_the_digest_unchanged(self) -> None:
        observation = _base_observation()
        before = O.compute_observation_semantic_digest(observation)
        observation[O.PROVENANCE_ONLY_BLOCK_KEY].update(
            {
                "absolute_machine_paths": ["E:\\SYNTHETIC\\PATH"],
                "output_paths": ["SYNTHETIC_OUTPUT"],
                "filesystem_mtime": 1234567890.0,
                "filesystem_ctime": 1234567890.0,
                "console_rendering_only_metadata": {"width": 80},
                "source_trace_relative_path_only": "SYNTHETIC/TRACE",
            }
        )
        self.assertEqual(
            O.compute_observation_semantic_digest(observation), before
        )

    def test_removing_the_provenance_block_leaves_the_digest_unchanged(self) -> None:
        observation = _base_observation()
        before = O.compute_observation_semantic_digest(observation)
        del observation[O.PROVENANCE_ONLY_BLOCK_KEY]
        self.assertEqual(
            O.compute_observation_semantic_digest(observation), before
        )

    def test_provenance_mutation_is_reported_as_valid_by_the_key_set_check(
        self,
    ) -> None:
        observation = _base_observation()
        observation["run_identity"]["run_id"] = "SYNTHETIC_OTHER_RUN_ID"
        result = O.validate_observation_semantic_key_set(observation)
        self.assertTrue(result["VALID"], result["ISSUES"])


# --------------------------------------------------------------------------- #
# 13 canonical adapter preserves supplied semantic arguments
# --------------------------------------------------------------------------- #
FORBIDDEN_CALL_KEYWORDS = frozenset(
    {
        "top_k",
        "candidate_limit",
        "include_front_matter",
        "temperature",
        "top_p",
        "repeat_penalty",
        "num_predict",
        "num_ctx",
        "options",
        "keep_alive",
        "stream",
        "prompt",
        "reranker",
        "retrieval_query",
        "max_tokens",
        "timeout",
    }
)
FORBIDDEN_DEFINED_NAMES = frozenset(
    {
        "verify",
        "verify_claim",
        "verify_answer",
        "split_claims",
        "is_factual_claim",
        "latin_key_terms",
        "cjk_key_terms",
        "normalize_compact",
        "extract_numbers",
        "fact_match",
        "match_facts",
        "classify",
        "classifier",
        "readiness",
        "citation_status",
        "attribution_class",
    }
)


class G2CanonicalAdapterArgumentTest(unittest.TestCase):
    def test_prepare_receives_the_canonical_query_history_and_scope(self) -> None:
        _payload, harness = base_payload_entry()
        self.assertEqual(
            harness.record["prepare_calls"],
            [
                {
                    "question": SYNTHETIC_QUERY,
                    "history": [],
                    "scope": None,
                }
            ],
        )

    def test_prepare_history_is_the_canonical_normalization_result(self) -> None:
        from core.query_router import normalize_history

        _payload, harness = base_payload_entry()
        self.assertEqual(
            harness.record["prepare_calls"][0]["history"],
            normalize_history(None),
        )

    def test_build_messages_receives_the_prepared_question_contexts_and_route(
        self,
    ) -> None:
        _payload, harness = base_payload_entry()
        self.assertEqual(
            harness.record["build_messages_calls"],
            [
                {
                    "question": SYNTHETIC_QUERY,
                    "context_count": 1,
                    "route": O.CANONICAL_SUPPORTED_ROUTE,
                    "history": [],
                }
            ],
        )

    def test_model_call_receives_only_the_canonical_messages_and_answer_model(
        self,
    ) -> None:
        payload, harness = base_payload_entry()
        call = harness.record["chat_calls"][0]
        self.assertEqual(call["model"], O.FROZEN_ANSWER_MODEL)
        self.assertIsNone(call["kwargs"])
        self.assertIs(
            call["messages"],
            payload["OBSERVATION"]["generation_input"][
                "application_level_model_visible_context"
            ],
        )

    def test_observer_passes_no_semantic_or_inference_option_override(self) -> None:
        violations: list[str] = []
        for node in _call_nodes(_observer_tree()):
            for keyword in node.keywords:
                if keyword.arg in FORBIDDEN_CALL_KEYWORDS:
                    violations.append(
                        "%s(%s=)" % (_dotted_name(node.func), keyword.arg)
                    )
        self.assertEqual(violations, [])

    def test_exactly_one_retrieval_and_one_model_call_per_synthetic_run(self) -> None:
        payload, _harness = base_payload_entry()
        self.assertEqual(payload["COUNTERS"]["TARGET_OBSERVATION_RUNS"], 1)
        self.assertEqual(payload["COUNTERS"]["PRODUCTION_RETRIEVAL_RUNS"], 1)
        self.assertEqual(payload["COUNTERS"]["EMBEDDING_CALLS"], 1)
        self.assertEqual(payload["COUNTERS"]["MODEL_CALLS"], 1)
        self.assertEqual(payload["COUNTERS"]["COUNTERFACTUAL_RUNS"], 0)
        self.assertEqual(payload["COUNTERS"]["FULL_144_RUNS"], 0)

    def test_canonical_qa_top_k_binding_matches_the_engine_source(self) -> None:
        source = _engine_prepare_source()
        match = re.search(
            r'top_k\s*=\s*10 if route == "locate_chapter" else 7 if '
            r'route == "compare" else (\d+)',
            source,
        )
        self.assertIsNotNone(match, "canonical top_k expression not found")
        self.assertEqual(int(match.group(1)), O.CANONICAL_QA_TOP_K)
        self.assertEqual(O.CANONICAL_QA_TOP_K, 5)

    def test_canonical_retrieval_query_binding_matches_the_engine_source(self) -> None:
        source = _engine_prepare_source()
        self.assertIn(
            'retrieval_query = clean_location_query(routing_question) if route '
            'in {"locate", "locate_chapter"} else routing_question',
            source,
        )
        self.assertIn(
            "routing_question = decision.normalized_question", source
        )
        self.assertIn("clean_location_query", O.CANONICAL_RETRIEVAL_QUERY_SOURCE)

    def test_retrieval_query_recorded_is_the_canonical_normalized_question(
        self,
    ) -> None:
        observation = _base_observation()
        self.assertEqual(
            observation["retrieval"]["retrieval_query"], SYNTHETIC_QUERY
        )
        self.assertEqual(
            observation["retrieval"]["retrieval_query"],
            observation["routing"]["normalized_question"],
        )
        self.assertEqual(observation["retrieval"]["top_k"], O.CANONICAL_QA_TOP_K)

    def test_scope_assertion_uses_the_resolved_scope_and_known_documents(
        self,
    ) -> None:
        _payload, harness = base_payload_entry()
        calls = harness.record["scope_assertion_calls"]
        self.assertEqual(len(calls), 2)
        for entry in calls:
            with self.subTest(citation_ids=entry["citation_ids"]):
                self.assertEqual(entry["citation_ids"], [1])
                self.assertEqual(entry["resolution_mode"], "default")
                self.assertEqual(entry["known_document_count"], 1)

    def test_canonical_parsers_agree_on_normalized_answers(self) -> None:
        from core.citation_verifier import citation_numbers

        answer = "GSM 使用 GMSK 调制[1]。[450]MHz 是频段[2]。"
        engine_pattern = [
            int(value)
            for value in re.findall(r"\[(\d+)\](?![A-Za-z])", answer)
        ]
        self.assertEqual(citation_numbers(answer), engine_pattern)


# --------------------------------------------------------------------------- #
# 14 raw and final answer remain distinct
# --------------------------------------------------------------------------- #
class G2RawFinalAnswerTest(unittest.TestCase):
    def test_raw_answer_is_the_exact_canonical_chat_return(self) -> None:
        observation = _base_observation()
        self.assertEqual(
            observation["generation_output"]["raw_model_answer"],
            SYNTHETIC_RAW_ANSWER,
        )

    def test_raw_and_final_answers_are_captured_at_distinct_points(self) -> None:
        observation = _base_observation()
        raw = observation["generation_output"]["raw_model_answer"]
        final = observation["generation_output"]["final_application_answer"]
        self.assertNotEqual(raw, final)
        self.assertIn("[9]", raw)
        self.assertNotIn("[9]", final)

    def test_final_answer_equals_the_canonical_postprocessing_chain(self) -> None:
        observation = _base_observation()
        _payload, harness = base_payload_entry()
        chunks = harness.record["sent_contexts"]
        citations = [
            chunk.citation(index) for index, chunk in enumerate(chunks, 1)
        ]
        normalized, verified = harness.bindings.engine_v2.normalize_citations(
            SYNTHETIC_RAW_ANSWER.strip(), len(chunks)
        )
        self.assertFalse(
            verified,
            "the synthetic raw answer carries an invalid citation, so the "
            "canonical normalization reports unverified",
        )
        self.assertTrue(
            harness.bindings.engine_v2.citation_support_verified(
                normalized, chunks, []
            )
        )
        renumbered, _used = harness.bindings.engine_v2.renumber_citations(
            normalized, citations
        )
        self.assertEqual(
            observation["generation_output"]["final_application_answer"],
            renumbered,
        )

    def test_final_answer_is_never_copied_from_the_raw_answer(self) -> None:
        observation = _base_observation()
        fields = observation["generation_output"]
        self.assertEqual(
            sorted(fields), ["expected_fact_presence", "final_application_answer", "raw_model_answer"]
        )
        self.assertIsInstance(fields["raw_model_answer"], str)
        self.assertIsInstance(fields["final_application_answer"], str)

    def test_final_answer_matches_the_canonical_result_object(self) -> None:
        payload, harness = base_payload_entry()
        engine = harness.engine_holder["engine"]
        self.assertEqual(
            payload["OBSERVATION"]["generation_output"][
                "final_application_answer"
            ],
            engine.result.answer,
        )
        self.assertEqual(
            payload["OBSERVATION"]["citation"]["citation_verifier_output"],
            engine.result.citation_report,
        )


# --------------------------------------------------------------------------- #
# 15 verifier / evaluator capture without reinterpretation
# --------------------------------------------------------------------------- #
def run_synthetic_with(real_evaluator: bool = False, real_verifier: bool = False):
    import eval_v4_baseline as real_evaluator_module
    from core.citation_verifier import DeterministicCitationVerifier
    from dataclasses import replace as _replace

    harness = SyntheticBindings()
    bindings = O.CanonicalBindings(
        engine_factory=harness.bindings.engine_factory,
        engine_v2=harness.bindings.engine_v2,
        citation_verifier=(
            __import__("core.citation_verifier", fromlist=["CITATION_VERIFIER_VERSION"])
            if real_verifier
            else harness.bindings.citation_verifier
        ),
        evaluator=(
            real_evaluator_module if real_evaluator else harness.bindings.evaluator
        ),
        config=harness.bindings.config,
        library_store=harness.bindings.library_store,
        query_scope=harness.bindings.query_scope,
        chat=harness.bindings.chat,
        rule_identity_reader=harness.bindings.rule_identity_reader,
        rule_identity_manifest_provider=(
            harness.bindings.rule_identity_manifest_provider
        ),
    )
    if real_verifier:
        base_factory = harness.bindings.engine_factory

        def factory(path):  # noqa: ANN001
            engine = base_factory(path)
            engine.citation_verifier = DeterministicCitationVerifier()
            return engine

        bindings = _replace(bindings, engine_factory=factory)
    payload = O.run_live_observation(live_request(), bindings)
    return payload, harness


class G2VerifierEvaluatorCaptureTest(unittest.TestCase):
    def test_original_material_three_remains_bound_after_final_renumbering(self) -> None:
        contexts = [SyntheticChunk(chunk_id="synthetic-original-%d" % index)
                    for index in (1, 2, 3)]
        harness = SyntheticBindings(SyntheticPrepared(contexts=contexts),
                                    raw_answer="GMSK。[3]")
        payload = O.run_live_observation(live_request(), harness.bindings)
        self.assertEqual(payload["STATUS"], "OBSERVED")
        citation = payload["OBSERVATION"]["citation"]
        self.assertEqual(payload["OBSERVATION"]["generation_output"]["final_application_answer"], "GMSK。[1]")
        self.assertEqual(citation["emitted_citation_tokens"], [1])
        self.assertEqual(citation["parsed_targets"]["unique_in_first_appearance_order"], [3])
        self.assertEqual(citation["target_identities"]["resolved"], {"3": contexts[2].id})
        self.assertEqual(harness.record["verify_calls"][0]["answer"], "GMSK。[3]")

    def test_original_three_then_one_targets_survive_final_one_then_two(self) -> None:
        contexts = [SyntheticChunk(chunk_id="synthetic-original-%d" % index)
                    for index in (1, 2, 3)]
        harness = SyntheticBindings(SyntheticPrepared(contexts=contexts),
                                    raw_answer="GMSK。[3][1]")
        payload = O.run_live_observation(live_request(), harness.bindings)
        self.assertEqual(payload["STATUS"], "OBSERVED")
        citation = payload["OBSERVATION"]["citation"]
        self.assertEqual(payload["OBSERVATION"]["generation_output"]["final_application_answer"], "GMSK。[1][2]")
        self.assertEqual(citation["emitted_citation_tokens"], [1, 2])
        self.assertEqual(citation["parsed_targets"]["unique_in_first_appearance_order"], [3, 1])
        self.assertEqual(citation["target_identities"]["resolved"], {"3": contexts[2].id, "1": contexts[0].id})

    def test_post_timer_telemetry_capture_matches_the_same_execution_stable_payload(self) -> None:
        payload, harness = base_payload_entry()
        captured = payload["CANONICAL_TELEMETRY_CAPTURE"]
        expected = {key: value for key, value in harness.record["telemetry_calls"][0].items()
                    if key not in ("ts", "elapsed_ms")}
        self.assertEqual(captured["STABLE_PAYLOAD"], expected)
        self.assertEqual(captured["DYNAMIC_TIMESTAMP_OR_APPEND_ELAPSED_CAPTURED"], "NO")
        self.assertEqual(captured["ENGINE_RESULT_ELAPSED_MS"],
                         harness.record["result_calls"][0]["engine_result_elapsed_ms"])

    def test_verifier_output_is_recorded_verbatim_from_the_canonical_report(
        self,
    ) -> None:
        payload, harness = base_payload_entry()
        engine = harness.engine_holder["engine"]
        self.assertIs(
            payload["OBSERVATION"]["citation"]["citation_verifier_output"],
            engine.result.citation_report,
        )
        self.assertEqual(
            payload["OBSERVATION"]["citation"]["citation_verifier_output"],
            harness.record["result_calls"][0]["citation_report"],
        )

    def test_alignment_result_is_derived_only_from_the_canonical_report(self) -> None:
        observation = _base_observation()
        report = observation["citation"]["citation_verifier_output"]
        self.assertEqual(
            observation["citation"]["alignment_result"][
                "supports_in_claim_order"
            ],
            [item["support"] for item in report["verifications"]],
        )

    def test_invalid_and_scope_violation_counts_come_from_the_report(self) -> None:
        observation = _base_observation()
        report = observation["citation"]["citation_verifier_output"]
        self.assertEqual(
            observation["citation"]["invalid_citation_count"],
            report["invalid_citation_count"],
        )
        self.assertEqual(
            observation["citation"]["scope_violation_count"],
            report["citation_scope_violation"],
        )

    def test_verifier_receives_the_pre_renumber_answer_and_sent_evidence(self) -> None:
        _payload, harness = base_payload_entry()
        call = harness.record["verify_calls"][0]
        self.assertEqual(call["evidence_text_keys"], [1])
        self.assertEqual(call["citation_count"], 1)
        self.assertNotIn("[9]", call["answer"])

    def test_evaluator_output_is_the_canonical_evaluator_row_verbatim(self) -> None:
        payload, harness = base_payload_entry()
        self.assertIs(
            payload["OBSERVATION"]["measurement"]["evaluator_output"],
            harness.record["evaluator_rows"][0],
        )

    def test_measurement_uses_the_real_canonical_evaluator_row(self) -> None:
        import eval_v4_baseline as real_evaluator_module

        payload, harness = run_synthetic_with(real_evaluator=True)
        row = payload["OBSERVATION"]["measurement"]["evaluator_output"]
        engine = harness.engine_holder["engine"]
        golden = json.loads(
            (ROOT_DIR / O.CANONICAL_GOLDEN_PATH).read_text(encoding="utf-8")
        )
        case = golden["cases"][O.CANONICAL_GOLDEN_CASE_INDEX]
        self.assertEqual(
            row,
            real_evaluator_module._build_row(case, engine.result, row["elapsed_ms"]),
        )
        self.assertEqual(
            row["evaluator_version"], real_evaluator_module.EVALUATOR_VERSION
        )
        self.assertEqual(row["id"], O.CANONICAL_GOLDEN_CASE_ID)

    def test_real_canonical_verifier_reports_its_frozen_version(self) -> None:
        from core.citation_verifier import CITATION_VERIFIER_VERSION

        payload, _harness = run_synthetic_with(real_verifier=True)
        report = payload["OBSERVATION"]["citation"]["citation_verifier_output"]
        self.assertEqual(report["verifier_version"], CITATION_VERIFIER_VERSION)
        self.assertEqual(
            payload["OBSERVATION"]["measurement"]["verifier_version"],
            CITATION_VERIFIER_VERSION,
        )

    def test_fact_matcher_output_comes_from_the_canonical_row(self) -> None:
        observation = _base_observation()
        row = observation["measurement"]["evaluator_output"]
        matcher = observation["measurement"]["fact_matcher_output"]
        self.assertEqual(matcher["fact_present"], row["fact_present"])
        self.assertEqual(matcher["fact_total"], row["fact_total"])
        self.assertEqual(matcher["missing_facts"], list(row["missing_facts"]))

    def test_expected_fact_presence_matches_the_canonical_membership_rule(self) -> None:
        observation = _base_observation()
        facts = observation["case_identity"]["expected_fact_contract"][
            "EXPECTED_ANSWER_FACTS"
        ]
        answer = observation["generation_output"]["final_application_answer"]
        self.assertEqual(
            observation["generation_output"]["expected_fact_presence"],
            [fact for fact in facts if fact in answer],
        )

    def test_evaluator_and_verifier_versions_come_from_canonical_constants(
        self,
    ) -> None:
        import eval_v4_baseline as real_evaluator_module
        from core.citation_verifier import CITATION_VERIFIER_VERSION

        observation = _base_observation()
        self.assertEqual(
            observation["measurement"]["evaluator_version"],
            real_evaluator_module.EVALUATOR_VERSION,
        )
        self.assertEqual(
            observation["measurement"]["verifier_version"],
            CITATION_VERIFIER_VERSION,
        )

    def test_observer_defines_no_second_verifier_or_fact_matcher(self) -> None:
        defined: list[str] = []
        for node in ast.walk(_observer_tree()):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name in FORBIDDEN_DEFINED_NAMES:
                    defined.append(node.name)
        self.assertEqual(defined, [])
        source = OBSERVER_PATH.read_text(encoding="utf-8")
        self.assertNotIn("[。！？!?；;", source)
        self.assertNotIn("_SENTENCE_BOUNDARY", source)
        self.assertNotIn("claim_index", source)

    def test_required_support_reached_generation_uses_the_sent_evidence_text(
        self,
    ) -> None:
        observation = _base_observation()
        support = observation["retrieval"]["required_support_reached_generation"]
        texts = [
            record["sent_evidence_text"]
            for record in observation["retrieval"]["sent_evidence_records"]
        ]
        facts = observation["case_identity"]["expected_fact_contract"][
            "EXPECTED_ANSWER_FACTS"
        ]
        expected_present, expected_missing = O.exact_substring_presence(facts, texts)
        self.assertEqual(support["PRESENT_IN_SENT_EVIDENCE"], expected_present)
        self.assertEqual(support["MISSING_FROM_SENT_EVIDENCE"], expected_missing)
        self.assertEqual(
            support["REQUIRED_SUPPORT_REACHED_GENERATION"], not expected_missing
        )


# --------------------------------------------------------------------------- #
# 16 observer self write-free
# --------------------------------------------------------------------------- #
class G2ObserverSelfWriteFreeTest(unittest.TestCase):
    def test_observer_source_has_no_writer_calls(self) -> None:
        self.assertEqual(_writer_violations(_observer_tree()), [])

    def test_observer_opens_only_read_only_inputs(self) -> None:
        modes: list[str] = []
        for node in _call_nodes(_observer_tree()):
            if _callable_name(node.func) != "open":
                continue
            for keyword in node.keywords:
                if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
                    modes.append(str(keyword.value.value))
            for argument in list(node.args)[1:2]:
                if isinstance(argument, ast.Constant):
                    modes.append(str(argument.value))
        self.assertTrue(modes, "expected at least one explicit read-only open")
        for mode in modes:
            self.assertIn(mode, ("r", "rb", "rt"))

    def test_observer_has_no_attribute_or_environment_assignment(self) -> None:
        self.assertEqual(_attribute_assignment_violations(_observer_tree()), [])

    def test_observer_self_sha_is_not_pinned_in_its_own_source(self) -> None:
        source = OBSERVER_PATH.read_text(encoding="utf-8")
        self.assertNotIn(O.observer_file_raw_sha256(), source)
        self.assertNotIn("observer_file_raw_sha256() ==", source)

    def test_observer_exposes_no_self_sha_constant(self) -> None:
        for node in _observer_tree().body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.assertNotIn(
                            "OBSERVER_SHA256",
                            target.id,
                            "the observer must not pin its own sha256",
                        )

    def test_static_contract_declares_the_write_free_contract(self) -> None:
        payload = O.describe_contract()
        self.assertEqual(payload["observer_self_write_free"], "YES")
        self.assertEqual(payload["observer_sha256_self_pinned"], "NO")
        self.assertEqual(payload["stdout_only"], "YES")

    def test_blocked_and_live_payloads_write_nothing(self) -> None:
        before = {path: path.stat().st_mtime_ns for path in _governed_paths()}
        run_blocked(g4_authorization="")
        base_payload()
        after = {path: path.stat().st_mtime_ns for path in _governed_paths()}
        self.assertEqual(before, after)


def _engine_prepare_source() -> str:
    """Whitespace-normalized canonical engine source (the real file text).

    The canonical engine entry points are patched during this module's run, so
    the binding witnesses read the canonical source file rather than a patched
    object's ``inspect`` output.
    """
    engine_path = ROOT_DIR / "core" / "engine_v2.py"
    return " ".join(engine_path.read_text(encoding="utf-8").split())


def _governed_paths() -> list[Path]:
    return [
        ACCEPTED_G1_BASE_ARTIFACT,
        ACCEPTED_G1_A001_ARTIFACT,
        ACCEPTED_G1_A001_FC1_ARTIFACT,
        G0_PREFLIGHT_ARTIFACT,
        ROOT_DIR / O.CANONICAL_GOLDEN_PATH,
        ROOT_DIR / O.FROZEN_MASTER_PATH,
        ROOT_DIR / O.FROZEN_EVALUATOR_PATH,
        ROOT_DIR / O.FROZEN_CITATION_VERIFIER_PATH,
        ROOT_DIR / O.RUNTIME_DB_RELATIVE_PATH,
        OBSERVER_PATH,
    ]


# --------------------------------------------------------------------------- #
# 17 no Product / Golden / evaluator / verifier / DB mutation path
# --------------------------------------------------------------------------- #
class G2GovernedArtifactMutationTest(unittest.TestCase):
    def test_observer_imports_no_writer_capable_modules(self) -> None:
        imported: set[str] = set()
        for node in ast.walk(_observer_tree()):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
        for module_name in ("sqlite3", "shutil", "tempfile", "subprocess"):
            self.assertNotIn(module_name, imported)
        self.assertEqual(_writer_violations(_observer_tree()), [])

    def test_observer_never_opens_a_governed_artifact_for_writing(self) -> None:
        for node in _call_nodes(_observer_tree()):
            if _callable_name(node.func) != "open":
                continue
            for argument in list(node.args)[1:2]:
                if isinstance(argument, ast.Constant):
                    self.assertNotIn(
                        str(argument.value), FORBIDDEN_WRITE_MODES
                    )
        self.assertTrue(_reads_only_input_sources(_observer_tree()))

    def test_observer_has_no_runtime_database_write_path(self) -> None:
        source = OBSERVER_PATH.read_text(encoding="utf-8")
        for token in (
            "import sqlite3",
            "INSERT INTO",
            "DELETE FROM",
            "CREATE TABLE",
            "DROP TABLE",
            "VACUUM",
            "connect(",
            "cursor(",
        ):
            self.assertNotIn(token, source)

    def test_observer_does_not_mutate_configuration_or_environment(self) -> None:
        source = OBSERVER_PATH.read_text(encoding="utf-8")
        for token in (
            "os.environ",
            "putenv",
            "setenv",
            "TELEMETRY_ENABLED",
            "config_module.ANSWER_MODEL =",
            "config.ANSWER_MODEL =",
        ):
            self.assertNotIn(token, source)
        self.assertEqual(_attribute_assignment_violations(_observer_tree()), [])
        for node in _call_nodes(_observer_tree()):
            self.assertNotIn(
                _callable_name(node.func),
                ("setattr", "delattr", "setdefault"),
                "no attribute or environment patching is allowed",
            )

    def test_governed_artifacts_are_byte_identical_after_the_test_doubles(
        self,
    ) -> None:
        digests = {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in _governed_paths()
        }
        run_blocked(case_id="cit-002")
        base_payload()
        for path, digest in digests.items():
            with self.subTest(path=path.name):
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(), digest
                )


# --------------------------------------------------------------------------- #
# 18 stdout-only output contract
# --------------------------------------------------------------------------- #
class G2StdoutOnlyOutputTest(unittest.TestCase):
    def test_observer_declares_no_output_file_option(self) -> None:
        option_strings: list[str] = []
        for node in _call_nodes(_observer_tree()):
            if _callable_name(node.func) != "add_argument":
                continue
            for argument in node.args:
                if isinstance(argument, ast.Constant) and isinstance(
                    argument.value, str
                ):
                    option_strings.append(argument.value)
        self.assertTrue(option_strings)
        for option in option_strings:
            self.assertFalse(
                re.match(r"^--(out|output|write|log|artifact)", option), option
            )
        self.assertEqual(_stdout_contract_violations(_observer_tree()), [])

    def test_observer_uses_no_direct_stream_writes(self) -> None:
        source = OBSERVER_PATH.read_text(encoding="utf-8")
        self.assertNotIn(".write(", source)
        self.assertNotIn("json.dump(", source)

    def test_static_mode_payload_arrives_on_stdout(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer), redirect_stderr(io.StringIO()):
            code = O.main(["--describe-contract"])
        self.assertEqual(code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["checkpoint"], O.CHECKPOINT)

    def test_validate_observation_reads_stdin_for_dash(self) -> None:
        payload = base_payload_for_validation()
        fake_stdin = io.StringIO(json.dumps(payload))
        buffer = io.StringIO()
        original_stdin = sys.stdin
        sys.stdin = fake_stdin
        try:
            with redirect_stdout(buffer):
                code = O.main(["--validate-observation", "-"])
        finally:
            sys.stdin = original_stdin
        self.assertEqual(code, 0)
        result = json.loads(buffer.getvalue())
        self.assertTrue(result["VALID"], result["ISSUES"])
        self.assertEqual(result["MODEL_CALLS"], 0)

    def test_invalid_payload_exits_non_zero_without_touching_a_real_call(
        self,
    ) -> None:
        payload = base_payload_for_validation()
        observation = payload["OBSERVATION"]
        observation["retrieval"]["sent_evidence_records"] = [
            synthetic_record(
                text="SYNTHETIC_ALTERED_EVIDENCE",
                sha256=observation["retrieval"]["sent_evidence_records"][0][
                    "sent_evidence_content_sha256"
                ],
            )
        ]
        buffer = io.StringIO()
        fake_stdin = io.StringIO(json.dumps(payload))
        original_stdin = sys.stdin
        sys.stdin = fake_stdin
        try:
            with redirect_stdout(buffer):
                code = O.main(["--validate-observation", "-"])
        finally:
            sys.stdin = original_stdin
        self.assertEqual(code, 3)
        result = json.loads(buffer.getvalue())
        self.assertFalse(result["VALID"])
        self.assertEqual(_REAL_CALL_ATTEMPTS, [])


# --------------------------------------------------------------------------- #
# 19 no classifier / readiness implementation
# --------------------------------------------------------------------------- #
class G2NoClassifierLogicTest(unittest.TestCase):
    def test_observer_source_contains_no_classifier_or_readiness_vocabulary(
        self,
    ) -> None:
        source = OBSERVER_PATH.read_text(encoding="utf-8")
        present = [
            token for token in FORBIDDEN_CLASSIFIER_TOKENS if token in source
        ]
        self.assertEqual(present, [])

    def test_observation_record_carries_no_classifier_or_readiness_keys(self) -> None:
        observation = _base_observation()
        serialized = json.dumps(observation, ensure_ascii=False)
        for token in FORBIDDEN_CLASSIFIER_TOKENS:
            self.assertNotIn(token, serialized)
        for key in ("CITATION_STATUS", "READINESS_CLASS", "NEXT_PERMISSIBLE_ACTION"):
            self.assertNotIn(key, observation)

    def test_static_contract_does_not_publish_classifier_outputs(self) -> None:
        payload = O.describe_contract()
        serialized = json.dumps(payload, ensure_ascii=False)
        for token in FORBIDDEN_CLASSIFIER_TOKENS:
            self.assertNotIn(token, serialized)
        self.assertEqual(payload["current_citation_status"], "NOT_EVALUATED_IN_G2")
        self.assertEqual(payload["scientific_attribution_performed"], "NO")
        self.assertEqual(payload["current_observation_captured"], "NO")

    def test_live_envelope_declares_no_scientific_outcome(self) -> None:
        payload = base_payload()
        serialized = json.dumps(payload, ensure_ascii=False)
        for token in FORBIDDEN_CLASSIFIER_TOKENS:
            self.assertNotIn(token, serialized)
        self.assertEqual(payload["STATUS"], "OBSERVED")

    def test_observer_defines_no_classifier_or_readiness_helper(self) -> None:
        defined: list[str] = []
        for node in ast.walk(_observer_tree()):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name in FORBIDDEN_DEFINED_NAMES:
                    defined.append(node.name)
        self.assertEqual(defined, [])


# --------------------------------------------------------------------------- #
# 20 unresolved G4 side-effect policy zero-call fail
# --------------------------------------------------------------------------- #
class G2SideEffectPolicyGuardTest(unittest.TestCase):
    def test_live_without_side_effect_policy_blocks_with_zero_calls(self) -> None:
        payload = run_blocked(g4_side_effect_policy="")
        self.assertEqual(payload["STATUS"], "BLOCKED_BEFORE_INVOCATION")
        checks = {item["CHECK"]: item["PASS"] for item in payload["LIVE_GUARD_CHECKS"]}
        self.assertFalse(checks["G4_SIDE_EFFECT_POLICY_RESOLVED"])
        self.assertEqual(payload["MODEL_CALLS"], 0)
        self.assertEqual(payload["EMBEDDING_CALLS"], 0)
        self.assertEqual(payload["PRODUCTION_RETRIEVAL_RUNS"], 0)
        self.assertEqual(payload["TARGET_OBSERVATION_RUNS"], 0)

    def test_missing_authorization_and_policy_together_blocks_with_zero_calls(
        self,
    ) -> None:
        payload = run_blocked(g4_authorization="", g4_side_effect_policy="")
        self.assertEqual(payload["STATUS"], "BLOCKED_BEFORE_INVOCATION")
        self.assertIsNone(payload["OBSERVATION"])
        self.assertEqual(payload["COUNTERS"]["MODEL_CALLS"], 0)

    def test_live_run_records_the_resolved_side_effect_policy(self) -> None:
        payload = base_payload()
        self.assertEqual(
            payload["RUN_BINDINGS"]["g4_side_effect_policy"],
            SYNTHETIC_G4_SIDE_EFFECT_POLICY,
        )
        self.assertTrue(payload["RUN_BINDINGS"]["g4_authorization_present"])

    def test_side_effect_declaration_enumerates_every_known_runtime_write(
        self,
    ) -> None:
        payload = base_payload()
        effects = " ".join(
            item["EFFECT"] for item in payload["SIDE_EFFECT_DECLARATION"]
        )
        self.assertIn("telemetry", effects)
        self.assertIn("cache", effects)
        self.assertIn("artifact", effects)
        for item in payload["SIDE_EFFECT_DECLARATION"]:
            self.assertTrue(item["HANDLING"])

    def test_observer_never_disables_telemetry_or_redirects_the_cache(self) -> None:
        source = OBSERVER_PATH.read_text(encoding="utf-8")
        for token in (
            "TELEMETRY_ENABLED",
            "eval_cache",
            "CACHE_DIR",
            "setenv",
            "os.environ",
        ):
            self.assertNotIn(token, source)
        self.assertEqual(_attribute_assignment_violations(_observer_tree()), [])


# --------------------------------------------------------------------------- #
# 21 G2_EQ1 canonical evaluator non-streaming generation branch (witnesses A-F)
# --------------------------------------------------------------------------- #
def canonical_evaluator_source() -> str:
    return (ROOT_DIR / O.CANONICAL_EVALUATOR_PATH).read_text(encoding="utf-8")


def engine_source() -> str:
    return (ROOT_DIR / "core" / "engine_v2.py").read_text(encoding="utf-8")


class _MarkerClient:
    """Test-only client double exposing only the canonical non-streaming chat."""

    def __init__(self, answer: str = "SYNTHETIC_TEST_ONLY_CLIENT_ANSWER") -> None:
        self.answer = answer
        self.calls: list = []

    def chat(self, messages, model=None):  # noqa: ANN001
        self.calls.append({"messages": messages, "model": model})
        return self.answer


class G2Eq1CanonicalEvaluatorBranchTest(unittest.TestCase):
    def test_canonical_evaluator_answer_call_supplies_no_on_token(self) -> None:
        tree = ast.parse(canonical_evaluator_source())
        answer_calls = [
            node
            for node in _call_nodes(tree)
            if _dotted_name(node.func).endswith(".answer")
        ]
        self.assertTrue(answer_calls, "canonical evaluator answer call not found")
        keywords = [keyword.arg for call in answer_calls for keyword in call.keywords]
        self.assertNotIn("on_token", keywords)
        self.assertIn(
            O.CANONICAL_EVALUATOR_ANSWER_CALL_SOURCE, canonical_evaluator_source()
        )

    def test_engine_answer_default_on_token_is_none(self) -> None:
        witness = O.canonical_evaluator_generation_branch_witness()
        self.assertIn("on_token", witness["ENGINE_ANSWER_PARAMETERS"])
        self.assertIsNone(witness["ENGINE_ON_TOKEN_DEFAULT_VALUE"])
        self.assertEqual(O.CANONICAL_EVALUATOR_SUPPLIES_ON_TOKEN, "NO")
        self.assertIn(
            "on_token", witness["ENGINE_ANSWER_PARAMETERS"],
        )

    def test_on_token_none_selects_the_non_streaming_chat_call(self) -> None:
        witness = O.canonical_evaluator_generation_branch_witness()
        self.assertEqual(witness["ENGINE_ON_TOKEN_NONE_SELECTS_CHAT"], "YES")
        self.assertEqual(
            witness["CHAT_CALL_ARGUMENT_SHAPE"]["KEYWORD_ARGUMENTS"], ["model"]
        )
        self.assertEqual(
            witness["CHAT_CALL_ARGUMENT_SHAPE"]["OPTION_OVERRIDE_PRESENT"], "NO"
        )
        self.assertEqual(
            witness["GENERATION_BRANCH_MARKERS"]["CHAT_CALL_POSITIONAL_COUNT"], 1
        )

    def test_on_token_none_does_not_select_chat_stream(self) -> None:
        witness = O.canonical_evaluator_generation_branch_witness()
        self.assertEqual(
            witness["ENGINE_ON_TOKEN_NONE_DOES_NOT_SELECT_CHAT_STREAM"], "YES"
        )
        self.assertEqual(
            witness["CHAT_STREAM_BRANCH_IS_ALTERNATIVE_CALLBACK_PATH"], "YES"
        )
        self.assertIn(
            "self.ollama.chat_stream",
            witness["GENERATION_BRANCH_MARKERS"]["STREAMING_BODY_MARKERS"],
        )
        self.assertNotIn(
            "self.ollama.chat_stream",
            witness["GENERATION_BRANCH_MARKERS"]["FALLBACK_BODY_MARKERS"],
        )

    def test_canonical_branch_witness_reports_pass(self) -> None:
        witness = O.canonical_evaluator_generation_branch_witness()
        self.assertEqual(
            witness["FIX_A_NONSTREAMING_CANONICAL_EVALUATOR_BRANCH"], "PASS"
        )
        self.assertEqual(
            witness["CANONICAL_EVALUATOR_NO_ON_TOKEN_WITNESS"], "YES"
        )
        self.assertEqual(
            witness["CANONICAL_EVALUATOR_SUPPLIES_ON_TOKEN"], "NO"
        )

    def test_observer_default_model_call_is_the_canonical_non_streaming_chat(
        self,
    ) -> None:
        self.assertEqual(O.OBSERVER_DEFAULT_MODEL_CALL, "OllamaClient.chat")
        self.assertEqual(
            O.CANONICAL_NONSTREAMING_CHAT_METHOD,
            "core/ollama_http.py#OllamaClient.chat",
        )
        bindings = O.default_canonical_bindings()
        client = _MarkerClient()
        messages = [{"role": "user", "content": "SYNTHETIC_TEST_ONLY"}]
        answer = bindings.chat(client, messages, O.FROZEN_ANSWER_MODEL)
        self.assertEqual(answer, client.answer)
        self.assertEqual(
            client.calls,
            [{"messages": messages, "model": O.FROZEN_ANSWER_MODEL}],
        )
        self.assertFalse(hasattr(bindings, "chat_stream"))

    def test_observer_live_path_contains_no_chat_stream_call(self) -> None:
        chat_stream_calls = [
            node
            for node in _call_nodes(_observer_tree())
            if _callable_name(node.func) == "chat_stream"
        ]
        self.assertEqual(chat_stream_calls, [])
        self.assertEqual(O.OBSERVER_STREAMING_GENERATION_BRANCH_REMOVED, "YES")
        self.assertEqual(
            list(O.CanonicalBindings.__dataclass_fields__),
            [
                "engine_factory",
                "engine_v2",
                "citation_verifier",
                "evaluator",
                "config",
                "library_store",
                "query_scope",
                "chat",
                # G2_EQ4 FIX_3 test-only read-only seams for the invocation-time
                # accepted-rule identity (both default to None in live mode).
                "rule_identity_reader",
                "rule_identity_manifest_provider",
            ],
        )
        self.assertIn(
            "resolved.chat(engine.ollama, messages, engine.answer_model)",
            OBSERVER_PATH.read_text(encoding="utf-8"),
        )


# --------------------------------------------------------------------------- #
# 22 G2_EQ1 current canonical request identity capture (witnesses G-J)
# --------------------------------------------------------------------------- #
class _CapturedResponse:
    """Test-only lowest-transport response double (no socket, no HTTP)."""

    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc_info) -> bool:
        return False


class _TransportSentinel:
    """Test-only lowest-transport sentinel: records, never opens a connection."""

    def __init__(self, response_body: bytes) -> None:
        self.records: list = []
        self.interceptions = 0
        self._response_body = response_body

    def transport(self, request, timeout=None):  # noqa: ANN001
        self.interceptions += 1
        self.records.append(
            {
                "url": request.full_url,
                "method": request.get_method(),
                "payload": json.loads(request.data.decode("utf-8")),
                "timeout": timeout,
            }
        )
        return _CapturedResponse(self._response_body)


def _isolated_real_ollama_http_module():
    """Load the current real ``core/ollama_http.py`` source as an isolated module.

    The G2 harness patches the imported module's real-call boundaries to raise,
    so the capture loads the same current source bytes once more and intercepts
    its lowest HTTP transport with a test-only sentinel instead.  Zero network
    requests are performed; the executed implementation is the current real one.
    """
    import importlib.util

    path = ROOT_DIR / "core" / "ollama_http.py"
    spec = importlib.util.spec_from_file_location(
        "ws13_real_ollama_http_capture_probe", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def capture_current_real_chat_request(
    model: str | None = None,
    messages: list | None = None,
) -> dict:
    """Run the real current non-streaming chat once with no network."""
    module = _isolated_real_ollama_http_module()
    sentinel = _TransportSentinel(
        json.dumps(
            {"message": {"content": "SYNTHETIC_CAPTURE_ONLY_ANSWER"}},
            ensure_ascii=False,
        ).encode("utf-8")
    )
    client = module.OllamaClient()
    call_messages = (
        messages
        if messages is not None
        else [{"role": "user", "content": "SYNTHETIC_TEST_ONLY_MESSAGE"}]
    )
    with unittest.mock.patch.object(module, "open_request", sentinel.transport):
        answer = client.chat(call_messages, model=model)
    return {
        "module": module,
        "sentinel": sentinel,
        "answer": answer,
        "messages": call_messages,
        "record": sentinel.records[0] if sentinel.records else None,
    }


class G2Eq1CurrentRequestIdentityCaptureTest(unittest.TestCase):
    def test_current_real_chat_request_is_captured_without_network(self) -> None:
        captured = capture_current_real_chat_request(model=O.FROZEN_ANSWER_MODEL)
        self.assertEqual(captured["sentinel"].interceptions, 1)
        self.assertEqual(captured["answer"], "SYNTHETIC_CAPTURE_ONLY_ANSWER")
        record = captured["record"]
        self.assertEqual(urlsplit(record["url"]).path, "/api/chat")
        self.assertEqual(record["method"], "POST")
        self.assertEqual(record["payload"]["model"], O.FROZEN_ANSWER_MODEL)
        self.assertEqual(
            record["payload"]["messages"], captured["messages"]
        )
        self.assertEqual(
            sorted(record["payload"]),
            ["keep_alive", "messages", "model", "options", "stream"],
        )
        self.assertEqual(record["timeout"], 600.0)

    def test_captured_current_request_is_non_streaming(self) -> None:
        captured = capture_current_real_chat_request(model=O.FROZEN_ANSWER_MODEL)
        self.assertIs(captured["record"]["payload"]["stream"], False)
        derived = O.derive_current_canonical_nonstreaming_request_identity()
        self.assertIs(derived["REQUEST"]["STREAM"], False)
        self.assertEqual(O.request_identity_projection(derived)["STREAM"], False)

    def test_captured_request_identity_equals_the_observer_identity(self) -> None:
        captured = capture_current_real_chat_request(model=O.FROZEN_ANSWER_MODEL)
        record = captured["record"]
        captured_identity = {
            "HTTP_ENDPOINT": urlsplit(record["url"]).path,
            "HTTP_METHOD": record["method"],
            "STREAM": record["payload"]["stream"],
            "KEEP_ALIVE": record["payload"]["keep_alive"],
            "OPTIONS": record["payload"]["options"],
        }
        derived = O.derive_current_canonical_nonstreaming_request_identity()
        self.assertEqual(
            captured_identity, O.request_identity_projection(derived)
        )
        self.assertEqual(
            captured_identity["OPTIONS"],
            {
                "temperature": 0,
                "top_p": 1,
                "top_k": 1,
                "repeat_penalty": 1.15,
                "num_predict": 800,
                "num_ctx": 8192,
            },
        )

    def test_captured_payload_keys_equal_the_derived_payload_keys(self) -> None:
        captured = capture_current_real_chat_request(model=O.FROZEN_ANSWER_MODEL)
        derived = O.derive_current_canonical_nonstreaming_request_identity()
        self.assertEqual(
            sorted(captured["record"]["payload"]),
            derived["DERIVATION"]["PAYLOAD_KEY_SET"],
        )
        self.assertEqual(
            derived["DERIVATION"]["SOURCE_PATH"], "core/ollama_http.py"
        )
        self.assertEqual(
            derived["DERIVATION"]["SOURCE_RAW_SHA256"],
            hashlib.sha256(
                (ROOT_DIR / "core" / "ollama_http.py").read_bytes()
            ).hexdigest(),
        )
        self.assertEqual(
            derived["DERIVATION"]["CONFIG_RAW_SHA256"],
            hashlib.sha256(
                (ROOT_DIR / "core" / "config.py").read_bytes()
            ).hexdigest(),
        )

    def test_captured_model_binding_matches_the_source_expression(self) -> None:
        from core import config as config_module

        derived = O.derive_current_canonical_nonstreaming_request_identity()
        self.assertEqual(
            derived["REQUEST"]["MODEL_SOURCE_EXPRESSION"],
            "model or config.ANSWER_MODEL",
        )
        self.assertEqual(
            derived["REQUEST"]["RESOLVED_MODEL_DEFAULT"], config_module.ANSWER_MODEL
        )
        captured_default = capture_current_real_chat_request(model=None)
        self.assertEqual(
            captured_default["record"]["payload"]["model"],
            derived["REQUEST"]["RESOLVED_MODEL_DEFAULT"],
        )
        captured_explicit = capture_current_real_chat_request(
            model="SYNTHETIC_TEST_ONLY_MODEL"
        )
        self.assertEqual(
            captured_explicit["record"]["payload"]["model"],
            "SYNTHETIC_TEST_ONLY_MODEL",
        )

    def test_current_identity_is_compared_to_the_anchor_separately(self) -> None:
        derived = O.derive_current_canonical_nonstreaming_request_identity()
        comparison = O.compare_current_request_identity_to_accepted_frozen_anchor(
            derived
        )
        self.assertEqual(comparison["ROLE"], "ACCEPTED_FROZEN_COMPARISON_ANCHOR")
        self.assertEqual(comparison["ANCHOR_USED_AS_CURRENT_VALUE_SOURCE"], "NO")
        self.assertEqual(comparison["COMPARISON_SEPARATED_FROM_DERIVATION"], "YES")
        self.assertEqual(comparison["DIMENSION_COUNT"], 8)
        self.assertEqual(comparison["MATCH_COUNT"], 8)
        self.assertEqual(
            comparison[
                "CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR"
            ],
            "YES",
        )
        for item in comparison["COMPARISONS"]:
            with self.subTest(field=item["FIELD"]):
                self.assertTrue(item["MATCH"], item)

    def test_derivation_does_not_reference_the_frozen_anchor(self) -> None:
        source = OBSERVER_PATH.read_text(encoding="utf-8")
        derivation_source = _function_source(
            source, "derive_current_canonical_nonstreaming_request_identity"
        )
        self.assertNotIn("ACCEPTED_FROZEN_COMPARISON_ANCHOR", derivation_source)
        self.assertIn("_ollama_chat_request_nodes", derivation_source)
        self.assertIn("REQUEST_IDENTITY_DERIVATION_RULE", derivation_source)
        self.assertEqual(
            O.REQUEST_IDENTITY_DERIVATION_RULE,
            "MECHANICAL_AST_DERIVATION_FROM_CURRENT_SOURCE_PLUS_LIVE_RUNTIME_CONFIG",
        )
        self.assertLess(
            source.index(
                "def derive_current_canonical_nonstreaming_request_identity"
            ),
            source.index(
                "def compare_current_request_identity_to_accepted_frozen_anchor"
            ),
        )

    def test_frozen_anchor_is_corroborated_by_the_historical_evidence(self) -> None:
        artifact = json.loads(
            (
                ROOT_DIR
                / "eval"
                / "v4_8_1_residual_generation_mechanism_isolation.json"
            ).read_text(encoding="utf-8")
        )
        historical = artifact["model_runtime_identity"]["generation_parameters"]
        anchor = O.accepted_frozen_comparison_anchor()
        self.assertEqual(
            O.ACCEPTED_FROZEN_COMPARISON_ANCHOR_ROLE,
            "ACCEPTED_FROZEN_COMPARISON_ANCHOR",
        )
        for field_name in (
            "temperature",
            "top_p",
            "top_k",
            "repeat_penalty",
            "num_predict",
            "num_ctx",
            "keep_alive",
            "stream",
        ):
            with self.subTest(field=field_name):
                self.assertEqual(anchor[field_name], historical[field_name])

    def test_current_request_identity_is_recorded_in_the_synthetic_observation(
        self,
    ) -> None:
        observation = _base_observation()
        identity = observation["generation_input"]["inference_parameter_identity"]
        self.assertEqual(
            identity["method"], "core/ollama_http.py#OllamaClient.chat"
        )
        self.assertEqual(
            identity["identity_source"],
            "MECHANICAL_AST_DERIVATION_FROM_CURRENT_SOURCE_PLUS_LIVE_RUNTIME_CONFIG",
        )
        self.assertEqual(
            identity["CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR"],
            "YES",
        )
        projection = identity["CURRENT_REQUEST_IDENTITY_PROJECTION"]
        self.assertIs(projection["STREAM"], False)
        self.assertEqual(
            projection["HTTP_ENDPOINT"],
            identity["CURRENT_REQUEST_IDENTITY"]["REQUEST"]["HTTP_ENDPOINT"],
        )


# --------------------------------------------------------------------------- #
# 23 G2_EQ1 raw / final answer capture equivalence (witnesses K-L)
# --------------------------------------------------------------------------- #
class G2Eq1RawFinalCaptureTest(unittest.TestCase):
    def test_raw_answer_is_the_direct_canonical_chat_return(self) -> None:
        payload, harness = base_payload_entry()
        self.assertEqual(
            payload["OBSERVATION"]["generation_output"]["raw_model_answer"],
            SYNTHETIC_RAW_ANSWER,
        )
        self.assertNotEqual(SYNTHETIC_RAW_ANSWER, SYNTHETIC_RAW_ANSWER.strip())
        self.assertIs(
            harness.record["chat_calls"][0]["messages"],
            payload["OBSERVATION"]["generation_input"][
                "application_level_model_visible_context"
            ],
        )

    def test_final_answer_is_the_canonical_postprocessed_result(self) -> None:
        payload, harness = base_payload_entry()
        engine = harness.engine_holder["engine"]
        observation = payload["OBSERVATION"]
        final = observation["generation_output"]["final_application_answer"]
        self.assertEqual(final, engine.result.answer)
        normalized, _verified = harness.bindings.engine_v2.normalize_citations(
            SYNTHETIC_RAW_ANSWER, 1
        )
        self.assertIn("[1]", normalized)
        self.assertNotIn("[9]", normalized)
        self.assertNotEqual(final, SYNTHETIC_RAW_ANSWER)

    def test_observer_contains_no_manual_token_joining(self) -> None:
        self.assertEqual(O._empty_string_join_calls(_observer_tree()), 0)
        self.assertEqual(
            O.raw_final_capture_witness()["MANUAL_TOKEN_JOINING_CALLS"], 0
        )
        self.assertEqual(
            O.raw_final_capture_witness()["RAW_FINAL_ANSWER_CAPTURE_EQUIVALENCE"],
            "ESTABLISHED",
        )

    def test_raw_final_capture_witness_reports_the_direct_assignment(self) -> None:
        witness = O.raw_final_capture_witness()
        self.assertEqual(
            witness["RAW_MODEL_ANSWER_DIRECT_FROM_CANONICAL_CHAT"], "YES"
        )
        self.assertEqual(
            witness["FINAL_APPLICATION_ANSWER_FROM_CANONICAL_POSTPROCESSING"],
            "YES",
        )
        self.assertIn(
            witness["RAW_ANSWER_ASSIGNMENT"],
            OBSERVER_PATH.read_text(encoding="utf-8"),
        )


# --------------------------------------------------------------------------- #
# 24 G2_EQ1 full canonical qa semantic sequence witness (witnesses M-O)
# --------------------------------------------------------------------------- #
def _function_source(source: str, name: str) -> str:
    """The source segment of a module-level function (test-only, read-only)."""
    start = source.index("def " + name + "(")
    rest = source[start + 1 :]
    ends = [
        position
        for position in (rest.find("\ndef "), rest.find("\nclass "))
        if position != -1
    ]
    if not ends:
        return source[start:]
    return source[start : start + 1 + min(ends)]


class G2Eq1FullSemanticSequenceTest(unittest.TestCase):
    def test_full_canonical_qa_semantic_sequence_witness_passes(self) -> None:
        witness = O.canonical_qa_semantic_sequence_witness()
        self.assertEqual(
            witness["FULL_CANONICAL_QA_SEMANTIC_SEQUENCE_WITNESS"], "PASS"
        )
        self.assertEqual(witness["ISSUES"], [])
        self.assertEqual(
            witness["CANONICAL_OPERATION_COUNT"],
            len(O.CANONICAL_QA_SEQUENCE_WITNESS),
        )

    def test_every_canonical_marker_exists_in_its_current_source(self) -> None:
        sources = {
            O.CANONICAL_EVALUATOR_PATH: canonical_evaluator_source(),
            "core/engine_v2.py": engine_source(),
        }
        missing = []
        for entry in O.CANONICAL_QA_SEQUENCE_WITNESS:
            source = sources[entry["CANONICAL_PATH"]]
            if entry["CANONICAL_MARKER"] not in source:
                missing.append(entry["OPERATION"])
        self.assertEqual(missing, [])

    def test_canonical_markers_follow_the_declared_source_order(self) -> None:
        witness = O.canonical_qa_semantic_sequence_witness()
        positions = {}
        previous = {}
        for row in witness["WITNESS_ROWS"]:
            self.assertIsNotNone(
                row["CANONICAL_MARKER_POSITION"],
                "canonical marker missing: " + row["OPERATION"],
            )
            path = row["CANONICAL_PATH"]
            position = row["CANONICAL_MARKER_POSITION"]
            if path in previous:
                self.assertGreater(
                    position,
                    previous[path],
                    "%s is out of source order" % row["OPERATION"],
                )
            previous[path] = position
            positions[row["OPERATION"]] = position
        self.assertTrue(positions)

    def test_observer_markers_follow_the_declared_observer_order(self) -> None:
        witness = O.canonical_qa_semantic_sequence_witness()
        previous = -1
        for row in witness["WITNESS_ROWS"]:
            if row["OBSERVER_MARKER_POSITION"] is None:
                continue
            self.assertGreater(
                row["OBSERVER_MARKER_POSITION"],
                previous,
                "%s is out of observer order" % row["OPERATION"],
            )
            previous = row["OBSERVER_MARKER_POSITION"]

    def test_semantic_operations_are_all_preserved(self) -> None:
        witness = O.canonical_qa_semantic_sequence_witness()
        self.assertEqual(witness["MISSING_SEMANTIC_OPERATIONS"], [])
        self.assertEqual(
            witness["ANSWER_WRAPPER_SEMANTIC_OPERATIONS_PRESERVED"], "YES"
        )
        for entry in O.CANONICAL_QA_SEQUENCE_WITNESS:
            if entry["CLASS"] != "SEMANTIC":
                continue
            with self.subTest(operation=entry["OPERATION"]):
                self.assertIsNotNone(entry["OBSERVER_MARKER"])

    def test_observer_sequence_carries_the_required_semantic_operations(
        self,
    ) -> None:
        witness = O.canonical_qa_semantic_sequence_witness()
        observer_operations = witness["OBSERVER_SUPPORTED_QA_SEMANTIC_SEQUENCE"]
        for operation in (
            "history normalization",
            "scope resolution",
            "known document id set",
            "effective allowed document id filter",
            "non-streaming canonical chat generation",
            "citation normalization",
            "citation entity support verification",
            "citation renumbering",
            "deterministic citation verifier",
            "canonical AnswerResultV2 construction",
            "canonical evaluator measurement row",
        ):
            with self.subTest(operation=operation):
                self.assertIn(operation, observer_operations)

    def test_synthetic_run_executes_each_semantic_operation_exactly_once(
        self,
    ) -> None:
        _payload, harness = base_payload_entry()
        record = harness.record
        self.assertEqual(len(record["normalize_history_calls"]), 1)
        self.assertEqual(record["normalize_history_calls"][0]["history"], None)
        self.assertEqual(len(record["prepare_calls"]), 1)
        self.assertEqual(len(record["scope_assertion_calls"]), 2)
        self.assertEqual(len(record["build_messages_calls"]), 1)
        self.assertEqual(len(record["chat_calls"]), 1)
        self.assertEqual(len(record["normalize_citations_calls"]), 1)
        # the synthetic raw answer carries an out-of-range citation, so the
        # canonical `if citation_verified:` guard skips the entity support check
        self.assertEqual(len(record["citation_support_verified_calls"]), 0)
        self.assertEqual(len(record["renumber_citations_calls"]), 1)
        self.assertEqual(len(record["verify_calls"]), 1)
        self.assertEqual(len(record["result_calls"]), 1)
        self.assertEqual(len(record["evaluator_rows"]), 1)

    def test_support_check_runs_on_a_valid_citation_synthetic_answer(self) -> None:
        harness = SyntheticBindings(
            None, " GSM 使用 GMSK 调制[1]。 "
        )
        payload = O.run_live_observation(live_request(), harness.bindings)
        self.assertEqual(payload["STATUS"], "OBSERVED")
        self.assertEqual(len(harness.record["normalize_citations_calls"]), 1)
        self.assertEqual(len(harness.record["citation_support_verified_calls"]), 1)

    def test_only_proven_nonsemantic_wrapper_behavior_is_omitted(self) -> None:
        omissions = O.omitted_canonical_wrapper_behavior()
        self.assertEqual(
            omissions["ONLY_PROVEN_NONSEMANTIC_WRAPPER_BEHAVIOR_OMITTED"], "YES"
        )
        self.assertTrue(omissions["ENTRIES"])
        for item in omissions["ENTRIES"]:
            with self.subTest(behavior=item["BEHAVIOR"]):
                self.assertTrue(
                    str(item["SEMANTIC_OR_NONSEMANTIC"]).startswith("NONSEMANTIC")
                )
                self.assertTrue(item["MECHANICAL_REASON"])

    def test_semantic_classes_and_omission_classes_are_from_the_vocabulary(
        self,
    ) -> None:
        for entry in O.CANONICAL_QA_SEQUENCE_WITNESS:
            with self.subTest(operation=entry["OPERATION"]):
                self.assertIn(entry["CLASS"], ("SEMANTIC", "NONSEMANTIC"))
                if entry["OBSERVER_MARKER"] is None:
                    self.assertIn(
                        entry.get("OMISSION_CLASS"), O.OMISSION_CLASSES
                    )
                else:
                    self.assertNotIn("OMISSION_CLASS", entry)


# --------------------------------------------------------------------------- #
# 25 G2_EQ1 extra read-only capture call accounting (witnesses P-Q)
# --------------------------------------------------------------------------- #
class G2Eq1ExtraReadOnlyCaptureAccountingTest(unittest.TestCase):
    def test_every_extra_call_is_accounted_for(self) -> None:
        accounting = O.extra_read_only_capture_calls()
        self.assertEqual(
            accounting["EXTRA_READ_ONLY_CAPTURE_CALLS_ACCOUNTED_FOR"], "YES"
        )
        self.assertTrue(accounting["CALLS"])
        for item in accounting["CALLS"]:
            with self.subTest(call=item["CALL"]):
                self.assertTrue(item["WITNESS_COMPLETE"])
                self.assertTrue(item["MECHANICAL_WITNESS"])
                self.assertTrue(item["DISPOSITION"])

    def test_every_extra_call_proves_the_read_only_property_bundle(self) -> None:
        for item in O.EXTRA_READ_ONLY_CAPTURE_CALLS:
            with self.subTest(call=item["CALL"]):
                self.assertEqual(item["READ_ONLY"], "YES")
                self.assertEqual(item["IDEMPOTENT_FOR_THIS_STATE"], "YES")
                self.assertEqual(item["NO_RANDOMNESS"], "YES")
                self.assertEqual(item["NO_MODEL_CALL"], "YES")
                self.assertEqual(item["NO_EMBEDDING_CALL"], "YES")
                self.assertEqual(item["NO_RETRIEVAL_SIDE_EFFECT"], "YES")
                self.assertEqual(item["DOES_NOT_MUTATE_STATE"], "YES")
                self.assertEqual(
                    item["DOES_NOT_CHANGE_CANONICAL_RETURN_VALUES"], "YES"
                )
                self.assertEqual(item["DOES_NOT_CHANGE_MODEL_VISIBLE_INPUT"], "YES")

    def test_classification_critical_operations_are_not_duplicated(self) -> None:
        source = OBSERVER_PATH.read_text(encoding="utf-8")
        # G2_EQ4 FIX_1: the live path is one single frame (SAME_FRAME), so the
        # audited live path is exactly that function.
        live_path = "".join(
            _function_source(source, name)
            for name in O.OBSERVER_LIVE_PATH_FUNCTION_NAMES
        )
        self.assertEqual(live_path.count("resolve_scope(None)"), 1)
        self.assertEqual(live_path.count("effective_allowed_ids(resolution)"), 1)
        self.assertEqual(
            live_path.count("known_documents = {record.id for record in"), 1
        )
        self.assertEqual(live_path.count("resolved.chat("), 1)
        self.assertEqual(live_path.count("build_messages("), 1)
        self.assertEqual(live_path.count("normalize_citations("), 1)
        self.assertEqual(live_path.count("citation_support_verified("), 1)
        self.assertEqual(live_path.count("renumber_citations("), 1)
        self.assertEqual(live_path.count("citation_verifier.verify("), 1)
        self.assertEqual(live_path.count("_result("), 1)
        self.assertEqual(live_path.count("_build_row("), 1)

    def test_scope_resolution_mirrors_the_canonical_two_call_shape(self) -> None:
        canonical = engine_source()
        observer_source = OBSERVER_PATH.read_text(encoding="utf-8")
        live_path = "".join(
            _function_source(observer_source, name)
            for name in O.OBSERVER_LIVE_PATH_FUNCTION_NAMES
        )
        # canonical answer() resolves directly and prepare() resolves again
        # internally; the observer mirrors exactly one direct resolution and
        # calls prepare once, so the total resolution count stays equal and no
        # third resolution is introduced.
        self.assertEqual(
            canonical.count("resolution = self.library.resolve_scope(scope)"), 2
        )
        self.assertEqual(
            live_path.count("resolution = engine.library.resolve_scope(None)"), 1
        )
        self.assertIn("resolution = self.library.resolve_scope(scope)", canonical)
        self.assertIn("resolution = engine.library.resolve_scope(None)", live_path)
        self.assertEqual(
            live_path.count("engine.prepare("), 1
        )

    def test_library_read_paths_are_provably_read_only(self) -> None:
        library_source = (ROOT_DIR / "core" / "library_store.py").read_text(
            encoding="utf-8"
        )
        scope_source = (ROOT_DIR / "core" / "query_scope.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("mode=ro", library_source)
        for token in ("INSERT", "UPDATE", "DELETE", "CREATE TABLE", "DROP TABLE"):
            with self.subTest(token=token):
                self.assertNotIn(token, scope_source)
        for item in O.EXTRA_READ_ONLY_CAPTURE_CALLS:
            if "resolve_scope" not in item["CALL"]:
                continue
            self.assertIn("mode=ro", item["MECHANICAL_WITNESS"])
            self.assertIn("SELECT", item["MECHANICAL_WITNESS"])

    def test_classification_critical_operations_audit_reports_single_execution(
        self,
    ) -> None:
        audit = O.classification_critical_operation_audit()
        self.assertEqual(
            audit["DUPLICATED_CLASSIFICATION_CRITICAL_OPERATIONS"], []
        )
        self.assertEqual(audit["DUPLICATED_OPERATIONS_REMOVED_OR_REUSED"], "YES")
        self.assertTrue(audit["OPERATIONS"])
        for item in audit["OPERATIONS"]:
            with self.subTest(operation=item["OPERATION"]):
                self.assertEqual(item["EXECUTIONS_IN_LIVE_PATH"], 1)
                self.assertEqual(item["SINGLE_EXECUTION"], "YES")

    def test_scope_group_uses_the_reused_canonical_values(self) -> None:
        observation = _base_observation()
        scope_block = observation["scope"]
        self.assertEqual(scope_block["requested_scope"], None)
        self.assertEqual(
            scope_block["effective_scope"]["mode"], "default"
        )
        self.assertEqual(
            scope_block["effective_scope"]["effective_allowed_ids_mode"],
            "WHOLE_LIBRARY",
        )


# --------------------------------------------------------------------------- #
# 26 G2_EQ1 zero real call boundary (witness R)
# --------------------------------------------------------------------------- #
class G2Eq1ZeroRealCallTest(unittest.TestCase):
    def test_g2_eq1_suites_trigger_no_real_call_boundary(self) -> None:
        self.assertEqual(_REAL_CALL_ATTEMPTS, [])

    def test_static_modes_report_zero_counters_for_the_correction(self) -> None:
        contract = O.describe_contract()
        for field_name in O.COUNTER_FIELDS:
            self.assertEqual(contract["counters"][field_name], 0)
        self.assertEqual(contract["MODEL_CALLS"], 0)
        self.assertEqual(contract["EMBEDDING_CALLS"], 0)
        self.assertEqual(contract["PRODUCTION_RETRIEVAL_RUNS"], 0)
        self.assertEqual(contract["TARGET_OBSERVATION_RUNS"], 0)

    def test_capture_helper_performs_zero_network_calls(self) -> None:
        captured = capture_current_real_chat_request(model=O.FROZEN_ANSWER_MODEL)
        self.assertEqual(captured["sentinel"].interceptions, 1)
        self.assertEqual(len(captured["sentinel"].records), 1)
        self.assertEqual(_REAL_CALL_ATTEMPTS, [])

    def test_required_correction_assertion_block_reports_the_frozen_values(
        self,
    ) -> None:
        assertions = O.required_correction_assertions()
        self.assertEqual(assertions["REQUIRED_FIX_COUNT"], 3)
        self.assertEqual(
            assertions["FIX_1_CANONICAL_MEASUREMENT_TIMER_BOUNDARY"], "PASS"
        )
        self.assertEqual(
            assertions["FIX_2_REQUEST_IDENTITY_BOOLEAN_SEMANTICS"], "PASS"
        )
        self.assertEqual(
            assertions["FIX_3_CANONICAL_PIPELINE_GENERATION_BINDING"], "PASS"
        )
        self.assertEqual(
            assertions["FIX_A_NONSTREAMING_CANONICAL_EVALUATOR_BRANCH"], "PASS"
        )
        self.assertEqual(assertions["FIX_B_CURRENT_REQUEST_IDENTITY"], "PASS")
        for field_name in (
            "CANONICAL_EVALUATOR_NO_ON_TOKEN_WITNESS",
            "ENGINE_ON_TOKEN_NONE_SELECTS_CHAT",
            "ENGINE_ON_TOKEN_NONE_DOES_NOT_SELECT_CHAT_STREAM",
            "ENGINE_RESULT_TIMER_START_MECHANICALLY_DERIVED",
            "ENGINE_RESULT_TIMER_END_MECHANICALLY_DERIVED",
            "EVALUATOR_ROW_TIMER_START_MECHANICALLY_DERIVED",
            "EVALUATOR_ROW_TIMER_END_MECHANICALLY_DERIVED",
            "ENGINE_CONSTRUCTION_TIMER_RELATION_ACCOUNTED_FOR",
            "ANSWER_RESULT_ELAPSED_MS_BOUND_TO_CANONICAL_ENGINE_TIMER",
            "EVALUATOR_OUTPUT_ELAPSED_MS_BOUND_TO_CANONICAL_EVALUATOR_TIMER",
            "ACTIVE_GENERATION_BINDING_MATCHES_CANONICAL_EVALUATOR_BRANCH_WITNESS",
            "CURRENT_REQUEST_IDENTITY_DERIVED_FROM_CURRENT_SOURCE_RUNTIME",
            "CURRENT_REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT",
            "INFERENCE_PARAMETER_TEMPERATURE_BOUND",
            "INFERENCE_PARAMETER_TOP_P_BOUND",
            "INFERENCE_PARAMETER_TOP_K_BOUND",
            "INFERENCE_PARAMETER_REPEAT_PENALTY_BOUND",
            "INFERENCE_PARAMETER_NUM_PREDICT_BOUND",
            "INFERENCE_PARAMETER_NUM_CTX_BOUND",
            "INFERENCE_PARAMETER_KEEP_ALIVE_BOUND",
            "INFERENCE_PARAMETER_STREAM_BOUND",
            "CURRENT_REQUEST_STREAM_IS_FALSE",
            "CURRENT_REQUEST_IDENTITY_COMPATIBLE_WITH_ACCEPTED_FROZEN_ANCHOR",
            "RAW_MODEL_ANSWER_DIRECT_FROM_CANONICAL_CHAT",
            "FINAL_APPLICATION_ANSWER_FROM_CANONICAL_POSTPROCESSING",
            "ANSWER_WRAPPER_SEMANTIC_OPERATIONS_PRESERVED",
            "ONLY_PROVEN_NONSEMANTIC_WRAPPER_BEHAVIOR_OMITTED",
            "EXTRA_READ_ONLY_CAPTURE_CALLS_ACCOUNTED_FOR",
            "OBSERVATION_EQUIVALENCE_ESTABLISHED_BY_STATIC_SYNTHETIC_G2_TESTS",
        ):
            with self.subTest(assertion=field_name):
                self.assertEqual(assertions[field_name], "YES")
        self.assertEqual(
            assertions["RAW_FINAL_ANSWER_CAPTURE_EQUIVALENCE"], "ESTABLISHED"
        )
        self.assertEqual(
            assertions["FULL_CANONICAL_QA_SEMANTIC_SEQUENCE_WITNESS"], "PASS"
        )
        self.assertEqual(assertions["MISSING_SEMANTIC_OPERATIONS"], [])
        self.assertEqual(assertions["OBSERVER_DEFAULT_MODEL_CALL"], "OllamaClient.chat")
        self.assertEqual(
            assertions["OBSERVER_STREAMING_GENERATION_BRANCH_REMOVED"], "YES"
        )

    def test_live_envelope_reports_the_correction_blocks(self) -> None:
        payload = base_payload()
        self.assertEqual(
            payload["OBSERVER_DEFAULT_MODEL_CALL"], "OllamaClient.chat"
        )
        self.assertEqual(
            payload["OBSERVER_STREAMING_GENERATION_BRANCH_REMOVED"], "YES"
        )
        self.assertEqual(
            payload["CANONICAL_NONSTREAMING_CHAT_METHOD"],
            "core/ollama_http.py#OllamaClient.chat",
        )
        self.assertEqual(
            payload["CANONICAL_GENERATION_BRANCH"][
                "FIX_A_NONSTREAMING_CANONICAL_EVALUATOR_BRANCH"
            ],
            "PASS",
        )
        self.assertEqual(
            payload["FULL_CANONICAL_QA_SEMANTIC_SEQUENCE"][
                "FULL_CANONICAL_QA_SEMANTIC_SEQUENCE_WITNESS"
            ],
            "PASS",
        )
        self.assertEqual(
            payload["OMITTED_CANONICAL_WRAPPER_BEHAVIOR"][
                "ONLY_PROVEN_NONSEMANTIC_WRAPPER_BEHAVIOR_OMITTED"
            ],
            "YES",
        )
        self.assertEqual(
            payload["EXTRA_READ_ONLY_CAPTURE_CALLS"][
                "EXTRA_READ_ONLY_CAPTURE_CALLS_ACCOUNTED_FOR"
            ],
            "YES",
        )
        self.assertEqual(
            payload["CANONICAL_GENERATION_BRANCH"][
                "ENGINE_ON_TOKEN_NONE_DOES_NOT_SELECT_CHAT_STREAM"
            ],
            "YES",
        )
        self.assertEqual(
            payload["CANONICAL_MEASUREMENT_TIMER_BOUNDARY"][
                "CANONICAL_MEASUREMENT_TIMER_BOUNDARY_EQUIVALENCE"
            ],
            "PASS",
        )
        self.assertEqual(
            payload["FULL_CANONICAL_QA_SEMANTIC_SEQUENCE"][
                "CANONICAL_MEASUREMENT_TIMER_BOUNDARY_EQUIVALENCE"
            ],
            "PASS",
        )
        binding_map = payload["SOURCE_BINDING_MAP"]
        self.assertEqual(
            binding_map["ACTIVE_CANONICAL_GENERATION_BINDING"], "OllamaClient.chat"
        )
        self.assertEqual(
            binding_map["ACTIVE_CANONICAL_PIPELINE_CONTAINS_CHAT_STREAM"], "NO"
        )
        self.assertEqual(
            binding_map["ACTIVE_GENERATION_BINDING_MATCHES_CANONICAL_EVALUATOR_BRANCH_WITNESS"],
            "YES",
        )


# --------------------------------------------------------------------------- #
# 27 G2_EQ2 canonical measurement timer boundary equivalence (FIX_1)
# --------------------------------------------------------------------------- #
class _DeterministicPerfCounter:
    """Test-only deterministic ``time.perf_counter`` sequence (no real clock).

    Every read returns the next declared value; an unexpected extra read fails
    loudly instead of silently reusing a value, so the tests can prove exactly
    how many canonical timer reads the observer performs and in which order.
    """

    def __init__(self, ticks: list[float]) -> None:
        self._ticks = list(ticks)
        self.calls: list[float] = []

    def __call__(self) -> float:
        if len(self.calls) >= len(self._ticks):
            raise AssertionError(
                "deterministic clock exhausted: unexpected canonical timer "
                "read #%d" % (len(self.calls) + 1)
            )
        value = self._ticks[len(self.calls)]
        self.calls.append(value)
        return value


class G2Eq2CanonicalMeasurementTimerBoundaryTest(unittest.TestCase):
    def test_engine_result_timer_start_source_is_mechanically_derived(self) -> None:
        witness = O.canonical_measurement_timer_boundary_witness()
        engine_timer = witness["CANONICAL_ENGINE_RESULT_TIMER"]
        self.assertEqual(
            engine_timer["START_STATEMENT_EXPRESSION"], "time.perf_counter()"
        )
        self.assertEqual(
            engine_timer["START_IS_FIRST_EXECUTED_ANSWER_STATEMENT"], "YES"
        )
        self.assertEqual(
            witness["ENGINE_RESULT_TIMER_START_MECHANICALLY_DERIVED"], "YES"
        )
        self.assertIn("started = time.perf_counter()", engine_source())
        tree = ast.parse(engine_source())
        answer_functions = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "answer"
        ]
        self.assertTrue(answer_functions)
        first_statement = answer_functions[0].body[0]
        self.assertIsInstance(first_statement, ast.Assign)
        self.assertEqual(
            _dotted_name(first_statement.value.func), "time.perf_counter"
        )

    def test_engine_result_timer_end_result_witness(self) -> None:
        witness = O.canonical_measurement_timer_boundary_witness()
        engine_timer = witness["CANONICAL_ENGINE_RESULT_TIMER"]
        self.assertEqual(
            engine_timer["END_EXPRESSION"],
            "round((time.perf_counter() - started) * 1000)",
        )
        self.assertEqual(
            engine_timer["ELAPSED_CONSUMER"],
            "core/engine_v2.py#AnswerResultV2.elapsed_ms",
        )
        self.assertEqual(
            witness["ENGINE_RESULT_TIMER_END_MECHANICALLY_DERIVED"], "YES"
        )
        source = engine_source()
        self.assertIn(
            "elapsed_ms=round((time.perf_counter() - started) * 1000)", source
        )
        self.assertIn("elapsed_ms: int", source)
        self.assertIn("ANSWER_RESULT_ELAPSED_MS_BOUND_TO_CANONICAL_ENGINE_TIMER", witness)

    def test_evaluator_row_timer_start_source_is_mechanically_derived(self) -> None:
        witness = O.canonical_measurement_timer_boundary_witness()
        evaluator_timer = witness["CANONICAL_EVALUATOR_ROW_TIMER"]
        self.assertEqual(
            evaluator_timer["START_STATEMENT_EXPRESSION"], "time.perf_counter()"
        )
        self.assertEqual(
            witness["EVALUATOR_ROW_TIMER_START_MECHANICALLY_DERIVED"], "YES"
        )
        source = canonical_evaluator_source()
        self.assertIn("case_started = time.perf_counter()", source)
        self.assertLess(
            source.index(
                "engine = StructuredQAEngine(library_path=args.library)"
            ),
            source.index("case_started = time.perf_counter()"),
        )
        self.assertLess(
            source.index("case_started = time.perf_counter()"),
            source.index('result = engine.answer(case["query"]'),
        )

    def test_evaluator_row_timer_end_build_row_witness(self) -> None:
        witness = O.canonical_measurement_timer_boundary_witness()
        evaluator_timer = witness["CANONICAL_EVALUATOR_ROW_TIMER"]
        self.assertEqual(
            evaluator_timer["END_EXPRESSION"],
            "round((time.perf_counter() - case_started) * 1000)",
        )
        self.assertEqual(
            evaluator_timer["ROW_BUILDER_RECEIVES_ELAPSED_VARIABLE"], "elapsed_ms"
        )
        self.assertEqual(
            witness["EVALUATOR_ROW_TIMER_END_MECHANICALLY_DERIVED"], "YES"
        )
        self.assertIn(
            "cache[key] = _build_row(case, result, elapsed_ms)",
            canonical_evaluator_source(),
        )
        self.assertEqual(
            witness["EVALUATOR_OUTPUT_ELAPSED_MS_BOUND_TO_CANONICAL_EVALUATOR_TIMER"],
            "YES",
        )

    def test_engine_construction_excluded_or_included_exactly_as_source_requires(
        self,
    ) -> None:
        witness = O.canonical_measurement_timer_boundary_witness()
        engine_timer = witness["CANONICAL_ENGINE_RESULT_TIMER"]
        evaluator_timer = witness["CANONICAL_EVALUATOR_ROW_TIMER"]
        self.assertEqual(engine_timer["ENGINE_CONSTRUCTION_INSIDE_ANSWER"], "NO")
        self.assertEqual(
            engine_timer["ENGINE_CONSTRUCTION_RELATIVE_TO_ENGINE_TIMER"], "AFTER"
        )
        self.assertEqual(
            evaluator_timer["ENGINE_CONSTRUCTION_BEFORE_EVALUATOR_TIMER_START"],
            "YES",
        )
        self.assertEqual(
            witness["ENGINE_CONSTRUCTION_TIMER_RELATION_ACCOUNTED_FOR"], "YES"
        )
        observer = witness["OBSERVER_TIMER_BOUNDARIES"]
        self.assertEqual(
            observer["ENGINE_CONSTRUCTION_BEFORE_BOTH_CANONICAL_TIMERS"], "YES"
        )
        source = OBSERVER_PATH.read_text(encoding="utf-8")
        self.assertLess(
            source.index(O.OBSERVER_ENGINE_CONSTRUCTION_MARKER),
            source.index(O.OBSERVER_EVALUATOR_TIMER_START_MARKER),
        )
        self.assertLess(
            source.index(O.OBSERVER_ENGINE_CONSTRUCTION_MARKER),
            source.index(O.OBSERVER_ENGINE_TIMER_START_MARKER),
        )

    def test_observer_engine_result_interval_matches_canonical(self) -> None:
        witness = O.canonical_measurement_timer_boundary_witness()
        observer = witness["OBSERVER_TIMER_BOUNDARIES"]
        self.assertEqual(
            observer["RESULT_CONSUMER_TIMER_ARGUMENT"],
            O.OBSERVER_ENGINE_TIMER_VARIABLE,
        )
        self.assertEqual(observer["RESULT_CONSUMER_RECEIVES_ENGINE_TIMER"], "YES")
        self.assertEqual(observer["ENGINE_TIMER_START_BEFORE_RESULT_CONSUMPTION"], "YES")
        self.assertEqual(
            witness["CANONICAL_EVALUATOR_ROW_TIMER"][
                "ROW_BUILDER_RECEIVES_ELAPSED_VARIABLE"
            ],
            "elapsed_ms",
        )
        self.assertEqual(witness["ENGINE_RESULT_TIMER_BOUNDARY_EQUIVALENCE"], "PASS")
        self.assertEqual(
            witness["CANONICAL_MEASUREMENT_TIMER_BOUNDARY_EQUIVALENCE"], "PASS"
        )

    def test_observer_evaluator_row_interval_matches_canonical(self) -> None:
        witness = O.canonical_measurement_timer_boundary_witness()
        observer = witness["OBSERVER_TIMER_BOUNDARIES"]
        self.assertEqual(
            observer["ROW_BUILDER_ELAPSED_ARGUMENT"],
            O.OBSERVER_EVALUATOR_ELAPSED_VARIABLE,
        )
        self.assertEqual(observer["ROW_BUILDER_RECEIVES_EVALUATOR_ELAPSED"], "YES")
        self.assertEqual(observer["EVALUATOR_TIMER_START_BEFORE_ENGINE_TIMER_START"], "YES")
        self.assertEqual(observer["EVALUATOR_TIMER_END_AFTER_RESULT_CONSUMPTION"], "YES")
        self.assertEqual(observer["EVALUATOR_TIMER_END_BEFORE_MEASUREMENT_ROW"], "YES")
        self.assertEqual(
            observer["OBSERVER_ONLY_CAPTURE_CALLS_INSIDE_TIMER_INTERVALS"], "NONE"
        )
        self.assertEqual(observer["OBSERVER_TIMER_IDENTITIES_ARE_DISTINCT"], "YES")
        self.assertEqual(witness["EVALUATOR_ROW_TIMER_BOUNDARY_EQUIVALENCE"], "PASS")

    def test_deterministic_clock_proves_intervals_are_not_conflated(self) -> None:
        # G2_EQ4 FIX_3: the mirrored canonical telemetry payload contains the
        # canonical `round((time.perf_counter() - started) * 1000)` read, so the
        # mirrored engine interval performs exactly the same timer reads as the
        # canonical reference (start, telemetry elapsed, _result elapsed).
        clock = _DeterministicPerfCounter([10.0, 20.0, 22.0, 25.0, 31.0])
        harness = SyntheticBindings(clock=clock)
        with unittest.mock.patch.object(O.time, "perf_counter", clock):
            payload = O.run_live_observation(live_request(), harness.bindings)
        self.assertEqual(payload["STATUS"], "OBSERVED")
        self.assertEqual(clock.calls, [10.0, 20.0, 22.0, 25.0, 31.0])
        self.assertEqual(
            harness.record["engine_construction_clock_call_counts"], [0]
        )
        self.assertEqual(
            harness.record["result_calls"][0]["engine_timer_started"], 20.0
        )
        engine_elapsed = harness.record["result_calls"][0][
            "engine_result_elapsed_ms"
        ]
        row = payload["OBSERVATION"]["measurement"]["evaluator_output"]
        self.assertEqual(engine_elapsed, round((25.0 - 20.0) * 1000))
        self.assertEqual(row["elapsed_ms"], round((31.0 - 10.0) * 1000))
        self.assertNotEqual(row["elapsed_ms"], engine_elapsed)
        self.assertEqual(
            harness.record["telemetry_calls"][0]["elapsed_ms"],
            round((22.0 - 20.0) * 1000),
        )

    def test_answer_result_elapsed_ms_comes_from_the_engine_timer(self) -> None:
        clock = _DeterministicPerfCounter([100.0, 200.0, 220.0, 250.0, 400.0])
        harness = SyntheticBindings(clock=clock)
        with unittest.mock.patch.object(O.time, "perf_counter", clock):
            payload = O.run_live_observation(live_request(), harness.bindings)
        result = harness.engine_holder["engine"].result
        self.assertEqual(result.elapsed_ms, round((250.0 - 200.0) * 1000))
        self.assertEqual(
            result.elapsed_ms,
            harness.record["result_calls"][0]["engine_result_elapsed_ms"],
        )
        row = payload["OBSERVATION"]["measurement"]["evaluator_output"]
        self.assertNotEqual(result.elapsed_ms, row["elapsed_ms"])
        self.assertEqual(row["elapsed_ms"], round((400.0 - 100.0) * 1000))

    def test_evaluator_output_elapsed_ms_comes_from_the_evaluator_timer(self) -> None:
        clock = _DeterministicPerfCounter([1.0, 2.0, 2.5, 3.0, 7.0])
        harness = SyntheticBindings(clock=clock)
        with unittest.mock.patch.object(O.time, "perf_counter", clock):
            payload = O.run_live_observation(live_request(), harness.bindings)
        row = payload["OBSERVATION"]["measurement"]["evaluator_output"]
        self.assertEqual(row["elapsed_ms"], round((7.0 - 1.0) * 1000))
        self.assertEqual(
            row["elapsed_ms"],
            harness.record["evaluator_rows"][0]["elapsed_ms"],
        )
        self.assertNotEqual(
            row["elapsed_ms"],
            harness.record["result_calls"][0]["engine_result_elapsed_ms"],
        )

    def test_full_semantic_witness_fails_when_timer_boundaries_are_shifted(self) -> None:
        source = OBSERVER_PATH.read_text(encoding="utf-8")
        construction_line = (
            "    engine = resolved.engine_factory(ROOT_DIR / "
            "RUNTIME_DB_RELATIVE_PATH)\n"
        )
        evaluator_line = "    evaluator_started = time.perf_counter()\n"
        engine_line = "    engine_started = time.perf_counter()\n"
        self.assertEqual(source.count(construction_line), 1)
        self.assertEqual(source.count(evaluator_line), 1)
        self.assertEqual(source.count(engine_line), 1)
        shifted = source.replace(construction_line, "", 1)
        shifted = shifted.replace(engine_line, "", 1)
        shifted = shifted.replace(
            evaluator_line, engine_line + construction_line + evaluator_line, 1
        )
        self.assertNotEqual(shifted, source)
        boundary = O.canonical_measurement_timer_boundary_witness(
            observer_source=shifted
        )
        self.assertEqual(
            boundary["CANONICAL_MEASUREMENT_TIMER_BOUNDARY_EQUIVALENCE"],
            O.CANONICAL_MEASUREMENT_TIMER_BOUNDARY_DRIFT_STATUS,
        )
        self.assertEqual(
            boundary["ENGINE_RESULT_TIMER_BOUNDARY_EQUIVALENCE"], "FAIL"
        )
        self.assertTrue(boundary["ISSUES"])
        full = O.canonical_qa_semantic_sequence_witness(observer_source=shifted)
        self.assertEqual(
            full["FULL_CANONICAL_QA_SEMANTIC_SEQUENCE_WITNESS"], "FAIL"
        )
        self.assertEqual(full["ANSWER_WRAPPER_SEMANTIC_OPERATIONS_PRESERVED"], "NO")
        self.assertEqual(
            O.canonical_qa_semantic_sequence_witness()[
                "FULL_CANONICAL_QA_SEMANTIC_SEQUENCE_WITNESS"
            ],
            "PASS",
        )

    def test_observer_timer_reads_are_exactly_the_canonical_timer_reads(self) -> None:
        clock = _DeterministicPerfCounter([0.0, 1.0, 2.0, 3.0, 4.0])
        harness = SyntheticBindings(clock=clock)
        with unittest.mock.patch.object(O.time, "perf_counter", clock):
            O.run_live_observation(live_request(), harness.bindings)
        self.assertEqual(len(clock.calls), 5)
        source = OBSERVER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)

        def _perf_counter_calls(node: ast.AST) -> int:
            return len(
                [
                    item
                    for item in ast.walk(node)
                    if isinstance(item, ast.Call)
                    and isinstance(item.func, ast.Attribute)
                    and _dotted_name(item.func) == "time.perf_counter"
                ]
            )

        live_path_calls = 0
        for name in O.OBSERVER_LIVE_PATH_FUNCTION_NAMES:
            function = [
                node
                for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == name
            ][0]
            live_path_calls += _perf_counter_calls(function)
        # Canonical reference: the engine-result timer start, the canonical
        # telemetry payload elapsed read, the canonical _result elapsed read and
        # the two canonical evaluator-row timer reads.
        canonical_source = O.governed_source_text(O.ENGINE_V2_PATH)
        canonical_tree = ast.parse(canonical_source)
        canonical_answer = [
            node
            for node in ast.walk(canonical_tree)
            if isinstance(node, ast.FunctionDef) and node.name == "answer"
        ][0]
        canonical_result = [
            node
            for node in ast.walk(canonical_tree)
            if isinstance(node, ast.FunctionDef) and node.name == "_result"
        ][0]
        # The canonical engine interval performs the timer start read and the
        # canonical telemetry payload read; the canonical result consumption
        # performs its own elapsed read.
        engine_interval_reads = _perf_counter_calls(canonical_answer)
        result_consumption_reads = _perf_counter_calls(canonical_result)
        self.assertEqual(engine_interval_reads, 2)
        self.assertEqual(result_consumption_reads, 1)
        # The canonical evaluator row interval performs exactly two reads: its
        # timer start and its elapsed-calculation read.
        evaluator_source = O.governed_source_text(O.CANONICAL_EVALUATOR_PATH)
        row_start = evaluator_source.index(
            O.CANONICAL_EVALUATOR_TIMER_START_MARKER
        )
        row_end = evaluator_source.index(O.CANONICAL_EVALUATOR_TIMER_END_MARKER) + len(
            O.CANONICAL_EVALUATOR_TIMER_END_MARKER
        )
        evaluator_row_reads = evaluator_source[row_start:row_end].count(
            "time.perf_counter()"
        )
        self.assertEqual(evaluator_row_reads, 2)
        canonical_runtime_reads = (
            engine_interval_reads + result_consumption_reads + evaluator_row_reads
        )
        self.assertEqual(canonical_runtime_reads, len(clock.calls))
        # The observer live path performs every canonical timer read except the
        # canonical result-consumption read, which the canonical _result seam
        # performs itself at runtime.
        self.assertEqual(
            live_path_calls, canonical_runtime_reads - result_consumption_reads
        )


# --------------------------------------------------------------------------- #
# 28 G2_EQ2 request identity boolean semantics (FIX_2)
# --------------------------------------------------------------------------- #
class G2Eq2RequestIdentityBooleanSemanticsTest(unittest.TestCase):
    @staticmethod
    def _identity_return_dict() -> ast.Dict:
        tree = _observer_tree()
        functions = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "derive_current_canonical_nonstreaming_request_identity"
        ]
        if not functions:
            raise AssertionError("identity derivation function not found")
        returns = [
            node for node in ast.walk(functions[0]) if isinstance(node, ast.Return)
        ]
        if not returns or not isinstance(returns[-1].value, ast.Dict):
            raise AssertionError("identity return literal dict not found")
        return returns[-1].value

    def test_current_request_identity_not_copied_field_is_yes(self) -> None:
        identity = O.derive_current_canonical_nonstreaming_request_identity()
        self.assertEqual(
            identity["REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT"],
            "YES",
        )
        self.assertEqual(
            identity["REQUEST_IDENTITY_DERIVED_FROM_CURRENT_SOURCE_RUNTIME"],
            "YES",
        )
        self.assertEqual(
            identity["REQUEST_IDENTITY_ACQUISITION_MODE"],
            "DERIVED_FROM_CURRENT_SOURCE_RUNTIME",
        )
        assertions = O.required_correction_assertions()
        self.assertEqual(
            assertions["CURRENT_REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT"],
            "YES",
        )

    def test_current_request_identity_copied_field_is_no(self) -> None:
        identity = O.derive_current_canonical_nonstreaming_request_identity()
        self.assertEqual(
            identity["REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT"], "NO"
        )
        self.assertEqual(O.REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT, "NO")
        self.assertNotEqual(
            identity["REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT"],
            identity["REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT"],
        )
        assertions = O.required_correction_assertions()
        self.assertEqual(
            assertions["CURRENT_REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT"],
            "NO",
        )
        self.assertEqual(
            assertions["FIX_2_REQUEST_IDENTITY_BOOLEAN_SEMANTICS"], "PASS"
        )

    def test_observation_semantic_record_carries_the_correct_polarity(self) -> None:
        observation = _base_observation()
        identity = observation["generation_input"]["inference_parameter_identity"][
            "CURRENT_REQUEST_IDENTITY"
        ]
        self.assertEqual(
            identity["REQUEST_IDENTITY_DERIVED_FROM_CURRENT_SOURCE_RUNTIME"], "YES"
        )
        self.assertEqual(
            identity["REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT"], "YES"
        )
        self.assertEqual(
            identity["REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT"], "NO"
        )

    def test_copied_key_is_bound_to_the_copied_constant_only(self) -> None:
        dictionary = self._identity_return_dict()
        values = {
            key.value: value
            for key, value in zip(dictionary.keys, dictionary.values)
            if isinstance(key, ast.Constant)
        }
        self.assertIn(
            "REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT", values
        )
        self.assertEqual(
            _dotted_name(values["REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT"]),
            "REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT",
        )
        self.assertEqual(
            _dotted_name(
                values["REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT"]
            ),
            "REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT",
        )
        self.assertNotEqual(
            _dotted_name(values["REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT"]),
            _dotted_name(
                values["REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT"]
            ),
        )
        self.assertEqual(
            O.REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT, "YES"
        )


# --------------------------------------------------------------------------- #
# 29 G2_EQ2 canonical pipeline generation binding (FIX_3)
# --------------------------------------------------------------------------- #
class G2Eq2CanonicalPipelineGenerationBindingTest(unittest.TestCase):
    def test_active_canonical_binding_contains_ollama_client_chat(self) -> None:
        active = [
            (path, symbol, role)
            for path, symbol, role in O.CANONICAL_PIPELINE_BINDINGS
            if role == O.CANONICAL_PIPELINE_GENERATION_BINDING_ROLE
        ]
        self.assertEqual(
            active,
            [
                (
                    "core/ollama_http.py",
                    "OllamaClient.chat",
                    O.CANONICAL_PIPELINE_GENERATION_BINDING_ROLE,
                )
            ],
        )
        self.assertEqual(O.ACTIVE_CANONICAL_GENERATION_BINDING, "OllamaClient.chat")
        self.assertEqual(
            O.CANONICAL_PIPELINE_GENERATION_BINDING_ROLE,
            "canonical evaluator non-streaming answer-model call",
        )
        binding_map = O.check_source_binding_map()
        self.assertTrue(binding_map["COMPLETE"])
        self.assertEqual(
            binding_map["ACTIVE_CANONICAL_GENERATION_BINDING"], "OllamaClient.chat"
        )
        self.assertEqual(
            binding_map["ACTIVE_CANONICAL_GENERATION_BINDING_STATUS"], "YES"
        )
        from core import ollama_http

        self.assertTrue(hasattr(ollama_http.OllamaClient, "chat"))

    def test_active_canonical_binding_excludes_chat_stream(self) -> None:
        self.assertEqual(O.ACTIVE_CANONICAL_PIPELINE_CONTAINS_CHAT_STREAM, "NO")
        self.assertFalse(
            [
                symbol
                for _path, symbol, _role in O.CANONICAL_PIPELINE_BINDINGS
                if "chat_stream" in symbol
            ]
        )
        binding_map = O.check_source_binding_map()
        self.assertEqual(
            binding_map["ACTIVE_CANONICAL_PIPELINE_CONTAINS_CHAT_STREAM"], "NO"
        )
        self.assertEqual(
            binding_map["ACTIVE_CANONICAL_PIPELINE_CHAT_STREAM_SYMBOLS"], []
        )
        contract = O.describe_contract()
        self.assertEqual(
            contract["active_canonical_pipeline_contains_chat_stream"], "NO"
        )
        self.assertNotIn(
            "chat_stream", json.dumps(contract["canonical_pipeline_bindings"])
        )

    def test_chat_stream_is_only_labelled_alternative_callback_branch(self) -> None:
        self.assertEqual(
            O.ALTERNATIVE_STREAMING_CALLBACK_BRANCH, "OllamaClient.chat_stream"
        )
        self.assertEqual(
            O.ALTERNATIVE_STREAMING_CALLBACK_BRANCH_LABEL,
            "ALTERNATIVE_STREAMING_CALLBACK_BRANCH",
        )
        self.assertEqual(
            O.ALTERNATIVE_STREAMING_CALLBACK_BRANCH_DISPOSITION,
            "NOT_ACTIVE_CANONICAL_EVALUATOR_GENERATION_BINDING",
        )
        self.assertEqual(
            O.NON_ACTIVE_CANONICAL_BRANCHES,
            (
                (
                    "core/ollama_http.py",
                    "OllamaClient.chat_stream",
                    "ALTERNATIVE_STREAMING_CALLBACK_BRANCH",
                ),
            ),
        )
        branch = O.canonical_evaluator_generation_branch_witness()
        self.assertEqual(
            branch["CHAT_STREAM_BRANCH_IS_ALTERNATIVE_CALLBACK_PATH"], "YES"
        )
        self.assertEqual(
            branch["ENGINE_ON_TOKEN_NONE_DOES_NOT_SELECT_CHAT_STREAM"], "YES"
        )
        self.assertEqual(
            [
                node
                for node in _call_nodes(_observer_tree())
                if _callable_name(node.func) == "chat_stream"
            ],
            [],
        )
        self.assertEqual(O.OBSERVER_STREAMING_GENERATION_BRANCH_REMOVED, "YES")

    def test_binding_map_agrees_with_the_canonical_evaluator_branch_witness(
        self,
    ) -> None:
        binding_map = O.check_source_binding_map()
        branch = O.canonical_evaluator_generation_branch_witness()
        self.assertEqual(
            binding_map[
                "CANONICAL_EVALUATOR_BRANCH_WITNESS_AGREES_WITH_ACTIVE_BINDING"
            ],
            "YES",
        )
        self.assertEqual(
            binding_map[
                "ACTIVE_GENERATION_BINDING_MATCHES_CANONICAL_EVALUATOR_BRANCH_WITNESS"
            ],
            "YES",
        )
        self.assertEqual(branch["ENGINE_ON_TOKEN_NONE_SELECTS_CHAT"], "YES")
        self.assertEqual(
            branch["FIX_A_NONSTREAMING_CANONICAL_EVALUATOR_BRANCH"], "PASS"
        )
        assertions = O.required_correction_assertions()
        self.assertEqual(
            assertions["FIX_3_CANONICAL_PIPELINE_GENERATION_BINDING"], "PASS"
        )
        self.assertEqual(
            assertions["ACTIVE_CANONICAL_GENERATION_BINDING"], "OllamaClient.chat"
        )
        self.assertEqual(
            assertions["ACTIVE_CANONICAL_PIPELINE_CONTAINS_CHAT_STREAM"], "NO"
        )


# --------------------------------------------------------------------------- #
# 30-33 G2_EQ3 canonical measurement timed-body purity (FIX_1)
# --------------------------------------------------------------------------- #
OBSERVER_ENGINE_START_LINE = "    engine_started = time.perf_counter()\n"
OBSERVER_EVALUATOR_START_LINE = "    evaluator_started = time.perf_counter()\n"
OBSERVER_CONSTRUCTION_LINE = (
    "    engine = resolved.engine_factory(ROOT_DIR / RUNTIME_DB_RELATIVE_PATH)\n"
)
OBSERVER_PREPARE_LINE = '    prepared = engine.prepare(case["query"], history, None)\n'
OBSERVER_RESOLUTION_LINE = "    resolution = engine.library.resolve_scope(None)\n"
OBSERVER_GENERATION_LINE = (
    "                    raw_answer = resolved.chat(engine.ollama, messages, "
    "engine.answer_model)\n"
)
OBSERVER_EVALUATOR_END_LINE = (
    "    evaluator_elapsed_ms = round((time.perf_counter() - "
    "evaluator_started) * 1000)\n"
)
OBSERVER_RESULT_CALL_LINE = "            result = engine._result(\n"
OBSERVER_MODEL_LOCK_LINE = "            with engine._model_lock:\n"
OBSERVER_TELEMETRY_CALL_LINE = "            resolved.engine_v2.write_telemetry(\n"
OBSERVER_TELEMETRY_BLOCK_END_LINE = "            )\n"
OBSERVER_ROW_LINE = (
    "        row = resolved.evaluator._build_row(case, result, "
    "evaluator_elapsed_ms)\n"
)
OBSERVER_ROW_LINE_BARE = (
    "    row = resolved.evaluator._build_row(case, result, "
    "evaluator_elapsed_ms)\n"
)
OBSERVER_ROW_BLOCK = (
    "    if result is not None:\n"
    "        row = resolved.evaluator._build_row(case, result, "
    "evaluator_elapsed_ms)\n"
)
OBSERVER_ROW_INIT_LINE = "    row: dict[str, Any] | None = None\n"
OBSERVER_POST_TIMER_SAVE_LINE = "    model_tail_reached = result is not None\n"
OBSERVER_CAPTURE_BLOCK_LINE = (
    "        blocks = extract_sent_evidence_blocks(messages, prepared.question, "
    "sent_contexts)\n"
)


def _observer_source_text() -> str:
    return OBSERVER_PATH.read_text(encoding="utf-8")


def _mutated_observer_source(old: str, new: str, source: str | None = None) -> str:
    """Mechanical single-anchor source mutation (test-only, read-only)."""
    text = _observer_source_text() if source is None else source
    if text.count(old) != 1:
        raise AssertionError("mutation anchor is not unique: %r" % old)
    return text.replace(old, new, 1)


def _mutated_timed_telemetry_scope_condition() -> str:
    """Mutate the unique executed telemetry call, excluding post-timer capture."""
    source = _observer_source_text()
    tree = ast.parse(source)
    live = next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "run_live_observation")
    calls = [node for node in ast.walk(live)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
             and node.func.attr == "write_telemetry"]
    if len(calls) != 1:
        raise AssertionError("expected one canonical timed telemetry call")
    call_source = ast.get_source_segment(source, calls[0])
    if call_source is None:
        raise AssertionError("canonical timed telemetry source not found")
    old = 'os.getenv("QA_DEBUG_SCOPE")'
    if call_source.count(old) != 1:
        raise AssertionError("timed telemetry scope condition is not unique")
    replacement = call_source.replace(old, 'os.getenv("QA_DEBUG_SCOPE_DRIFTED")', 1)
    return _mutated_observer_source(call_source, replacement, source)


def _eq3_purity_witness(observer_source: str) -> dict:
    return O.canonical_measurement_timed_body_purity_witness(
        observer_source=observer_source
    )


def _assert_purity_fails(test: unittest.TestCase, mutated: str) -> dict:
    witness = _eq3_purity_witness(mutated)
    test.assertEqual(
        witness["CANONICAL_MEASUREMENT_TIMED_BODY_PURITY"],
        O.CANONICAL_MEASUREMENT_TIMED_BODY_PURITY_DRIFT_STATUS,
    )
    test.assertTrue(witness["ISSUES"])
    return witness


class G2Eq3EngineTimedRegionTest(unittest.TestCase):
    def test_engine_timed_region_derivation_yields_the_canonical_sequence(
        self,
    ) -> None:
        witness = O.canonical_measurement_timed_body_purity_witness()
        canonical = witness["CANONICAL_ENGINE_TIMED_BODY_OPERATION_SET"]
        observer = witness["OBSERVER_ENGINE_TIMED_BODY_OPERATION_SET"]
        self.assertTrue(canonical)
        self.assertEqual(canonical, observer)
        self.assertEqual(
            witness["TIMED_BODY_OPERATION_SET_SEMANTICS"],
            "OCCURRENCE_PRESERVING_ORDERED_OPERATION_SEQUENCE",
        )
        for operation in (
            "engine_timer_start",
            "history_normalization",
            "scope_resolution",
            "known_document_id_set",
            "effective_allowed_ids",
            "prepare",
            "routing_decision_read",
            "build_messages",
            "generation",
            "citation_normalization",
            "citation_entity_support_check",
            "pre_renumber_capture",
            "citation_renumbering",
            "deterministic_citation_verifier",
            "_result_construction",
        ):
            with self.subTest(operation=operation):
                self.assertIn(operation, canonical)

    def test_engine_extra_and_missing_detection(self) -> None:
        witness = O.canonical_measurement_timed_body_purity_witness()
        self.assertEqual(witness["ENGINE_TIMED_BODY_EXTRA_OBSERVER_OPERATIONS"], [])
        self.assertEqual(
            witness["ENGINE_TIMED_BODY_MISSING_CANONICAL_OPERATIONS"], []
        )
        duplicated = _assert_purity_fails(
            self,
            _mutated_observer_source(
                OBSERVER_RESOLUTION_LINE,
                OBSERVER_RESOLUTION_LINE + OBSERVER_RESOLUTION_LINE,
            ),
        )
        self.assertIn(
            "scope_resolution",
            duplicated["DUPLICATED_CANONICAL_TIMED_OPERATIONS"],
        )
        missing = _assert_purity_fails(
            self, _mutated_observer_source(OBSERVER_PREPARE_LINE, "")
        )
        self.assertIn(
            "prepare", missing["ENGINE_TIMED_BODY_MISSING_CANONICAL_OPERATIONS"]
        )

    def test_engine_operation_order_is_preserved(self) -> None:
        canonical = O.canonical_measurement_timed_body_purity_witness()[
            "CANONICAL_ENGINE_TIMED_BODY_OPERATION_SET"
        ]
        self.assertLess(canonical.index("prepare"), canonical.index("build_messages"))
        self.assertLess(canonical.index("build_messages"), canonical.index("generation"))
        self.assertLess(
            canonical.index("generation"), canonical.index("_result_construction")
        )
        self.assertEqual(canonical.count("citation_scope_assertion"), 2)
        self.assertEqual(canonical.count("prepare"), 1)

    def test_engine_multiplicity_equivalence(self) -> None:
        witness = O.canonical_measurement_timed_body_purity_witness()
        self.assertEqual(
            witness["ENGINE_TIMED_OPERATION_MULTIPLICITY_EQUIVALENCE"], "PASS"
        )
        self.assertEqual(witness["DUPLICATED_CANONICAL_TIMED_OPERATIONS"], [])
        self.assertEqual(witness["MISSING_CANONICAL_TIMED_OPERATION_OCCURRENCES"], [])
        mutated = _assert_purity_fails(
            self,
            _mutated_observer_source(
                OBSERVER_RESOLUTION_LINE,
                OBSERVER_RESOLUTION_LINE + OBSERVER_RESOLUTION_LINE,
            ),
        )
        self.assertEqual(
            mutated["ENGINE_TIMED_OPERATION_MULTIPLICITY_EQUIVALENCE"], "FAIL"
        )

    def test_nested_engine_hierarchical_equivalence(self) -> None:
        witness = O.canonical_measurement_timed_body_purity_witness()
        self.assertEqual(witness["NESTED_ENGINE_TIMED_REGION_EQUIVALENCE"], "PASS")
        self.assertEqual(
            witness["EVALUATOR_TIMED_BODY_OPERATION_SET_EQUIVALENCE"], "PASS"
        )

    def test_flattened_nested_operations_are_rejected(self) -> None:
        mutated = _mutated_observer_source(
            OBSERVER_EVALUATOR_START_LINE,
            OBSERVER_EVALUATOR_START_LINE
            + OBSERVER_ENGINE_START_LINE
            + OBSERVER_PREPARE_LINE,
        )
        witness = _assert_purity_fails(self, mutated)
        self.assertTrue(
            witness["EVALUATOR_OUTER_TIMED_BODY_EXTRA_OBSERVER_OPERATIONS"]
        )


class G2Eq3EvaluatorOuterRegionTest(unittest.TestCase):
    def test_evaluator_outer_timed_region_derivation(self) -> None:
        witness = O.canonical_measurement_timed_body_purity_witness()
        expected = [
            "evaluator_timer_start",
            "invoke_or_mirror_nested_engine_region",
            "evaluator_elapsed_calculation",
        ]
        self.assertEqual(
            witness["CANONICAL_EVALUATOR_OUTER_TIMED_BODY_OPERATION_SET"], expected
        )
        self.assertEqual(
            witness["OBSERVER_EVALUATOR_OUTER_TIMED_BODY_OPERATION_SET"], expected
        )
        self.assertEqual(witness["EVALUATOR_TIMER_STARTED_EXACTLY_ONCE"], "YES")
        self.assertEqual(witness["ENGINE_TIMER_STARTED_EXACTLY_ONCE"], "YES")
        self.assertEqual(witness["EVALUATOR_TIMER_OWNED_BY_OUTER_FRAME_ONLY"], "YES")
        self.assertEqual(
            witness["ENGINE_TIMER_OWNED_BY_NESTED_ENGINE_REGION_ONLY"], "YES"
        )
        self.assertEqual(
            witness["CANONICAL_EVALUATOR_POST_TIMER_MEASUREMENT_CONSUMER"],
            "_build_row(case, result, elapsed_ms)",
        )
        self.assertEqual(
            witness["OBSERVER_EVALUATOR_POST_TIMER_MEASUREMENT_CONSUMER"],
            "_build_row(case, result, evaluator_elapsed_ms)",
        )
        self.assertEqual(
            witness["EVALUATOR_POST_TIMER_MEASUREMENT_CONSUMER_EQUIVALENCE"], "PASS"
        )

    def test_evaluator_outer_extra_and_missing_detection(self) -> None:
        witness = O.canonical_measurement_timed_body_purity_witness()
        self.assertEqual(
            witness["EVALUATOR_OUTER_TIMED_BODY_EXTRA_OBSERVER_OPERATIONS"], []
        )
        self.assertEqual(
            witness["EVALUATOR_OUTER_TIMED_BODY_MISSING_CANONICAL_OPERATIONS"], []
        )
        # G2_EQ4 SAME_FRAME: an observer-only statement inserted inside the
        # evaluator measured interval (after the inline engine region) is an
        # extra outer-region operation.
        extra = _assert_purity_fails(
            self,
            _mutated_observer_source(
                OBSERVER_EVALUATOR_END_LINE,
                "    capture = {}\n" + OBSERVER_EVALUATOR_END_LINE,
            ),
        )
        self.assertTrue(
            extra["EVALUATOR_OUTER_TIMED_BODY_EXTRA_OBSERVER_OPERATIONS"]
        )
        missing = _assert_purity_fails(
            self, _mutated_observer_source(OBSERVER_ENGINE_START_LINE, "")
        )
        self.assertIn(
            "nested_engine_region_invocation_count_not_one",
            missing["EVALUATOR_OUTER_TIMED_BODY_EXTRA_OBSERVER_OPERATIONS"],
        )
        self.assertTrue(
            missing["EVALUATOR_OUTER_TIMED_BODY_MISSING_CANONICAL_OPERATIONS"]
        )

    def test_evaluator_outer_operation_order_is_preserved(self) -> None:
        sequence = O.canonical_measurement_timed_body_purity_witness()[
            "CANONICAL_EVALUATOR_OUTER_TIMED_BODY_OPERATION_SET"
        ]
        self.assertEqual(
            sequence,
            [
                "evaluator_timer_start",
                "invoke_or_mirror_nested_engine_region",
                "evaluator_elapsed_calculation",
            ],
        )
        self.assertLess(
            sequence.index("evaluator_timer_start"),
            sequence.index("invoke_or_mirror_nested_engine_region"),
        )
        self.assertLess(
            sequence.index("invoke_or_mirror_nested_engine_region"),
            sequence.index("evaluator_elapsed_calculation"),
        )

    def test_evaluator_outer_multiplicity_equivalence(self) -> None:
        witness = O.canonical_measurement_timed_body_purity_witness()
        self.assertEqual(
            witness["EVALUATOR_OUTER_TIMED_OPERATION_MULTIPLICITY_EQUIVALENCE"],
            "PASS",
        )
        # A second inline nested-region start inside the same interval is a
        # duplicated engine-region operation and breaks the occurrence count.
        mutated = _assert_purity_fails(
            self,
            _mutated_observer_source(
                OBSERVER_ENGINE_START_LINE,
                OBSERVER_ENGINE_START_LINE + OBSERVER_ENGINE_START_LINE,
            ),
        )
        self.assertEqual(
            mutated["TIMED_OPERATION_MIRROR_PAIRING_COMPLETENESS"], "FAIL"
        )

    def test_build_row_inside_evaluator_interval_is_rejected(self) -> None:
        trimmed = _mutated_observer_source(OBSERVER_ROW_BLOCK, OBSERVER_ROW_INIT_LINE)
        mutated = _mutated_observer_source(
            OBSERVER_EVALUATOR_END_LINE,
            OBSERVER_ROW_LINE_BARE + OBSERVER_EVALUATOR_END_LINE,
            source=trimmed,
        )
        witness = _assert_purity_fails(self, mutated)
        self.assertEqual(
            witness["BUILD_ROW_EXECUTES_INSIDE_EVALUATOR_MEASURED_INTERVAL"], "YES"
        )
        self.assertEqual(
            witness["BUILD_ROW_EXECUTES_AFTER_EVALUATOR_TIMER_CLOSE"], "NO"
        )

    def test_capture_before_build_row_is_rejected(self) -> None:
        mutated = _mutated_observer_source(
            OBSERVER_ROW_LINE, OBSERVER_CAPTURE_BLOCK_LINE + OBSERVER_ROW_LINE
        )
        witness = _assert_purity_fails(self, mutated)
        self.assertEqual(
            witness["BUILD_ROW_EXECUTES_BEFORE_OBSERVER_ONLY_CAPTURE"], "NO"
        )


class G2Eq3IntervalContaminationTest(unittest.TestCase):
    def test_counter_mutation_inside_engine_timer_is_rejected(self) -> None:
        mutated = _mutated_observer_source(
            OBSERVER_PREPARE_LINE,
            OBSERVER_PREPARE_LINE + '    counters["MODEL_CALLS"] = 1\n',
        )
        witness = _assert_purity_fails(self, mutated)
        self.assertEqual(
            witness["COUNTER_MUTATION_INSIDE_CANONICAL_TIMER_INTERVALS"], "YES"
        )

    def test_schema_construction_inside_timers_is_rejected(self) -> None:
        mutated = _mutated_observer_source(
            OBSERVER_PREPARE_LINE,
            OBSERVER_PREPARE_LINE
            + "    _scope_group(prepared, decision, resolution, allowed)\n",
        )
        witness = _assert_purity_fails(self, mutated)
        self.assertEqual(
            witness["OBSERVATION_SCHEMA_CONSTRUCTION_INSIDE_ENGINE_TIMER"], "YES"
        )
        outer = _mutated_observer_source(
            OBSERVER_EVALUATOR_START_LINE,
            OBSERVER_EVALUATOR_START_LINE + "    observation = {}\n",
        )
        outer_witness = _assert_purity_fails(self, outer)
        self.assertEqual(
            outer_witness["OBSERVATION_SCHEMA_CONSTRUCTION_INSIDE_EVALUATOR_TIMER"],
            "YES",
        )
        self.assertTrue(
            outer_witness["EVALUATOR_OUTER_TIMED_BODY_EXTRA_OBSERVER_OPERATIONS"]
        )

    def test_scope_group_inside_engine_timer_is_rejected(self) -> None:
        mutated = _mutated_observer_source(
            OBSERVER_PREPARE_LINE,
            OBSERVER_PREPARE_LINE
            + "    _scope_group(prepared, decision, resolution, allowed)\n",
        )
        witness = _assert_purity_fails(self, mutated)
        self.assertTrue(
            any(
                "_scope_group" in item
                for item in witness["ENGINE_TIMED_BODY_EXTRA_OBSERVER_OPERATIONS"]
            )
        )

    def test_retrieval_group_inside_engine_timer_is_rejected(self) -> None:
        mutated = _mutated_observer_source(
            OBSERVER_PREPARE_LINE,
            OBSERVER_PREPARE_LINE + "    _retrieval_group(prepared, decision)\n",
        )
        witness = _assert_purity_fails(self, mutated)
        self.assertTrue(
            any(
                "_retrieval_group" in item
                for item in witness["ENGINE_TIMED_BODY_EXTRA_OBSERVER_OPERATIONS"]
            )
        )

    def test_branch_support_helper_inside_engine_timer_is_rejected(self) -> None:
        mutated = _mutated_observer_source(
            OBSERVER_PREPARE_LINE,
            OBSERVER_PREPARE_LINE
            + "    _supports_canonical_model_tail(prepared, decision)\n",
        )
        witness = _assert_purity_fails(self, mutated)
        self.assertTrue(
            any(
                "_supports_canonical_model_tail" in item
                for item in witness["ENGINE_TIMED_BODY_EXTRA_OBSERVER_OPERATIONS"]
            )
        )
        self.assertEqual(
            witness["SUPPORTED_BRANCH_JUDGEMENT_OUTSIDE_BOTH_INTERVALS"], "NO"
        )

    def test_prepare_moved_outside_engine_timer_is_rejected(self) -> None:
        trimmed = _mutated_observer_source(OBSERVER_PREPARE_LINE, "")
        mutated = _mutated_observer_source(
            OBSERVER_CONSTRUCTION_LINE,
            OBSERVER_PREPARE_LINE + OBSERVER_CONSTRUCTION_LINE,
            source=trimmed,
        )
        witness = _assert_purity_fails(self, mutated)
        self.assertEqual(
            witness["CANONICAL_TIMED_OPERATION_MOVED_OUTSIDE_TIMER"], "YES"
        )
        self.assertEqual(
            witness["CANONICAL_TIMED_OPERATION_PRECOMPUTED_OUTSIDE_TIMER"], "YES"
        )
        self.assertNotEqual(witness["PRE_RESOLVED_CANONICAL_TIMED_RESULTS"], "NONE")
        self.assertEqual(
            witness["DUPLICATE_PREPARE_ROUTE_RETRIEVE_FOR_OBSERVER_ELIGIBILITY"],
            "YES",
        )

    def test_duplicate_prepare_is_rejected(self) -> None:
        in_region = _assert_purity_fails(
            self,
            _mutated_observer_source(
                OBSERVER_PREPARE_LINE, OBSERVER_PREPARE_LINE + OBSERVER_PREPARE_LINE
            ),
        )
        self.assertIn("prepare", in_region["DUPLICATED_CANONICAL_TIMED_OPERATIONS"])
        pre_run = _assert_purity_fails(
            self,
            _mutated_observer_source(
                OBSERVER_CONSTRUCTION_LINE,
                OBSERVER_PREPARE_LINE + OBSERVER_CONSTRUCTION_LINE,
            ),
        )
        self.assertEqual(
            pre_run["DUPLICATE_PREPARE_ROUTE_RETRIEVE_FOR_OBSERVER_ELIGIBILITY"],
            "YES",
        )

    def test_duplicated_canonical_operation_is_rejected(self) -> None:
        for anchor, operation in (
            (OBSERVER_RESOLUTION_LINE, "scope_resolution"),
            (OBSERVER_GENERATION_LINE, "generation"),
        ):
            with self.subTest(operation=operation):
                witness = _assert_purity_fails(
                    self, _mutated_observer_source(anchor, anchor + anchor)
                )
                self.assertIn(
                    operation, witness["DUPLICATED_CANONICAL_TIMED_OPERATIONS"]
                )

    def test_engine_timer_start_moved_before_construction_is_rejected(self) -> None:
        trimmed = _mutated_observer_source(OBSERVER_ENGINE_START_LINE, "")
        mutated = _mutated_observer_source(
            OBSERVER_CONSTRUCTION_LINE,
            OBSERVER_ENGINE_START_LINE + OBSERVER_CONSTRUCTION_LINE,
            source=trimmed,
        )
        witness = _assert_purity_fails(self, mutated)
        self.assertEqual(
            witness["CANONICAL_TIMED_OPERATION_MOVED_OUTSIDE_TIMER"], "YES"
        )
        self.assertEqual(
            witness["TIMED_OPERATION_MIRROR_PAIRING_COMPLETENESS"], "FAIL"
        )
        boundary = O.canonical_measurement_timer_boundary_witness(
            observer_source=mutated
        )
        self.assertEqual(boundary["ENGINE_RESULT_TIMER_BOUNDARY_EQUIVALENCE"], "FAIL")
        self.assertEqual(
            boundary["CANONICAL_MEASUREMENT_TIMER_BOUNDARY_EQUIVALENCE"],
            O.CANONICAL_MEASUREMENT_TIMER_BOUNDARY_DRIFT_STATUS,
        )

    def test_nested_region_restarting_evaluator_timer_is_rejected(self) -> None:
        mutated = _mutated_observer_source(
            OBSERVER_ENGINE_START_LINE,
            OBSERVER_EVALUATOR_START_LINE + OBSERVER_ENGINE_START_LINE,
        )
        witness = _assert_purity_fails(self, mutated)
        self.assertEqual(witness["EVALUATOR_TIMER_STARTED_EXACTLY_ONCE"], "NO")
        self.assertEqual(witness["ENGINE_TIMER_STARTED_EXACTLY_ONCE"], "YES")
        self.assertEqual(
            witness["CANONICAL_MEASUREMENT_TIMED_BODY_PURITY"],
            O.CANONICAL_MEASUREMENT_TIMED_BODY_PURITY_DRIFT_STATUS,
        )

    def test_capture_package_before_evaluator_close_is_rejected(self) -> None:
        # A packaging statement inside the mirrored nested engine region.
        nested_bundle = _mutated_observer_source(
            OBSERVER_RESULT_CALL_LINE,
            "            capture = {}\n" + OBSERVER_RESULT_CALL_LINE,
        )
        nested_witness = _assert_purity_fails(self, nested_bundle)
        self.assertTrue(
            nested_witness["UNCLASSIFIED_OBSERVER_ENGINE_TIMED_OPERATIONS"]
            or any(
                "capture" in item
                for item in nested_witness["ENGINE_TIMED_BODY_EXTRA_OBSERVER_OPERATIONS"]
            )
        )
        self.assertEqual(
            nested_witness[
                "OBSERVER_SPECIFIC_CAPTURE_PACKAGING_BEFORE_EVALUATOR_TIMER_CLOSE"
            ],
            "YES",
        )
        # A packaging statement inside the evaluator interval but outside the
        # mirrored nested engine region.
        outer_bundle = _mutated_observer_source(
            OBSERVER_EVALUATOR_END_LINE,
            "    capture = {}\n" + OBSERVER_EVALUATOR_END_LINE,
        )
        outer_witness = _assert_purity_fails(self, outer_bundle)
        self.assertEqual(
            outer_witness[
                "OBSERVER_SPECIFIC_CAPTURE_PACKAGING_BEFORE_EVALUATOR_TIMER_CLOSE"
            ],
            "YES",
        )


class G2Eq3PostTimerInvarianceTest(unittest.TestCase):
    def _run_with_clock(self) -> tuple[dict, "SyntheticBindings", list]:
        clock = _DeterministicPerfCounter([5.0, 6.0, 6.5, 7.0, 9.0])
        harness = SyntheticBindings(clock=clock)
        with unittest.mock.patch.object(O.time, "perf_counter", clock):
            payload = O.run_live_observation(live_request(), harness.bindings)
        return payload, harness, list(clock.calls)

    def test_post_timer_bookkeeping_does_not_change_engine_elapsed(self) -> None:
        payload, harness, reads_before = self._run_with_clock()
        engine_elapsed_before = harness.engine_holder["engine"].result.elapsed_ms
        self.assertEqual(engine_elapsed_before, round((7.0 - 6.0) * 1000))
        O.compute_observation_semantic_digest(payload["OBSERVATION"])
        O.validate_observation(payload["OBSERVATION"])
        O.canonical_json(payload["OBSERVATION"])
        json.dumps(payload, ensure_ascii=False)
        self.assertEqual(
            harness.engine_holder["engine"].result.elapsed_ms, engine_elapsed_before
        )

    def test_post_timer_bookkeeping_does_not_change_evaluator_elapsed(self) -> None:
        payload, _harness, reads_before = self._run_with_clock()
        row = payload["OBSERVATION"]["measurement"]["evaluator_output"]
        evaluator_elapsed_before = row["elapsed_ms"]
        self.assertEqual(evaluator_elapsed_before, round((9.0 - 5.0) * 1000))
        O.compute_observation_semantic_digest(payload["OBSERVATION"])
        O.validate_observation(payload["OBSERVATION"])
        O.canonical_digest(payload["OBSERVATION"])
        self.assertEqual(row["elapsed_ms"], evaluator_elapsed_before)
        self.assertEqual(reads_before, [5.0, 6.0, 6.5, 7.0, 9.0])

    def test_eq3_live_envelope_and_assertion_block_pass(self) -> None:
        payload = base_payload()
        witness = payload["CANONICAL_MEASUREMENT_TIMED_BODY_PURITY_WITNESS"]
        self.assertEqual(
            witness["CANONICAL_MEASUREMENT_TIMED_BODY_PURITY"], "PASS"
        )
        self.assertEqual(
            payload["FULL_CANONICAL_QA_SEMANTIC_SEQUENCE"][
                "CANONICAL_MEASUREMENT_TIMED_BODY_PURITY"
            ],
            "PASS",
        )
        assertions = payload["EQ3_REQUIRED_ASSERTIONS"]
        self.assertEqual(assertions["REQUIRED_FIX_COUNT"], 1)
        self.assertEqual(
            assertions["FIX_1_CANONICAL_MEASUREMENT_TIMED_BODY_PURITY"], "PASS"
        )
        self.assertEqual(
            assertions["OBSERVATION_EQUIVALENCE_ESTABLISHED_BY_STATIC_SYNTHETIC_G2_TESTS"],
            "YES",
        )

    def test_request_identity_polarity_regression(self) -> None:
        assertions = O.eq3_required_assertions()
        self.assertEqual(
            assertions["REQUEST_IDENTITY_NOT_COPIED_FROM_HISTORICAL_ARTIFACT"],
            "YES",
        )
        self.assertEqual(
            assertions["REQUEST_IDENTITY_COPIED_FROM_HISTORICAL_ARTIFACT"], "NO"
        )

    def test_active_canonical_generation_binding_regression(self) -> None:
        assertions = O.eq3_required_assertions()
        self.assertEqual(assertions["ACTIVE_CANONICAL_GENERATION_BINDING"],
                         "OllamaClient.chat")

    def test_active_pipeline_chat_stream_absence_regression(self) -> None:
        assertions = O.eq3_required_assertions()
        self.assertEqual(assertions["ACTIVE_CANONICAL_PIPELINE_CONTAINS_CHAT_STREAM"],
                         "NO")
        self.assertEqual(
            [
                node
                for node in _call_nodes(_observer_tree())
                if _callable_name(node.func) == "chat_stream"
            ],
            [],
        )


# --------------------------------------------------------------------------- #
# 34-40 G2_EQ4 observer equivalence correction (FIX_1 / FIX_2 / FIX_3)
# --------------------------------------------------------------------------- #
class SyntheticTelemetryFailureEngineV2(SyntheticEngineV2):
    """Synthetic telemetry double modelling the canonical IO-failure contract.

    ``core/engine_v2.py#write_telemetry`` appends inside an OSError-swallowing
    ``try``: a failed append never propagates into the answer semantics.  This
    double records the invocation and models the swallowed append failure, so
    the test can prove the observer does not add observer-side suppression and
    that a failed append cannot change the canonical answer.
    """

    def write_telemetry(self, record):  # noqa: ANN001
        self.recorder["telemetry_calls"].append(copy.deepcopy(record))
        try:
            raise OSError("SYNTHETIC_TEST_ONLY_TELEMETRY_IO_FAILURE")
        except OSError:
            self.recorder.setdefault("telemetry_append_results", []).append(False)


class G2Eq4SameFrameShapeTest(unittest.TestCase):
    """FIX_1: same-frame implementation shape, no transport packaging return."""

    def test_live_path_is_a_single_frame(self) -> None:
        self.assertEqual(O.OBSERVER_LIVE_PATH_IMPLEMENTATION_SHAPE, "SAME_FRAME")
        self.assertEqual(O.OBSERVER_LIVE_PATH_FUNCTION_NAMES, ("run_live_observation",))
        self.assertEqual(O.OBSERVER_NESTED_REGION_FUNCTION, "run_live_observation")
        tree = _observer_tree()
        names = [
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        ]
        self.assertIn("run_live_observation", names)
        self.assertNotIn("_run_canonical_model_tail", names)
        self.assertEqual(
            [
                node
                for node in _call_nodes(tree)
                if _callable_name(node.func) == "_run_canonical_model_tail"
            ],
            [],
        )

    def test_no_observer_transport_packaging_return_exists(self) -> None:
        witness = O.canonical_measured_region_return_witness()
        self.assertEqual(
            witness["AST_RETURN_NODES_INSIDE_MEASURED_REGIONS"], "FULLY_CLASSIFIED"
        )
        self.assertEqual(
            witness["UNCLASSIFIED_RETURN_NODES_INSIDE_MEASURED_REGIONS"], []
        )
        self.assertEqual(
            witness["PRE_EVALUATOR_CLOSE_OBSERVER_RETURN_PACKAGING"], "NONE"
        )
        self.assertEqual(witness["RETURN_WITNESS_BLIND_SPOT"], "CLOSED")
        self.assertEqual(witness["OBSERVER_RETURN_NODES_INSIDE_MEASURED_REGIONS"], 0)
        self.assertEqual(witness["OBSERVER_NESTED_REGION_HELPER_RETURN"], "NONE")
        self.assertEqual(
            witness["RETURN_CLASSIFICATION_VOCABULARY"],
            [
                "CANONICAL_EQUIVALENT_RETURN",
                "EMPTY_CONTROL_RETURN",
                "OBSERVER_CAPTURE_PACKAGING_RETURN",
            ],
        )

    def test_canonical_branch_outcome_is_read_from_the_canonical_result(self) -> None:
        source = _observer_source_text()
        self.assertNotIn("branch_outcome", source)
        self.assertIn(OBSERVER_POST_TIMER_SAVE_LINE, source)
        purity = O.canonical_measurement_timed_body_purity_witness()
        self.assertEqual(purity["OBSERVER_SPECIFIC_CAPTURE_PACKAGING_BEFORE_EVALUATOR_TIMER_CLOSE"], "NO")


class G2Eq4PackagingReturnMutationTest(unittest.TestCase):
    """Mutants A-D: any pre-evaluator-close transport packaging return fails."""

    def _assert_return_witness_fails(self, mutated: str) -> dict:
        witness = O.canonical_measured_region_return_witness(
            observer_source=mutated
        )
        self.assertEqual(
            witness["PRE_EVALUATOR_CLOSE_OBSERVER_RETURN_PACKAGING"] != "NONE", True
        )
        self.assertEqual(
            witness["UNCLASSIFIED_RETURN_NODES_INSIDE_MEASURED_REGIONS"], []
        )
        self.assertEqual(witness["RETURN_WITNESS_BLIND_SPOT"], "CLOSED")
        return witness

    def test_return_tuple_before_evaluator_close_is_rejected(self) -> None:
        mutated = _mutated_observer_source(
            OBSERVER_EVALUATOR_START_LINE,
            OBSERVER_EVALUATOR_START_LINE
            + "    return (prepared, decision)\n",
        )
        witness = self._assert_return_witness_fails(mutated)
        self.assertTrue(
            any(
                entry["CLASSIFICATION"] == "OBSERVER_CAPTURE_PACKAGING_RETURN"
                for entry in witness["OBSERVER_RETURN_LEDGER"]
            )
        )
        _assert_purity_fails(self, mutated)

    def test_return_list_before_evaluator_close_is_rejected(self) -> None:
        mutated = _mutated_observer_source(
            OBSERVER_EVALUATOR_START_LINE,
            OBSERVER_EVALUATOR_START_LINE + "    return [prepared]\n",
        )
        self._assert_return_witness_fails(mutated)
        _assert_purity_fails(self, mutated)

    def test_return_dict_before_evaluator_close_is_rejected(self) -> None:
        mutated = _mutated_observer_source(
            OBSERVER_EVALUATOR_START_LINE,
            OBSERVER_EVALUATOR_START_LINE + '    return {"prepared": prepared}\n',
        )
        self._assert_return_witness_fails(mutated)
        _assert_purity_fails(self, mutated)

    def test_return_custom_capture_package_before_close_is_rejected(self) -> None:
        mutated = _mutated_observer_source(
            OBSERVER_EVALUATOR_START_LINE,
            OBSERVER_EVALUATOR_START_LINE
            + "    return _supports_canonical_model_tail(prepared, decision)\n",
        )
        self._assert_return_witness_fails(mutated)
        _assert_purity_fails(self, mutated)

    def test_return_before_engine_timer_close_is_rejected(self) -> None:
        mutated = _mutated_observer_source(
            OBSERVER_RESULT_CALL_LINE,
            "            return (answer, used_citations)\n"
            + OBSERVER_RESULT_CALL_LINE,
        )
        witness = O.canonical_measured_region_return_witness(
            observer_source=mutated
        )
        self.assertEqual(
            [
                entry["CLASSIFICATION"]
                for entry in witness["OBSERVER_RETURN_LEDGER"]
                if entry["INSIDE_ENGINE_MEASURED_INTERVAL"] == "YES"
            ],
            ["OBSERVER_CAPTURE_PACKAGING_RETURN"],
        )
        _assert_purity_fails(self, mutated)


class G2Eq4TimedRegionExhaustivenessTest(unittest.TestCase):
    """FIX_2: the actual AST enumeration is the completeness authority (E-H)."""

    def test_actual_ast_enumeration_is_the_completeness_authority(self) -> None:
        purity = O.canonical_measurement_timed_body_purity_witness()
        self.assertEqual(
            purity["ACTUAL_AST_REGION_ENUMERATION_IS_COMPLETENESS_AUTHORITY"], "YES"
        )
        self.assertEqual(purity["MARKER_TABLE_CAN_DETERMINE_COMPLETENESS"], "NO")
        self.assertEqual(purity["BLACKLIST_CAN_DETERMINE_COMPLETENESS"], "NO")
        self.assertEqual(
            purity["TIMED_LEDGER_COMPLETENESS_AUTHORITY"],
            "ACTUAL_AST_TIMER_REGION_ENUMERATION",
        )
        self.assertEqual(
            purity["TIMED_OPERATION_TABLE_ROLE"],
            "SECONDARY_LABELING_AND_DIAGNOSTIC_ONLY",
        )
        self.assertEqual(
            purity["OBSERVER_ONLY_HELPER_NAMES_ROLE"],
            "SECONDARY_LABELING_AND_DIAGNOSTIC_ONLY",
        )
        self.assertEqual(
            purity["OBSERVER_PACKAGING_NAME_SET_ROLE"],
            "SECONDARY_LABELING_AND_DIAGNOSTIC_ONLY",
        )
        self.assertEqual(purity["TIMED_OPERATION_WITNESS_EXHAUSTIVENESS"], "PASS")
        self.assertEqual(purity["TIMED_OPERATION_MIRROR_PAIRING_COMPLETENESS"], "PASS")
        self.assertEqual(
            purity["CANONICAL_ENGINE_TIMED_OCCURRENCE_COUNT"],
            len(purity["CANONICAL_ENGINE_TIMED_OPERATION_LEDGER"]),
        )
        self.assertEqual(purity["UNCLASSIFIED_CANONICAL_ENGINE_TIMED_OPERATIONS"], [])
        self.assertEqual(purity["UNCLASSIFIED_OBSERVER_ENGINE_TIMED_OPERATIONS"], [])
        self.assertEqual(
            purity["UNCLASSIFIED_CANONICAL_EVALUATOR_TIMED_OPERATIONS"], []
        )
        self.assertEqual(
            purity["UNCLASSIFIED_OBSERVER_EVALUATOR_TIMED_OPERATIONS"], []
        )
        self.assertEqual(purity["UNCOVERED_CANONICAL_ENGINE_TIMED_OCCURRENCES"], [])
        self.assertEqual(purity["UNCOVERED_OBSERVER_ENGINE_TIMED_OCCURRENCES"], [])
        self.assertEqual(purity["MIRRORED_STATEMENT_PAIR_MISMATCHES"], [])
        self.assertEqual(
            purity["MIRRORED_STATEMENT_PAIR_COUNTS"]["CANONICAL"],
            purity["MIRRORED_STATEMENT_PAIR_COUNTS"]["OBSERVER"],
        )

    def test_every_ledger_entry_carries_the_required_fields(self) -> None:
        purity = O.canonical_measurement_timed_body_purity_witness()
        required = (
            "OCCURRENCE_ID",
            "AST_NODE_TYPE",
            "SOURCE_START_LINE",
            "SOURCE_END_LINE",
            "NORMALIZED_AST_OR_SOURCE",
            "CALL_TARGET_IF_ANY",
            "PARENT_CONTROL_STRUCTURE",
            "EXECUTION_ORDER_INDEX",
            "OCCURRENCE_COUNT",
            "CLASSIFICATION",
            "CLASSIFICATION_REASON",
        )
        for ledger_name in (
            "CANONICAL_ENGINE_TIMED_OPERATION_LEDGER",
            "OBSERVER_ENGINE_TIMED_OPERATION_LEDGER",
        ):
            for entry in purity[ledger_name]:
                with self.subTest(ledger=ledger_name, item=entry["OCCURRENCE_ID"]):
                    for field_name in required:
                        self.assertIn(field_name, entry)
                    self.assertIn(
                        entry["CLASSIFICATION"], O.TIMED_OCCURRENCE_CLASSES
                    )
                    self.assertTrue(entry["CLASSIFICATION_REASON"])

    def test_ledger_covers_every_required_node_type(self) -> None:
        purity = O.canonical_measurement_timed_body_purity_witness()
        self.assertEqual(
            purity["TIMED_LEDGER_COVERED_NODE_TYPES"],
            list(O.TIMED_LEDGER_COVERED_NODE_TYPES),
        )
        covered_types = set()
        statement_types = set()
        for ledger_name in (
            "CANONICAL_ENGINE_TIMED_OPERATION_LEDGER",
            "OBSERVER_ENGINE_TIMED_OPERATION_LEDGER",
        ):
            for entry in purity[ledger_name]:
                if entry["OCCURRENCE_KIND"] == "EXPRESSION":
                    self.assertIn(
                        entry["AST_NODE_TYPE"], O.TIMED_LEDGER_COVERED_NODE_TYPES
                    )
                    covered_types.add(entry["AST_NODE_TYPE"])
                else:
                    self.assertTrue(hasattr(ast, entry["AST_NODE_TYPE"]))
                    statement_types.add(entry["AST_NODE_TYPE"])
        # The canonical timer region genuinely exercises these executable node
        # types, and every one of them is exhaustively classified.
        for node_type in ("Assign", "Call", "If", "With", "Return", "Compare"):
            with self.subTest(node_type=node_type):
                self.assertIn(node_type, covered_types | statement_types)

    def _assert_timed_occurrence_rejected(self, witness: dict) -> None:
        """The witness must fail through the ledger or the mirrored pairing."""
        self.assertEqual(witness["TIMED_OPERATION_WITNESS_EXHAUSTIVENESS"], "FAIL")
        self.assertTrue(
            witness["UNCLASSIFIED_OBSERVER_ENGINE_TIMED_OPERATIONS"]
            or witness["MIRRORED_STATEMENT_PAIR_MISMATCHES"]
            or witness["TIMED_OPERATION_MIRROR_PAIRING_COMPLETENESS"] == "FAIL"
            or witness["UNCOVERED_OBSERVER_ENGINE_TIMED_OCCURRENCES"]
        )

    def test_unknown_observer_call_in_timed_region_is_rejected(self) -> None:
        # E: an unknown observer Call with the marker tables left untouched.
        baseline = O.canonical_measurement_timed_body_purity_witness()
        mutated = _mutated_observer_source(
            OBSERVER_PREPARE_LINE,
            OBSERVER_PREPARE_LINE + "    unknown_observer_helper(prepared)\n",
        )
        witness = _assert_purity_fails(self, mutated)
        self._assert_timed_occurrence_rejected(witness)
        self.assertEqual(
            witness["MIRRORED_STATEMENT_PAIR_COUNTS"]["OBSERVER"],
            baseline["MIRRORED_STATEMENT_PAIR_COUNTS"]["OBSERVER"] + 1,
        )
        self.assertEqual(
            witness["TIMED_OPERATION_MIRROR_PAIRING_COMPLETENESS"], "FAIL"
        )
        self.assertTrue(witness["UNMATCHED_MIRRORED_OBSERVER_OCCURRENCES"])

    def test_unknown_timed_assignment_is_classified_or_rejected(self) -> None:
        # F: an unknown timed assignment must be classified or the witness fails.
        mutated = _mutated_observer_source(
            OBSERVER_PREPARE_LINE,
            OBSERVER_PREPARE_LINE + "    unknown_counter = 7\n",
        )
        witness = _assert_purity_fails(self, mutated)
        self._assert_timed_occurrence_rejected(witness)
        self.assertTrue(
            any(
                "unknown_counter" in entry["NORMALIZED_AST_OR_SOURCE"]
                for entry in witness["OBSERVER_ENGINE_TIMED_OPERATION_LEDGER"]
            )
        )

    def test_unknown_timed_with_is_classified_or_rejected(self) -> None:
        # G: an unknown timed With must be classified or the witness fails.
        mutated = _mutated_observer_source(
            OBSERVER_PREPARE_LINE,
            OBSERVER_PREPARE_LINE + "    with engine._model_lock:\n        pass\n",
        )
        witness = _assert_purity_fails(self, mutated)
        self._assert_timed_occurrence_rejected(witness)
        self.assertTrue(
            any(
                entry["AST_NODE_TYPE"] == "With"
                for entry in witness["OBSERVER_ENGINE_TIMED_OPERATION_LEDGER"]
            )
        )

    def test_unknown_timed_return_is_classified_or_rejected(self) -> None:
        # H: an unknown timed Return must be classified or the witness fails.
        mutated = _mutated_observer_source(
            OBSERVER_PREPARE_LINE,
            OBSERVER_PREPARE_LINE + "    return prepared\n",
        )
        witness = _assert_purity_fails(self, mutated)
        self._assert_timed_occurrence_rejected(witness)
        self.assertTrue(
            any(
                entry["AST_NODE_TYPE"] == "Return"
                for entry in witness["OBSERVER_ENGINE_TIMED_OPERATION_LEDGER"]
            )
        )
        # The measured-region return witness independently classifies it as an
        # observer transport packaging return.
        returns = O.canonical_measured_region_return_witness(
            observer_source=mutated
        )
        self.assertEqual(
            returns["PRE_EVALUATOR_CLOSE_OBSERVER_RETURN_PACKAGING"] != "NONE",
            True,
        )

    def test_covered_expression_occurrences_are_in_the_ledger(self) -> None:
        purity = O.canonical_measurement_timed_body_purity_witness()
        observer_ledger = purity["OBSERVER_ENGINE_TIMED_OPERATION_LEDGER"]
        kinds = {entry["OCCURRENCE_KIND"] for entry in observer_ledger}
        self.assertEqual(kinds, {"STATEMENT", "EXPRESSION"})
        call_entries = [
            entry
            for entry in observer_ledger
            if entry["AST_NODE_TYPE"] == "Call"
        ]
        self.assertTrue(call_entries)
        self.assertTrue(
            any(
                "build_messages" in entry["CALL_TARGET_IF_ANY"][0]
                for entry in call_entries
                if entry["CALL_TARGET_IF_ANY"]
            )
        )


class G2Eq4TimedSemanticsTest(unittest.TestCase):
    """FIX_3 plus multiplicity mutants I-N."""

    def test_model_lock_and_telemetry_are_mirrored_not_omitted(self) -> None:
        purity = O.canonical_measurement_timed_body_purity_witness()
        self.assertEqual(purity["MODEL_LOCK_TIMED_SEMANTICS"], "PRESERVED")
        self.assertEqual(
            purity["CANONICAL_TELEMETRY_TIMED_SEMANTICS"],
            "PRESERVED_UNDER_ACCEPTED_TPR1_PERMISSION_SEMANTICS",
        )
        self.assertEqual(
            purity["CANONICAL_MODEL_LOCK_OPERATION_LABEL"], "engine_model_lock"
        )
        self.assertEqual(
            purity["OBSERVER_MODEL_LOCK_OPERATION_LABEL"], "engine_model_lock"
        )
        self.assertEqual(
            purity["CANONICAL_TELEMETRY_OPERATION_LABEL"], "telemetry_append"
        )
        self.assertEqual(
            purity["OBSERVER_TELEMETRY_OPERATION_LABEL"], "telemetry_append"
        )
        omitted = {
            entry["OPERATION"]
            for entry in purity["CANONICAL_ENGINE_TIMED_BODY_OMITTED_NONSEMANTIC_OPERATIONS"]
        }
        self.assertNotIn("canonical per-engine model lock", omitted)
        self.assertNotIn("telemetry append", omitted)
        observer_markers = [
            entry["OBSERVER_MARKER"]
            for entry in O.ENGINE_TIMED_BODY_OPERATION_TABLE
            if entry["CLASS"] == "MIRRORED"
        ]
        self.assertIn(O.OBSERVER_MODEL_LOCK_MARKER, observer_markers)
        self.assertIn(O.OBSERVER_TELEMETRY_CALL_MARKER, observer_markers)

    def test_telemetry_payload_is_bound_to_the_canonical_payload(self) -> None:
        witness = O.canonical_telemetry_payload_binding_witness()
        self.assertEqual(witness["TELEMETRY_PAYLOAD_BINDING_EQUIVALENCE"], "PASS")
        self.assertEqual(witness["TELEMETRY_PAYLOAD_KEY_ORDER_EQUIVALENCE"], "YES")
        self.assertEqual(
            witness["TELEMETRY_PAYLOAD_VALUE_BINDING_EQUIVALENCE"], "YES"
        )
        self.assertEqual(
            witness["TELEMETRY_CONDITIONAL_SCOPE_KEY_BINDING_EQUIVALENCE"], "YES"
        )
        self.assertIn("QA_DEBUG_SCOPE", witness["CANONICAL_CONDITIONAL_SCOPE_ENTRY"])
        self.assertIn("QA_DEBUG_SCOPE", witness["OBSERVER_CONDITIONAL_SCOPE_ENTRY"])
        self.assertEqual(
            witness["CANONICAL_CONDITIONAL_SCOPE_ENTRY"],
            witness["OBSERVER_CONDITIONAL_SCOPE_ENTRY"],
        )
        self.assertNotIn("TELEMETRY_ENABLED", witness["OBSERVER_CONDITIONAL_SCOPE_ENTRY"])
        drifted = O.canonical_telemetry_payload_binding_witness(
            source=_mutated_timed_telemetry_scope_condition()
        )
        self.assertEqual(drifted["TELEMETRY_PAYLOAD_BINDING_EQUIVALENCE"], "FAIL")
        self.assertEqual(
            drifted["TELEMETRY_CONDITIONAL_SCOPE_KEY_BINDING_EQUIVALENCE"], "NO"
        )

    def test_duplicate_telemetry_operation_fails_multiplicity(self) -> None:
        # I: a duplicated canonical telemetry append breaks multiplicity.
        mutated = _mutated_observer_source(
            OBSERVER_TELEMETRY_CALL_LINE,
            "            _telemetry_mirror_extra = (\n"
            "                resolved.engine_v2.write_telemetry({})\n"
            "            )\n"
            + OBSERVER_TELEMETRY_CALL_LINE,
        )
        witness = _assert_purity_fails(self, mutated)
        self.assertEqual(
            witness["OBSERVER_TELEMETRY_INVOCATION_OCCURRENCE_COUNT"], 2
        )
        self.assertEqual(
            witness["CANONICAL_TELEMETRY_TIMED_SEMANTICS"],
            O.CANONICAL_MEASUREMENT_TIMED_BODY_PURITY_DRIFT_STATUS,
        )
        self.assertTrue(
            witness["UNCLASSIFIED_OBSERVER_ENGINE_TIMED_OPERATIONS"]
            or witness["TIMED_OPERATION_MIRROR_PAIRING_COMPLETENESS"] == "FAIL"
        )

    def test_duplicate_model_lock_fails_multiplicity(self) -> None:
        mutated = _mutated_observer_source(
            OBSERVER_MODEL_LOCK_LINE,
            OBSERVER_MODEL_LOCK_LINE
            + "                pass\n"
            + OBSERVER_MODEL_LOCK_LINE,
        )
        witness = _assert_purity_fails(self, mutated)
        self.assertEqual(witness["OBSERVER_MODEL_LOCK_OCCURRENCE_COUNT"], 2)
        self.assertEqual(
            witness["MODEL_LOCK_TIMED_SEMANTICS"],
            O.CANONICAL_MEASUREMENT_TIMED_BODY_PURITY_DRIFT_STATUS,
        )
        self.assertTrue(
            witness["UNCLASSIFIED_OBSERVER_ENGINE_TIMED_OPERATIONS"]
            or witness["TIMED_OPERATION_MIRROR_PAIRING_COMPLETENESS"] == "FAIL"
        )

    def test_missing_canonical_occurrence_fails(self) -> None:
        # J: removing a mirrored canonical occurrence is a missing occurrence.
        witness = _assert_purity_fails(
            self, _mutated_observer_source(OBSERVER_PREPARE_LINE, "")
        )
        self.assertIn(
            "prepare", witness["MISSING_CANONICAL_TIMED_OPERATION_OCCURRENCES"]
        )
        self.assertEqual(
            witness["ENGINE_TIMED_OPERATION_MULTIPLICITY_EQUIVALENCE"], "FAIL"
        )

    def test_model_lock_absent_from_measured_interval_fails(self) -> None:
        # K, direction 1: the current canonical source places the lock INSIDE
        # the measured interval, so a mirrored interval without the canonical
        # lock occurrence is a missing canonical timed operation.
        mutated = _mutated_observer_source(
            OBSERVER_MODEL_LOCK_LINE,
            "            with engine.generation_guard:\n",
        )
        witness = _assert_purity_fails(self, mutated)
        self.assertIn(
            "engine_model_lock",
            witness["MISSING_CANONICAL_TIMED_OPERATION_OCCURRENCES"],
        )
        self.assertEqual(
            witness["MODEL_LOCK_TIMED_SEMANTICS"],
            O.CANONICAL_MEASUREMENT_TIMED_BODY_PURITY_DRIFT_STATUS,
        )
        self.assertEqual(
            witness["CANONICAL_MODEL_LOCK_EXECUTES_INSIDE_ENGINE_MEASURED_INTERVAL"],
            "YES",
        )

    def test_canonical_timed_operation_outside_the_timer_fails(self) -> None:
        # K, direction 2: the canonical timed telemetry operation may never
        # appear outside the measured interval.
        mutated = _mutated_observer_source(
            OBSERVER_POST_TIMER_SAVE_LINE,
            "    model_tail_reached = "
            "resolved.engine_v2.write_telemetry(None) is not None\n",
        )
        witness = _assert_purity_fails(self, mutated)
        self.assertEqual(
            witness["CANONICAL_TIMED_OPERATION_MOVED_OUTSIDE_TIMER"], "YES"
        )
        self.assertIn(
            "telemetry_append", witness["PRE_RESOLVED_CANONICAL_TIMED_RESULTS"]
        )
        self.assertEqual(
            witness["CANONICAL_TELEMETRY_EXECUTES_INSIDE_ENGINE_MEASURED_INTERVAL"],
            "YES",
        )

    def test_omitted_canonical_telemetry_fails(self) -> None:
        # L: the canonical source and the accepted permission semantics require
        # the telemetry append to be preserved faithfully.
        trimmed = _mutated_observer_source(
            OBSERVER_TELEMETRY_CALL_LINE,
            "            telemetry_not_preserved = None\n"
            "            _unused_telemetry_payload = (\n",
        )
        witness = _assert_purity_fails(self, trimmed)
        self.assertIn(
            "telemetry_append",
            witness["MISSING_CANONICAL_TIMED_OPERATION_OCCURRENCES"],
        )
        self.assertEqual(
            witness["CANONICAL_TELEMETRY_TIMED_SEMANTICS"],
            O.CANONICAL_MEASUREMENT_TIMED_BODY_PURITY_DRIFT_STATUS,
        )

    def test_telemetry_is_not_declared_nonsemantic_for_an_unused_return(self) -> None:
        # M: the return value being discarded never makes a timed operation
        # nonsemantic; the witness keeps it in the mirrored operation set.
        purity = O.canonical_measurement_timed_body_purity_witness()
        self.assertIn(
            "telemetry_append", purity["CANONICAL_ENGINE_TIMED_BODY_OPERATION_SET"]
        )
        self.assertIn(
            "telemetry_append", purity["OBSERVER_ENGINE_TIMED_BODY_OPERATION_SET"]
        )

    def test_model_lock_is_not_declared_nonsemantic_for_absent_contention(self) -> None:
        # N: no expected contention never makes the timed lock nonsemantic.
        purity = O.canonical_measurement_timed_body_purity_witness()
        self.assertIn(
            "engine_model_lock", purity["CANONICAL_ENGINE_TIMED_BODY_OPERATION_SET"]
        )
        self.assertIn(
            "engine_model_lock", purity["OBSERVER_ENGINE_TIMED_BODY_OPERATION_SET"]
        )
        self.assertEqual(purity["CANONICAL_MODEL_LOCK_OCCURRENCE_COUNT"], 1)
        self.assertEqual(purity["OBSERVER_MODEL_LOCK_OCCURRENCE_COUNT"], 1)

    def test_engine_timed_operation_order_is_still_preserved(self) -> None:
        sequence = O.canonical_measurement_timed_body_purity_witness()[
            "CANONICAL_ENGINE_TIMED_BODY_OPERATION_SET"
        ]
        self.assertLess(sequence.index("prepare"), sequence.index("engine_model_lock"))
        self.assertLess(
            sequence.index("engine_model_lock"), sequence.index("generation")
        )
        self.assertLess(
            sequence.index("generation"), sequence.index("telemetry_append")
        )
        self.assertLess(
            sequence.index("telemetry_append"), sequence.index("_result_construction")
        )


class G2Eq4SyntheticTelemetryTest(unittest.TestCase):
    """T / U: synthetic telemetry invocation, payload and IO-failure contract."""

    def _run(self, engine_v2=None, **overrides) -> tuple[dict, SyntheticBindings]:  # noqa: ANN001
        harness = SyntheticBindings(
            overrides.pop("prepared", None), engine_v2=engine_v2
        )
        payload = O.run_live_observation(live_request(**overrides), harness.bindings)
        return payload, harness

    def test_synthetic_telemetry_path_invokes_the_canonical_operation_once(
        self,
    ) -> None:
        payload, harness = self._run()
        self.assertEqual(payload["STATUS"], "OBSERVED")
        self.assertEqual(len(harness.record["telemetry_calls"]), 1)
        self.assertEqual(harness.record["telemetry_append_results"], [True])
        canonical_calls = [call for call in harness.record["scope_fingerprint_calls"]
                           if not call["after_canonical_measurement"]]
        self.assertEqual(len(canonical_calls), 1)
        self.assertEqual(len(harness.record["scope_fingerprint_calls"]), 2)
        record = harness.record["telemetry_calls"][0]
        self.assertEqual(record["question"], O.CANONICAL_QUERY)
        self.assertEqual(record["route"], O.CANONICAL_SUPPORTED_ROUTE)
        self.assertEqual(
            record["scope_fingerprint"], SYNTHETIC_ACCEPTED_RULE_SCOPE_FINGERPRINT
        )
        # Conditional QA_DEBUG_SCOPE scope key: the raw environment state is UNSET,
        # so the canonical conditional entry is EXCLUDED from the payload.
        self.assertEqual(os.environ.get("QA_DEBUG_SCOPE"), None)
        self.assertNotIn("scope_document_ids", record)
        witness = O.canonical_telemetry_payload_binding_witness()
        self.assertEqual(
            sorted(record),
            sorted(witness["CANONICAL_TELEMETRY_PAYLOAD_KEY_SET"]),
        )
        self.assertEqual(
            payload["OBSERVATION"]["generation_output"]["final_application_answer"],
            harness.engine_holder["engine"].result.answer,
        )

    def test_synthetic_telemetry_io_failure_does_not_change_answer_semantics(
        self,
    ) -> None:
        ok_payload, ok_harness = self._run()
        failure_harness = SyntheticBindings()
        failure_harness_bindings = O.CanonicalBindings(
            engine_factory=failure_harness.bindings.engine_factory,
            engine_v2=SyntheticTelemetryFailureEngineV2(failure_harness.record),
            citation_verifier=failure_harness.bindings.citation_verifier,
            evaluator=failure_harness.bindings.evaluator,
            config=failure_harness.bindings.config,
            library_store=failure_harness.bindings.library_store,
            query_scope=failure_harness.bindings.query_scope,
            chat=failure_harness.bindings.chat,
            rule_identity_reader=failure_harness.bindings.rule_identity_reader,
            rule_identity_manifest_provider=(
                failure_harness.bindings.rule_identity_manifest_provider
            ),
        )
        failure_payload = O.run_live_observation(
            live_request(), failure_harness_bindings
        )
        self.assertEqual(failure_payload["STATUS"], "OBSERVED")
        self.assertEqual(len(failure_harness.record["telemetry_calls"]), 1)
        self.assertEqual(
            failure_harness.record["telemetry_append_results"], [False]
        )
        self.assertEqual(
            failure_payload["OBSERVATION_EQUIVALENCE_SUPPORTED_BRANCH"],
            ok_payload["OBSERVATION_EQUIVALENCE_SUPPORTED_BRANCH"],
        )
        self.assertEqual(
            failure_payload["OBSERVATION"]["generation_output"][
                "final_application_answer"
            ],
            ok_payload["OBSERVATION"]["generation_output"][
                "final_application_answer"
            ],
        )
        self.assertEqual(
            failure_payload["OBSERVATION"]["generation_output"]["raw_model_answer"],
            ok_payload["OBSERVATION"]["generation_output"]["raw_model_answer"],
        )
        # The observation semantic digest is compared with the measured elapsed
        # value normalized: an IO failure may never change any other semantic
        # value of the same-run observation.
        def _digest_without_measured_elapsed(payload: dict) -> str:
            observation = copy.deepcopy(payload["OBSERVATION"])
            observation["measurement"]["evaluator_output"]["elapsed_ms"] = 0
            return O.compute_observation_semantic_digest(observation)

        self.assertEqual(
            _digest_without_measured_elapsed(failure_payload),
            _digest_without_measured_elapsed(ok_payload),
        )
        self.assertEqual(
            failure_payload["OBSERVATION"]["measurement"]["evaluator_output"][
                "elapsed_ms"
            ]
            is not None,
            True,
        )
        self.assertEqual(ok_harness.record["telemetry_append_results"], [True])
        self.assertEqual(
            O.AUTHORIZED_SUCCESSFUL_APPEND_DELTA,
            "AT_MOST_ONE_CANONICAL_JSONL_RECORD_PER_AUTHORIZED_CANONICAL_ANSWER_"
            "EXECUTION",
        )
        # The canonical write_telemetry swallows OSError itself: the observer
        # adds no suppression, redirection or monkeypatch.
        canonical_source = O.governed_source_text(O.ENGINE_V2_PATH)
        self.assertIn("except OSError:", canonical_source)
        live_path = "".join(
            _function_source(_observer_source_text(), name)
            for name in O.OBSERVER_LIVE_PATH_FUNCTION_NAMES
        )
        self.assertNotIn("except OSError", live_path)
        self.assertNotIn("try:", live_path)


class G2Eq4AcceptedRuleIdentityTest(unittest.TestCase):
    """P-S, V, W: invocation-time accepted-rule identity governance."""

    def test_side_effect_policy_alone_is_not_authorization(self) -> None:
        # P: an arbitrary non-empty g4-side-effect-policy without the
        # invocation-time exact accepted rule identity must fail closed.
        payload = run_blocked(
            accepted_rule_relative_path="",
            accepted_rule_raw_sha256="",
            accepted_rule_semantic_digest="",
        )
        self.assertEqual(payload["STATUS"], "BLOCKED_BEFORE_INVOCATION")
        checks = {item["CHECK"]: item["PASS"] for item in payload["LIVE_GUARD_CHECKS"]}
        self.assertFalse(checks["FUTURE_G4_ACCEPTED_RULE_LOCATOR_PRESENT"])
        self.assertFalse(checks["FUTURE_G4_ACCEPTED_RULE_RAW_SHA256_PRESENT"])
        self.assertFalse(checks["FUTURE_G4_ACCEPTED_RULE_SEMANTIC_DIGEST_PRESENT"])
        self.assertTrue(checks["G4_SIDE_EFFECT_POLICY_RESOLVED"])
        self.assertFalse(payload["LIVE_GUARDS_PASSED"])
        self.assertEqual(payload["TARGET_OBSERVATION_RUNS"], 0)

    def test_invocation_time_rule_raw_sha_mismatch_fails_closed(self) -> None:
        # Q
        _, raw_sha, digest = _synthetic_rule_identity()
        payload = run_blocked(
            accepted_rule_raw_sha256="a" * 64,
        )
        self.assertFalse(payload["LIVE_GUARDS_PASSED"])
        checks = {item["CHECK"]: item["PASS"] for item in payload["LIVE_GUARD_CHECKS"]}
        self.assertFalse(checks["FUTURE_G4_ACCEPTED_RULE_IDENTITY_VALIDATED"])
        validation = O.validate_accepted_rule_identity(
            O.AcceptedRuleIdentity(
                SYNTHETIC_ACCEPTED_RULE_PATH, "a" * 64, digest
            ),
            rule_reader=_in_memory_rule_reader,
            manifest_provider=_in_memory_manifest_provider,
        )
        self.assertEqual(validation["VALIDATION_STATUS"], "FAIL_CLOSED")
        self.assertEqual(validation["ACTUAL_RAW_SHA256"], raw_sha)
        stages = {stage["STAGE"]: stage["PASS"] for stage in validation["STAGES"]}
        self.assertFalse(
            stages["INVOCATION_TIME_EXPECTED_RAW_SHA256_COMPARISON"]
        )

    def test_invocation_time_rule_semantic_digest_mismatch_fails_closed(self) -> None:
        # R
        validation = O.validate_accepted_rule_identity(
            O.AcceptedRuleIdentity(
                SYNTHETIC_ACCEPTED_RULE_PATH,
                _synthetic_rule_identity()[1],
                "b" * 64,
            ),
            rule_reader=_in_memory_rule_reader,
            manifest_provider=_in_memory_manifest_provider,
        )
        self.assertEqual(validation["VALIDATION_STATUS"], "FAIL_CLOSED")
        stages = {stage["STAGE"]: stage["PASS"] for stage in validation["STAGES"]}
        self.assertTrue(stages["INVOCATION_TIME_EXPECTED_RAW_SHA256_COMPARISON"])
        self.assertFalse(
            stages["INVOCATION_TIME_EXPECTED_SEMANTIC_DIGEST_COMPARISON"]
        )

    def test_qa_debug_scope_drift_is_fail_closed_in_the_rule_scope(self) -> None:
        # S: the QA_DEBUG_SCOPE raw state is captured by the accepted rule; the
        # observer reads it and never writes it.  A drifted conditional scope
        # key is detected by the payload binding witness and fails the purity
        # witness.
        witness = O.canonical_telemetry_payload_binding_witness()
        self.assertIn("QA_DEBUG_SCOPE", witness["CANONICAL_CONDITIONAL_SCOPE_ENTRY"])
        self.assertIn("QA_DEBUG_SCOPE", witness["OBSERVER_CONDITIONAL_SCOPE_ENTRY"])
        drifted = _mutated_timed_telemetry_scope_condition()
        purity = _assert_purity_fails(self, drifted)
        self.assertEqual(
            purity["TELEMETRY_PAYLOAD_BINDING_WITNESS"][
                "TELEMETRY_PAYLOAD_BINDING_EQUIVALENCE"
            ],
            "FAIL",
        )
        self.assertEqual(_attribute_assignment_violations(_observer_tree()), [])
        self.assertIsNone(os.environ.get("QA_DEBUG_SCOPE"))
        self.assertFalse(os.getenv("QA_DEBUG_SCOPE"))

    def test_current_pre_g2_accepted_rule_fails_closed_after_g2_correction(
        self,
    ) -> None:
        # V: the CURRENT pre-G2 accepted TPR1 artifact, validated against the
        # post-G2 source / immutable-surface state, must fail closed; production
        # validation runs with BOTH the source-binding and the immutable-surface
        # precondition checks enabled and the real governed artifact read.
        validation = O.validate_accepted_rule_identity(
            O.AcceptedRuleIdentity(
                ACCEPTED_TPR1_RULE_RELATIVE_PATH,
                ACCEPTED_TPR1_RULE_RAW_SHA256,
                ACCEPTED_TPR1_RULE_SEMANTIC_DIGEST,
            )
        )
        self.assertEqual(validation["VALIDATION_STATUS"], "FAIL_CLOSED")
        self.assertEqual(validation["FAIL_CLOSED"], "YES")
        stages = {stage["STAGE"]: stage for stage in validation["STAGES"]}
        self.assertTrue(stages["LOCATOR_RESOLUTION_INSIDE_ACTIVE_WORKSPACE"]["PASS"])
        self.assertTrue(stages["REGULAR_FILE_NOT_REPARSE_NOT_OUTSIDE_ROOT"]["PASS"])
        self.assertTrue(stages["INVOCATION_TIME_EXPECTED_RAW_SHA256_COMPARISON"]["PASS"])
        self.assertTrue(
            stages["INVOCATION_TIME_EXPECTED_SEMANTIC_DIGEST_COMPARISON"]["PASS"]
        )
        self.assertTrue(stages["PERMISSION_SEMANTIC_VALIDATION"]["PASS"])
        self.assertFalse(stages["SOURCE_BINDING_VALIDATION"]["PASS"])
        self.assertFalse(
            stages["IMMUTABLE_SURFACE_PRECONDITION_VALIDATION"]["PASS"]
        )
        stale = [
            issue
            for issue in stages["SOURCE_BINDING_VALIDATION"]["ISSUES"]
            if "drifted" in issue
        ]
        self.assertTrue(stale)
        self.assertTrue(
            any(
                "observe_v4_ws13_citation_fresh_attribution.py" in issue
                for issue in stale
            )
        )
        self.assertTrue(
            any(
                "test_v4_ws13_citation_fresh_attribution.py" in issue
                for issue in stale
            )
        )
        # The immutable-surface precondition is evaluated even though the source
        # binding drift is already established, and it independently fails.
        surface_issues = stages["IMMUTABLE_SURFACE_PRECONDITION_VALIDATION"][
            "ISSUES"
        ]
        self.assertTrue(
            any("baseline digest drifted" in issue for issue in surface_issues)
        )
        self.assertEqual(
            O.TPR1_PERMISSION_SEMANTICS_ACCEPTED, "YES"
        )
        self.assertEqual(O.TPR1_RULE_ARTIFACT_BYTES_STABLE, "YES")
        self.assertEqual(O.TPR1_PERMISSION_SEMANTICS_ACCEPTED, "YES")
        self.assertEqual(O.TPR1_RULE_BINDINGS_STILL_MATCH_POST_G2_STATE, "NO")
        self.assertEqual(
            O.TPR1_RULE_REBIND_OR_AMENDMENT_REQUIRED_BEFORE_G4, "YES"
        )

    def test_future_rule_identity_can_change_without_observer_source_change(
        self,
    ) -> None:
        # W: a different reviewer-bound rule locator + raw SHA256 + semantic
        # digest supplied through the invocation-time governance inputs is
        # mechanically validated without modifying the observer source.
        observer_before = _observer_source_text()
        rule_object = _synthetic_accepted_rule_object()
        rule_object["short_id"] = "SYNTHETIC_TEST_ONLY_FUTURE_ACCEPTED_RULE_V2"
        rule_object["checkpoint"] = "SYNTHETIC_TEST_ONLY_FUTURE_RULE_REVISION"
        raw_bytes = json.dumps(
            rule_object,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        identity = O.AcceptedRuleIdentity(
            "eval/SYNTHETIC_TEST_ONLY_FUTURE_ACCEPTED_RULE_V2.json",
            hashlib.sha256(raw_bytes).hexdigest(),
            O.rule_semantic_digest(rule_object),
        )
        self.assertNotEqual(
            identity.raw_sha256,
            SYNTHETIC_ACCEPTED_RULE_PATH and _synthetic_rule_identity()[1],
        )
        validation = O.validate_accepted_rule_identity(
            identity,
            rule_reader=lambda _path: raw_bytes,
            manifest_provider=_in_memory_manifest_provider,
        )
        stages = {stage["STAGE"]: stage["PASS"] for stage in validation["STAGES"]}
        for stage_name in O.ACCEPTED_RULE_IDENTITY_VERIFICATION_STAGES:
            with self.subTest(stage=stage_name):
                self.assertIn(stage_name, stages)
        self.assertTrue(stages["LOCATOR_RESOLUTION_INSIDE_ACTIVE_WORKSPACE"])
        self.assertTrue(stages["INVOCATION_TIME_EXPECTED_RAW_SHA256_COMPARISON"])
        self.assertTrue(
            stages["INVOCATION_TIME_EXPECTED_SEMANTIC_DIGEST_COMPARISON"]
        )
        self.assertTrue(stages["PERMISSION_SEMANTIC_VALIDATION"])
        self.assertTrue(stages["SOURCE_BINDING_VALIDATION"])
        self.assertTrue(stages["IMMUTABLE_SURFACE_PRECONDITION_VALIDATION"])
        self.assertEqual(validation["VALIDATION_STATUS"], "PASS")
        self.assertEqual(validation["RULE_LOCATOR"], identity.relative_path)
        self.assertEqual(
            validation["ACTUAL_SEMANTIC_DIGEST"], identity.semantic_digest
        )
        self.assertEqual(_observer_source_text(), observer_before)
        self.assertNotIn(identity.relative_path, observer_before)
        self.assertNotIn(identity.raw_sha256, observer_before)
        self.assertNotIn(identity.semantic_digest, observer_before)
        assertions = O.eq4_required_assertions()
        self.assertEqual(
            assertions["FUTURE_G4_ACCEPTED_RULE_IDENTITY"],
            "REQUIRED_INVOCATION_TIME_GOVERNANCE_INPUT",
        )
        self.assertEqual(
            assertions["FUTURE_G4_RULE_IDENTITY_SOURCE"],
            "SEPARATELY_REVIEWER_AUTHORIZED_G4_INVOCATION_CONTRACT",
        )

    def test_observer_source_pins_no_accepted_rule_identity(self) -> None:
        source = _observer_source_text()
        violations = O.observer_pinned_rule_identity_violations(
            source,
            forbidden_literals=(
                ACCEPTED_TPR1_RULE_RAW_SHA256,
                ACCEPTED_TPR1_RULE_SEMANTIC_DIGEST,
            ),
        )
        self.assertEqual(violations, [])
        self.assertNotIn(ACCEPTED_TPR1_RULE_RAW_SHA256, source)
        self.assertNotIn(ACCEPTED_TPR1_RULE_SEMANTIC_DIGEST, source)
        self.assertNotIn(ACCEPTED_TPR1_RULE_RELATIVE_PATH, source)
        assertions = O.eq4_required_assertions()
        self.assertEqual(
            assertions["OBSERVER_SOURCE_HARDCODES_ACCEPTED_RULE_IDENTITY"], "NO"
        )
        self.assertEqual(assertions["OBSERVER_SELF_DECIDES_ACCEPTED_RULE"], "NO")
        self.assertEqual(
            assertions["G4_SIDE_EFFECT_POLICY_ALONE_IS_SUFFICIENT_AUTHORIZATION"],
            "NO",
        )
        contract = O.describe_contract()
        self.assertEqual(contract["accepted_rule_identity_is_invocation_time"], "YES")
        self.assertEqual(
            contract["observer_source_pins_accepted_rule_identity"], "NO"
        )


class G2Eq4AssertionBlockTest(unittest.TestCase):
    def test_eq4_required_assertions_pass(self) -> None:
        assertions = O.eq4_required_assertions()
        self.assertEqual(assertions["CHECKPOINT"], "WS13_G2_OBSERVER_EQUIVALENCE_CORRECTION_004")
        self.assertEqual(assertions["SHORT_ID"], "G2_EQ4")
        self.assertEqual(assertions["REQUIRED_FIX_COUNT"], 3)
        self.assertEqual(
            assertions["FIX_1_REMOVE_PRE_EVALUATOR_CLOSE_RETURN_PACKAGING"], "PASS"
        )
        self.assertEqual(
            assertions["FIX_2_TIMED_REGION_WITNESS_EXHAUSTIVENESS"], "PASS"
        )
        self.assertEqual(
            assertions["FIX_3_CANONICAL_TIMED_MODEL_LOCK_AND_TELEMETRY_SEMANTICS"],
            "PASS",
        )
        self.assertEqual(
            assertions["OBSERVATION_EQUIVALENCE_ESTABLISHED_BY_STATIC_SYNTHETIC_G2_TESTS"],
            "YES",
        )
        self.assertEqual(assertions["TPR1_PERMISSION_SEMANTICS_ACCEPTED"], "YES")
        self.assertEqual(
            assertions["TPR1_RULE_REBIND_OR_AMENDMENT_REQUIRED_BEFORE_G4"], "YES"
        )
        self.assertEqual(
            assertions["AUTHORIZED_TELEMETRY_OPERATION_MULTIPLICITY"],
            "EXACTLY_ONE_CANONICAL_WRITE_TELEMETRY_INVOCATION_PER_AUTHORIZED_"
            "CANONICAL_ANSWER_EXECUTION",
        )
        self.assertEqual(
            assertions["CANONICAL_TELEMETRY_IO_FAILURE_PROPAGATES"], "NO"
        )
        self.assertEqual(
            assertions["TELEMETRY_APPEND_SUCCESS_REQUIRED_FOR_RUN_ACCEPTANCE"],
            "NO",
        )

    def test_live_envelope_carries_the_eq4_blocks(self) -> None:
        payload = base_payload()
        self.assertEqual(payload["EQ3_REQUIRED_ASSERTIONS"]["REQUIRED_FIX_COUNT"], 1)
        purity = payload["CANONICAL_MEASUREMENT_TIMED_BODY_PURITY_WITNESS"]
        self.assertEqual(purity["CANONICAL_MEASUREMENT_TIMED_BODY_PURITY"], "PASS")
        self.assertEqual(
            purity["PRE_EVALUATOR_CLOSE_OBSERVER_RETURN_PACKAGING"], "NONE"
        )
        self.assertEqual(purity["RETURN_WITNESS_BLIND_SPOT"], "CLOSED")
        self.assertEqual(
            purity["MODEL_LOCK_TIMED_SEMANTICS"],
            O.MODEL_LOCK_TIMED_SEMANTICS,
        )
        self.assertEqual(
            purity["CANONICAL_TELEMETRY_TIMED_SEMANTICS"],
            O.CANONICAL_TELEMETRY_TIMED_SEMANTICS,
        )
        self.assertEqual(
            payload["RUN_BINDINGS"]["accepted_rule_identity"]["relative_path"],
            SYNTHETIC_ACCEPTED_RULE_PATH,
        )
        self.assertEqual(
            payload["RUN_BINDINGS"]["accepted_rule_identity"]["raw_sha256"],
            _synthetic_rule_identity()[1],
        )
        self.assertEqual(
            payload["RUN_BINDINGS"]["accepted_rule_identity"]["semantic_digest"],
            _synthetic_rule_identity()[2],
        )
        self.assertEqual(
            payload["RUN_BINDINGS"]["accepted_rule_identity"]["identity_source"],
            O.FUTURE_G4_RULE_IDENTITY_SOURCE,
        )
        self.assertEqual(
            payload["COUNTERS"]["TARGET_OBSERVATION_RUNS"], 1
        )


# --------------------------------------------------------------------------- #
# Mandatory G2 test-category coverage registry
# --------------------------------------------------------------------------- #
MANDATORY_G2_TEST_CATEGORIES = (
    "01_ACCEPTED_G1_CHAIN_BINDINGS",
    "02_TARGET_ALLOWLIST",
    "03_CONTROL_DENYLIST",
    "04_RUN_ORDINAL_ALLOWLIST",
    "05_STATIC_SCHEMA_MODE_ZERO_CALL",
    "06_MISSING_G4_AUTHORIZATION_ZERO_CALL_FAIL",
    "07_MISSING_EXTERNAL_BINDING_ZERO_CALL_FAIL",
    "08_REQUIRED_OBSERVATION_GROUPS_AND_FIELDS",
    "09_SEMANTIC_PROVENANCE_SEPARATION",
    "10_SENT_EVIDENCE_TEXT_HASH_CONTRACT",
    "11_OBSERVATION_SEMANTIC_DIGEST_CANONICALIZATION",
    "12_PROVENANCE_DIGEST_INVARIANCE",
    "13_CANONICAL_ADAPTER_PRESERVES_SEMANTIC_ARGUMENTS",
    "14_RAW_FINAL_ANSWER_DISTINCT",
    "15_VERIFIER_EVALUATOR_CAPTURE_WITHOUT_REINTERPRETATION",
    "16_OBSERVER_SELF_WRITE_FREE",
    "17_NO_PRODUCT_GOLDEN_EVALUATOR_VERIFIER_DB_MUTATION_PATH",
    "18_STDOUT_ONLY_OUTPUT_CONTRACT",
    "19_NO_CLASSIFIER_READINESS_IMPLEMENTATION",
    "20_UNRESOLVED_G4_SIDE_EFFECT_POLICY_ZERO_CALL_FAIL",
    "21_G2_EQ1_CANONICAL_EVALUATOR_NONSTREAMING_BRANCH",
    "22_G2_EQ1_CURRENT_REQUEST_IDENTITY_CAPTURE",
    "23_G2_EQ1_RAW_FINAL_CAPTURE_EQUIVALENCE",
    "24_G2_EQ1_FULL_CANONICAL_QA_SEMANTIC_SEQUENCE",
    "25_G2_EQ1_EXTRA_READ_ONLY_CAPTURE_ACCOUNTING",
    "26_G2_EQ1_ZERO_REAL_CALL",
    "27_G2_EQ2_CANONICAL_MEASUREMENT_TIMER_BOUNDARY",
    "28_G2_EQ2_REQUEST_IDENTITY_BOOLEAN_SEMANTICS",
    "29_G2_EQ2_CANONICAL_PIPELINE_GENERATION_BINDING",
    "30_G2_EQ3_ENGINE_TIMED_REGION_PURITY",
    "31_G2_EQ3_EVALUATOR_OUTER_TIMED_REGION_PURITY",
    "32_G2_EQ3_TIMED_REGION_CONTAMINATION_FAIL_CLOSED",
    "33_G2_EQ3_POST_TIMER_CONSUMER_AND_INVARIANCE",
    "34_G2_EQ4_SAME_FRAME_AND_RETURN_PACKAGING",
    "35_G2_EQ4_TIMED_REGION_WITNESS_EXHAUSTIVENESS",
    "36_G2_EQ4_TIMED_MODEL_LOCK_AND_TELEMETRY_SEMANTICS",
    "37_G2_EQ4_SYNTHETIC_TELEMETRY_INVOCATION_AND_IO_FAILURE",
    "38_G2_EQ4_INVOCATION_TIME_ACCEPTED_RULE_IDENTITY",
    "39_G2_EQ4_NO_PINNED_RULE_IDENTITY_IN_OBSERVER_SOURCE",
    "40_G2_EQ4_REQUIRED_ASSERTION_BLOCK",
)
MANDATORY_G2_TEST_CATEGORY_COUNT = 40

CATEGORY_TEST_METHODS = {
    "01_ACCEPTED_G1_CHAIN_BINDINGS": (
        "test_g0_preflight_raw_sha256_matches_the_accepted_identity",
        "test_accepted_g1_base_raw_sha256_matches",
        "test_accepted_g1_a001_raw_sha256_matches",
        "test_accepted_g1_a001_fc1_raw_sha256_matches",
        "test_base_design_semantic_payload_digest_recomputes",
        "test_amendment_semantic_payload_digest_recomputes",
        "test_effective_design_chain_digest_recomputes_to_the_operative_value",
        "test_fc1_boundary_correction_payload_digest_recomputes",
        "test_observer_chain_recomputation_reports_every_check_matching",
        "test_validate_bindings_mode_reports_valid",
    ),
    "02_TARGET_ALLOWLIST": (
        "test_primary_target_case_ids_is_the_frozen_singleton",
        "test_guard_accepts_the_frozen_primary_target",
        "test_live_guard_rejects_a_non_allowlisted_case_with_zero_calls",
    ),
    "03_CONTROL_DENYLIST": (
        "test_control_case_ids_is_empty",
        "test_guard_evaluates_the_control_denylist_for_the_target",
        "test_live_guard_rejects_any_control_case_with_zero_calls",
    ),
    "04_RUN_ORDINAL_ALLOWLIST": (
        "test_run_ordinals_are_the_frozen_triple",
        "test_guard_allows_every_authorized_ordinal",
        "test_live_guard_rejects_ordinals_outside_the_allowlist",
    ),
    "05_STATIC_SCHEMA_MODE_ZERO_CALL": (
        "test_describe_contract_is_static_and_authorizes_no_live_execution",
        "test_validate_bindings_is_static_and_reports_zero_calls",
        "test_cli_static_modes_emit_json_on_stdout",
        "test_static_modes_never_trigger_a_real_call_boundary",
        "test_validate_observation_mode_is_static_and_zero_call",
    ),
    "06_MISSING_G4_AUTHORIZATION_ZERO_CALL_FAIL": (
        "test_live_without_g4_authorization_blocks_with_zero_calls",
        "test_blank_g4_authorization_blocks_with_zero_calls",
        "test_g4_authorization_absent_skips_every_deep_check",
    ),
    "07_MISSING_EXTERNAL_BINDING_ZERO_CALL_FAIL": (
        "test_missing_observer_sha256_blocks_with_zero_calls",
        "test_mismatching_observer_sha256_blocks_with_zero_calls",
        "test_missing_classifier_sha256_blocks_with_zero_calls",
        "test_missing_future_tests_sha256_blocks_with_zero_calls",
        "test_missing_effective_design_digest_blocks_with_zero_calls",
        "test_mismatching_effective_design_digest_blocks_with_zero_calls",
        "test_mismatching_accepted_g1_chain_sha256_blocks_with_zero_calls",
        "test_every_blocked_payload_reports_all_counters_zero",
    ),
    "08_REQUIRED_OBSERVATION_GROUPS_AND_FIELDS": (
        "test_group_order_equals_the_accepted_g1_schema",
        "test_group_field_map_equals_the_effective_superseded_schema",
        "test_field_contract_metadata_equals_the_accepted_g1_schema",
        "test_field_entry_key_order_is_the_frozen_order",
        "test_observation_record_carries_exactly_the_frozen_groups",
        "test_every_frozen_field_is_present_in_a_synthetic_observation",
        "test_observation_schema_version_is_the_frozen_version",
    ),
    "09_SEMANTIC_PROVENANCE_SEPARATION": (
        "test_effective_semantic_key_set_equals_the_artifact_derived_62",
        "test_base_and_effective_key_counts_match_the_amendment_declaration",
        "test_provenance_key_set_equals_the_frozen_eight",
        "test_semantic_and_provenance_sets_are_disjoint",
        "test_removed_ambiguous_key_is_absent_and_the_three_new_keys_present",
        "test_digest_payload_keys_equal_the_frozen_semantic_key_set",
        "test_provenance_only_keys_never_enter_the_semantic_payload",
        "test_run_ordinal_is_semantic_while_run_id_is_provenance",
        "test_provenance_block_carries_only_the_bare_provenance_fields",
    ),
    "10_SENT_EVIDENCE_TEXT_HASH_CONTRACT": (
        "test_correct_text_and_hash_pair_is_accepted",
        "test_text_only_record_is_rejected",
        "test_hash_only_record_is_rejected",
        "test_hash_mismatch_is_rejected",
        "test_record_shape_violation_is_rejected",
        "test_non_hex_hash_is_rejected",
        "test_exact_text_hashing_is_preserved_without_normalization",
        "test_order_preservation_is_checked_against_sent_context_ids",
        "test_synthetic_observation_satisfies_the_contract",
    ),
    "11_OBSERVATION_SEMANTIC_DIGEST_CANONICALIZATION": (
        "test_canonical_json_rule_matches_the_frozen_serialization",
        "test_canonical_rule_does_not_escape_non_ascii",
        "test_digest_is_stable_across_repeated_computations",
        "test_digest_is_independent_of_record_key_order",
        "test_changing_run_ordinal_changes_the_digest",
        "test_changing_a_semantic_field_changes_the_digest",
        "test_changing_sent_evidence_text_changes_the_digest",
        "test_changing_sent_evidence_content_sha256_changes_the_digest",
        "test_changing_sent_context_id_changes_the_digest",
        "test_digest_matches_the_envelope_declared_digest",
    ),
    "12_PROVENANCE_DIGEST_INVARIANCE": (
        "test_changing_run_id_leaves_the_digest_unchanged",
        "test_changing_the_provenance_block_leaves_the_digest_unchanged",
        "test_removing_the_provenance_block_leaves_the_digest_unchanged",
        "test_provenance_mutation_is_reported_as_valid_by_the_key_set_check",
    ),
    "13_CANONICAL_ADAPTER_PRESERVES_SEMANTIC_ARGUMENTS": (
        "test_prepare_receives_the_canonical_query_history_and_scope",
        "test_build_messages_receives_the_prepared_question_contexts_and_route",
        "test_model_call_receives_only_the_canonical_messages_and_answer_model",
        "test_observer_passes_no_semantic_or_inference_option_override",
        "test_exactly_one_retrieval_and_one_model_call_per_synthetic_run",
        "test_canonical_qa_top_k_binding_matches_the_engine_source",
        "test_canonical_retrieval_query_binding_matches_the_engine_source",
        "test_retrieval_query_recorded_is_the_canonical_normalized_question",
        "test_scope_assertion_uses_the_resolved_scope_and_known_documents",
        "test_canonical_parsers_agree_on_normalized_answers",
    ),
    "14_RAW_FINAL_ANSWER_DISTINCT": (
        "test_raw_answer_is_the_exact_canonical_chat_return",
        "test_raw_and_final_answers_are_captured_at_distinct_points",
        "test_final_answer_equals_the_canonical_postprocessing_chain",
        "test_final_answer_is_never_copied_from_the_raw_answer",
        "test_final_answer_matches_the_canonical_result_object",
    ),
    "15_VERIFIER_EVALUATOR_CAPTURE_WITHOUT_REINTERPRETATION": (
        "test_verifier_output_is_recorded_verbatim_from_the_canonical_report",
        "test_alignment_result_is_derived_only_from_the_canonical_report",
        "test_invalid_and_scope_violation_counts_come_from_the_report",
        "test_verifier_receives_the_pre_renumber_answer_and_sent_evidence",
        "test_evaluator_output_is_the_canonical_evaluator_row_verbatim",
        "test_measurement_uses_the_real_canonical_evaluator_row",
        "test_real_canonical_verifier_reports_its_frozen_version",
        "test_fact_matcher_output_comes_from_the_canonical_row",
        "test_expected_fact_presence_matches_the_canonical_membership_rule",
        "test_evaluator_and_verifier_versions_come_from_canonical_constants",
        "test_observer_defines_no_second_verifier_or_fact_matcher",
        "test_required_support_reached_generation_uses_the_sent_evidence_text",
    ),
    "16_OBSERVER_SELF_WRITE_FREE": (
        "test_observer_source_has_no_writer_calls",
        "test_observer_opens_only_read_only_inputs",
        "test_observer_has_no_attribute_or_environment_assignment",
        "test_observer_self_sha_is_not_pinned_in_its_own_source",
        "test_observer_exposes_no_self_sha_constant",
        "test_static_contract_declares_the_write_free_contract",
        "test_blocked_and_live_payloads_write_nothing",
    ),
    "17_NO_PRODUCT_GOLDEN_EVALUATOR_VERIFIER_DB_MUTATION_PATH": (
        "test_observer_imports_no_writer_capable_modules",
        "test_observer_never_opens_a_governed_artifact_for_writing",
        "test_observer_has_no_runtime_database_write_path",
        "test_observer_does_not_mutate_configuration_or_environment",
        "test_governed_artifacts_are_byte_identical_after_the_test_doubles",
    ),
    "18_STDOUT_ONLY_OUTPUT_CONTRACT": (
        "test_observer_declares_no_output_file_option",
        "test_observer_uses_no_direct_stream_writes",
        "test_static_mode_payload_arrives_on_stdout",
        "test_validate_observation_reads_stdin_for_dash",
        "test_invalid_payload_exits_non_zero_without_touching_a_real_call",
    ),
    "19_NO_CLASSIFIER_READINESS_IMPLEMENTATION": (
        "test_observer_source_contains_no_classifier_or_readiness_vocabulary",
        "test_observation_record_carries_no_classifier_or_readiness_keys",
        "test_static_contract_does_not_publish_classifier_outputs",
        "test_live_envelope_declares_no_scientific_outcome",
        "test_observer_defines_no_classifier_or_readiness_helper",
    ),
    "20_UNRESOLVED_G4_SIDE_EFFECT_POLICY_ZERO_CALL_FAIL": (
        "test_live_without_side_effect_policy_blocks_with_zero_calls",
        "test_missing_authorization_and_policy_together_blocks_with_zero_calls",
        "test_live_run_records_the_resolved_side_effect_policy",
        "test_side_effect_declaration_enumerates_every_known_runtime_write",
        "test_observer_never_disables_telemetry_or_redirects_the_cache",
    ),
    "21_G2_EQ1_CANONICAL_EVALUATOR_NONSTREAMING_BRANCH": (
        "test_canonical_evaluator_answer_call_supplies_no_on_token",
        "test_engine_answer_default_on_token_is_none",
        "test_on_token_none_selects_the_non_streaming_chat_call",
        "test_on_token_none_does_not_select_chat_stream",
        "test_canonical_branch_witness_reports_pass",
        "test_observer_default_model_call_is_the_canonical_non_streaming_chat",
        "test_observer_live_path_contains_no_chat_stream_call",
    ),
    "22_G2_EQ1_CURRENT_REQUEST_IDENTITY_CAPTURE": (
        "test_current_real_chat_request_is_captured_without_network",
        "test_captured_current_request_is_non_streaming",
        "test_captured_request_identity_equals_the_observer_identity",
        "test_captured_payload_keys_equal_the_derived_payload_keys",
        "test_captured_model_binding_matches_the_source_expression",
        "test_current_identity_is_compared_to_the_anchor_separately",
        "test_derivation_does_not_reference_the_frozen_anchor",
        "test_frozen_anchor_is_corroborated_by_the_historical_evidence",
        "test_current_request_identity_is_recorded_in_the_synthetic_observation",
    ),
    "23_G2_EQ1_RAW_FINAL_CAPTURE_EQUIVALENCE": (
        "test_raw_answer_is_the_direct_canonical_chat_return",
        "test_final_answer_is_the_canonical_postprocessed_result",
        "test_observer_contains_no_manual_token_joining",
        "test_raw_final_capture_witness_reports_the_direct_assignment",
    ),
    "24_G2_EQ1_FULL_CANONICAL_QA_SEMANTIC_SEQUENCE": (
        "test_full_canonical_qa_semantic_sequence_witness_passes",
        "test_every_canonical_marker_exists_in_its_current_source",
        "test_canonical_markers_follow_the_declared_source_order",
        "test_observer_markers_follow_the_declared_observer_order",
        "test_semantic_operations_are_all_preserved",
        "test_observer_sequence_carries_the_required_semantic_operations",
        "test_synthetic_run_executes_each_semantic_operation_exactly_once",
        "test_support_check_runs_on_a_valid_citation_synthetic_answer",
        "test_only_proven_nonsemantic_wrapper_behavior_is_omitted",
        "test_semantic_classes_and_omission_classes_are_from_the_vocabulary",
    ),
    "25_G2_EQ1_EXTRA_READ_ONLY_CAPTURE_ACCOUNTING": (
        "test_every_extra_call_is_accounted_for",
        "test_every_extra_call_proves_the_read_only_property_bundle",
        "test_classification_critical_operations_are_not_duplicated",
        "test_scope_resolution_mirrors_the_canonical_two_call_shape",
        "test_classification_critical_operations_audit_reports_single_execution",
        "test_library_read_paths_are_provably_read_only",
        "test_scope_group_uses_the_reused_canonical_values",
    ),
    "26_G2_EQ1_ZERO_REAL_CALL": (
        "test_g2_eq1_suites_trigger_no_real_call_boundary",
        "test_static_modes_report_zero_counters_for_the_correction",
        "test_capture_helper_performs_zero_network_calls",
        "test_required_correction_assertion_block_reports_the_frozen_values",
        "test_live_envelope_reports_the_correction_blocks",
    ),
    "27_G2_EQ2_CANONICAL_MEASUREMENT_TIMER_BOUNDARY": (
        "test_engine_result_timer_start_source_is_mechanically_derived",
        "test_engine_result_timer_end_result_witness",
        "test_evaluator_row_timer_start_source_is_mechanically_derived",
        "test_evaluator_row_timer_end_build_row_witness",
        "test_engine_construction_excluded_or_included_exactly_as_source_requires",
        "test_observer_engine_result_interval_matches_canonical",
        "test_observer_evaluator_row_interval_matches_canonical",
        "test_deterministic_clock_proves_intervals_are_not_conflated",
        "test_answer_result_elapsed_ms_comes_from_the_engine_timer",
        "test_evaluator_output_elapsed_ms_comes_from_the_evaluator_timer",
        "test_full_semantic_witness_fails_when_timer_boundaries_are_shifted",
        "test_observer_timer_reads_are_exactly_the_canonical_timer_reads",
    ),
    "28_G2_EQ2_REQUEST_IDENTITY_BOOLEAN_SEMANTICS": (
        "test_current_request_identity_not_copied_field_is_yes",
        "test_current_request_identity_copied_field_is_no",
        "test_observation_semantic_record_carries_the_correct_polarity",
        "test_copied_key_is_bound_to_the_copied_constant_only",
    ),
    "29_G2_EQ2_CANONICAL_PIPELINE_GENERATION_BINDING": (
        "test_active_canonical_binding_contains_ollama_client_chat",
        "test_active_canonical_binding_excludes_chat_stream",
        "test_chat_stream_is_only_labelled_alternative_callback_branch",
        "test_binding_map_agrees_with_the_canonical_evaluator_branch_witness",
    ),
    "30_G2_EQ3_ENGINE_TIMED_REGION_PURITY": (
        "test_engine_timed_region_derivation_yields_the_canonical_sequence",
        "test_engine_extra_and_missing_detection",
        "test_engine_operation_order_is_preserved",
        "test_engine_multiplicity_equivalence",
        "test_nested_engine_hierarchical_equivalence",
        "test_flattened_nested_operations_are_rejected",
    ),
    "31_G2_EQ3_EVALUATOR_OUTER_TIMED_REGION_PURITY": (
        "test_evaluator_outer_timed_region_derivation",
        "test_evaluator_outer_extra_and_missing_detection",
        "test_evaluator_outer_operation_order_is_preserved",
        "test_evaluator_outer_multiplicity_equivalence",
        "test_build_row_inside_evaluator_interval_is_rejected",
        "test_capture_before_build_row_is_rejected",
    ),
    "32_G2_EQ3_TIMED_REGION_CONTAMINATION_FAIL_CLOSED": (
        "test_counter_mutation_inside_engine_timer_is_rejected",
        "test_schema_construction_inside_timers_is_rejected",
        "test_scope_group_inside_engine_timer_is_rejected",
        "test_retrieval_group_inside_engine_timer_is_rejected",
        "test_branch_support_helper_inside_engine_timer_is_rejected",
        "test_prepare_moved_outside_engine_timer_is_rejected",
        "test_duplicate_prepare_is_rejected",
        "test_duplicated_canonical_operation_is_rejected",
        "test_engine_timer_start_moved_before_construction_is_rejected",
        "test_nested_region_restarting_evaluator_timer_is_rejected",
        "test_capture_package_before_evaluator_close_is_rejected",
    ),
    "33_G2_EQ3_POST_TIMER_CONSUMER_AND_INVARIANCE": (
        "test_post_timer_bookkeeping_does_not_change_engine_elapsed",
        "test_post_timer_bookkeeping_does_not_change_evaluator_elapsed",
        "test_eq3_live_envelope_and_assertion_block_pass",
        "test_request_identity_polarity_regression",
        "test_active_canonical_generation_binding_regression",
        "test_active_pipeline_chat_stream_absence_regression",
    ),
    "34_G2_EQ4_SAME_FRAME_AND_RETURN_PACKAGING": (
        "test_live_path_is_a_single_frame",
        "test_no_observer_transport_packaging_return_exists",
        "test_canonical_branch_outcome_is_read_from_the_canonical_result",
        "test_return_tuple_before_evaluator_close_is_rejected",
        "test_return_list_before_evaluator_close_is_rejected",
        "test_return_dict_before_evaluator_close_is_rejected",
        "test_return_custom_capture_package_before_close_is_rejected",
        "test_return_before_engine_timer_close_is_rejected",
    ),
    "35_G2_EQ4_TIMED_REGION_WITNESS_EXHAUSTIVENESS": (
        "test_actual_ast_enumeration_is_the_completeness_authority",
        "test_every_ledger_entry_carries_the_required_fields",
        "test_ledger_covers_every_required_node_type",
        "test_unknown_observer_call_in_timed_region_is_rejected",
        "test_unknown_timed_assignment_is_classified_or_rejected",
        "test_unknown_timed_with_is_classified_or_rejected",
        "test_unknown_timed_return_is_classified_or_rejected",
        "test_covered_expression_occurrences_are_in_the_ledger",
    ),
    "36_G2_EQ4_TIMED_MODEL_LOCK_AND_TELEMETRY_SEMANTICS": (
        "test_model_lock_and_telemetry_are_mirrored_not_omitted",
        "test_telemetry_payload_is_bound_to_the_canonical_payload",
        "test_duplicate_telemetry_operation_fails_multiplicity",
        "test_duplicate_model_lock_fails_multiplicity",
        "test_missing_canonical_occurrence_fails",
        "test_model_lock_absent_from_measured_interval_fails",
        "test_canonical_timed_operation_outside_the_timer_fails",
        "test_omitted_canonical_telemetry_fails",
        "test_telemetry_is_not_declared_nonsemantic_for_an_unused_return",
        "test_model_lock_is_not_declared_nonsemantic_for_absent_contention",
        "test_engine_timed_operation_order_is_still_preserved",
    ),
    "37_G2_EQ4_SYNTHETIC_TELEMETRY_INVOCATION_AND_IO_FAILURE": (
        "test_synthetic_telemetry_path_invokes_the_canonical_operation_once",
        "test_synthetic_telemetry_io_failure_does_not_change_answer_semantics",
        "test_eq3_live_envelope_and_assertion_block_pass",
    ),
    "38_G2_EQ4_INVOCATION_TIME_ACCEPTED_RULE_IDENTITY": (
        "test_side_effect_policy_alone_is_not_authorization",
        "test_invocation_time_rule_raw_sha_mismatch_fails_closed",
        "test_invocation_time_rule_semantic_digest_mismatch_fails_closed",
        "test_qa_debug_scope_drift_is_fail_closed_in_the_rule_scope",
        "test_current_pre_g2_accepted_rule_fails_closed_after_g2_correction",
        "test_future_rule_identity_can_change_without_observer_source_change",
    ),
    "39_G2_EQ4_NO_PINNED_RULE_IDENTITY_IN_OBSERVER_SOURCE": (
        "test_observer_source_pins_no_accepted_rule_identity",
        "test_future_rule_identity_can_change_without_observer_source_change",
    ),
    "40_G2_EQ4_REQUIRED_ASSERTION_BLOCK": (
        "test_eq4_required_assertions_pass",
        "test_live_envelope_carries_the_eq4_blocks",
    ),
}


def missing_mandatory_g2_test_categories() -> list[str]:
    """Mandatory categories without a declared mechanical test method list."""
    return [
        category
        for category in MANDATORY_G2_TEST_CATEGORIES
        if category not in CATEGORY_TEST_METHODS
    ]


def _module_test_method_names() -> list[str]:
    names: list[str] = []
    for node in ast.walk(_test_tree()):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
            "test"
        ):
            names.append(node.name)
    return names


class G2TestCategoryCoverageTest(unittest.TestCase):
    def test_mandatory_category_count_is_frozen(self) -> None:
        self.assertEqual(
            len(MANDATORY_G2_TEST_CATEGORIES), MANDATORY_G2_TEST_CATEGORY_COUNT
        )
        self.assertEqual(
            len(set(MANDATORY_G2_TEST_CATEGORIES)),
            MANDATORY_G2_TEST_CATEGORY_COUNT,
        )
        self.assertEqual(MANDATORY_G2_TEST_CATEGORY_COUNT, 40)

    def test_original_twenty_mandatory_categories_are_all_preserved(self) -> None:
        expected_original = (
            "01_ACCEPTED_G1_CHAIN_BINDINGS",
            "02_TARGET_ALLOWLIST",
            "03_CONTROL_DENYLIST",
            "04_RUN_ORDINAL_ALLOWLIST",
            "05_STATIC_SCHEMA_MODE_ZERO_CALL",
            "06_MISSING_G4_AUTHORIZATION_ZERO_CALL_FAIL",
            "07_MISSING_EXTERNAL_BINDING_ZERO_CALL_FAIL",
            "08_REQUIRED_OBSERVATION_GROUPS_AND_FIELDS",
            "09_SEMANTIC_PROVENANCE_SEPARATION",
            "10_SENT_EVIDENCE_TEXT_HASH_CONTRACT",
            "11_OBSERVATION_SEMANTIC_DIGEST_CANONICALIZATION",
            "12_PROVENANCE_DIGEST_INVARIANCE",
            "13_CANONICAL_ADAPTER_PRESERVES_SEMANTIC_ARGUMENTS",
            "14_RAW_FINAL_ANSWER_DISTINCT",
            "15_VERIFIER_EVALUATOR_CAPTURE_WITHOUT_REINTERPRETATION",
            "16_OBSERVER_SELF_WRITE_FREE",
            "17_NO_PRODUCT_GOLDEN_EVALUATOR_VERIFIER_DB_MUTATION_PATH",
            "18_STDOUT_ONLY_OUTPUT_CONTRACT",
            "19_NO_CLASSIFIER_READINESS_IMPLEMENTATION",
            "20_UNRESOLVED_G4_SIDE_EFFECT_POLICY_ZERO_CALL_FAIL",
        )
        self.assertEqual(
            MANDATORY_G2_TEST_CATEGORIES[:20], expected_original
        )
        self.assertIn("21_G2_EQ1_CANONICAL_EVALUATOR_NONSTREAMING_BRANCH",
                      MANDATORY_G2_TEST_CATEGORIES)
        self.assertIn("26_G2_EQ1_ZERO_REAL_CALL",
                      MANDATORY_G2_TEST_CATEGORIES)
        self.assertIn("27_G2_EQ2_CANONICAL_MEASUREMENT_TIMER_BOUNDARY",
                      MANDATORY_G2_TEST_CATEGORIES)
        self.assertIn("29_G2_EQ2_CANONICAL_PIPELINE_GENERATION_BINDING",
                      MANDATORY_G2_TEST_CATEGORIES)

    def test_missing_mandatory_categories_is_empty(self) -> None:
        self.assertEqual(missing_mandatory_g2_test_categories(), [])
        self.assertEqual(
            set(CATEGORY_TEST_METHODS), set(MANDATORY_G2_TEST_CATEGORIES)
        )

    def test_every_category_has_a_mechanical_test_method(self) -> None:
        defined = set(_module_test_method_names())
        uncovered: list[str] = []
        for category, methods in CATEGORY_TEST_METHODS.items():
            if not methods or not any(method in defined for method in methods):
                uncovered.append(category)
        self.assertEqual(uncovered, [])

    def test_every_declared_category_method_exists(self) -> None:
        defined = set(_module_test_method_names())
        missing: list[str] = []
        for methods in CATEGORY_TEST_METHODS.values():
            for method in methods:
                if method not in defined:
                    missing.append(method)
        self.assertEqual(missing, [])

    def test_total_and_unique_test_method_counts_are_equal(self) -> None:
        names = _module_test_method_names()
        self.assertEqual(len(names), len(set(names)))

    def test_no_real_call_boundary_was_triggered_by_this_module(self) -> None:
        self.assertEqual(_REAL_CALL_ATTEMPTS, [])


if __name__ == "__main__":
    unittest.main()
