"""Guard the diagnostic budget and single-variable prompt transformations."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import diagnose_prod02_generation_content as probe


class TestFrozenPromptProbe(unittest.TestCase):
    def setUp(self):
        self.question = "GSM 使用 GMSK 调制，请指出出处。"
        self.messages = [{"role": "system", "content": "只使用材料；引用写为[1]。"},
                         {"role": "user", "content": "任务要求：直接回答。\n\n" + "\n\n".join(
                             f"[材料{i}｜位置{i}]\n材料正文{i} GMSK" for i in range(1, 6)
                         ) + "\n\n问题：" + self.question}]

    def test_fixed_twelve_call_order_and_exact_target_repeats(self):
        runs = probe.build_runs(self.messages, self.question)
        self.assertEqual([(r["arm"], r["case_kind"]) for r in runs],
                         [(a, k) for a in "ABC" for k in ("target", "positive", "negative")]
                         + [(a, "target") for a in "ABC"])
        self.assertEqual([r["ordinal"] for r in runs], list(range(1, 13)))
        for left, right in ((0, 9), (3, 10), (6, 11)):
            self.assertEqual(runs[left]["messages"], runs[right]["messages"])
            self.assertEqual(runs[left]["messages_sha256"], runs[right]["messages_sha256"])

    def test_a_is_exact_and_never_mutates_input(self):
        before = deepcopy(self.messages)
        self.assertEqual(probe.arm_messages(self.messages, "A"), before)
        probe.build_runs(self.messages, self.question)
        self.assertEqual(self.messages, before)

    def test_b_only_replaces_five_headers(self):
        changed = probe.arm_messages(self.messages, "B")
        self.assertEqual(changed[0], self.messages[0])
        for i in range(1, 6):
            self.assertIn(f"[{i}] 位置{i}\n材料正文{i} GMSK", changed[-1]["content"])
        restored = changed[-1]["content"]
        for i in range(1, 6):
            restored = restored.replace(f"[{i}] 位置{i}\n", f"[材料{i}｜位置{i}]\n")
        self.assertEqual(restored, self.messages[-1]["content"])

    def test_c_adds_generic_rule_without_case_terms_or_context_change(self):
        changed = probe.arm_messages(self.messages, "C")
        self.assertEqual(changed[-1], self.messages[-1])
        self.assertEqual(changed[0]["content"], self.messages[0]["content"] + probe.CONTENT_RULE)
        self.assertNotIn("GSM", probe.CONTENT_RULE)
        self.assertNotIn("GMSK", probe.CONTENT_RULE)

    def test_missing_headers_or_mismatched_query_fail_closed(self):
        with self.assertRaises(ValueError):
            probe.arm_messages([{"role": "user", "content": "plain text"}], "B")
        with self.assertRaises(ValueError):
            probe.build_runs(self.messages, "another query")

    def test_transport_retains_all_decoded_metadata_and_uses_canonical_chat(self):
        expected = {"model": "qwen2.5:7b", "messages": self.messages, "stream": False,
                    "keep_alive": "10m", "options": probe.OPTIONS}
        response = {"model": "qwen2.5:7b", "done": True, "done_reason": "stop", "eval_count": 9,
                    "message": {"role": "assistant", "content": "  GSM 使用 GMSK。[1]  "},
                    "additional_nested_metadata": {"preserved": [1, 2, 3]}}
        client = probe.CapturingClient(expected)
        with patch.object(probe.OllamaClient, "_request", return_value=response) as transport:
            self.assertEqual(client.chat(self.messages, model="qwen2.5:7b"), "GSM 使用 GMSK。[1]")
        transport.assert_called_once()
        self.assertEqual(client.capture["response"], response)
        self.assertIsNot(client.capture["response"], response)
        self.assertEqual(client.call_count, 1)
        with self.assertRaises(RuntimeError):
            client.chat(self.messages, model="qwen2.5:7b")

    def test_consumed_budget_cannot_be_reexecuted(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            plan = {"generation_budget": 12, "runs": [{} for _ in range(12)]}
            plan["semantic_digest"] = probe.digest(plan)
            probe.save(output / "frozen-plan.json", plan)
            probe.save(output / "execution-binding.json", {
                "frozen_plan_raw_sha256": probe.sha((output / "frozen-plan.json").read_bytes())})
            (output / "attempts.jsonl").write_text(json.dumps({"ordinal": 1}) + "\n", encoding="utf-8")
            with patch.object(probe.OllamaClient, "_request") as transport:
                with self.assertRaisesRegex(RuntimeError, "already started"):
                    probe.execute(output / "frozen-plan.json")
            transport.assert_not_called()

    def test_label_only_is_separate_from_numeric_citation_validity(self):
        old = probe.heuristic_checks("[材料1]", "target")
        self.assertTrue(old["label_only"])
        self.assertFalse(old["required_terms_present"]["GMSK"])
        proper = probe.heuristic_checks("GSM 使用 GMSK。[1]", "target")
        self.assertFalse(proper["label_only"])
        self.assertTrue(proper["required_terms_present"]["GMSK"])
        self.assertEqual(proper["numeric_citation_ids"], [1])


if __name__ == "__main__":
    unittest.main()
