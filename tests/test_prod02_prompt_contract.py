"""Current prompt numbering and its exact link to the controlled intervention."""

import json
from pathlib import Path
import re
from types import SimpleNamespace
import unittest

from core.engine_v2 import build_messages
from scripts.diagnose_prod02_generation_content import arm_messages

ROOT = Path(__file__).resolve().parents[1]


class TestProd02PromptContract(unittest.TestCase):
    def test_live_prompt_equals_effective_frozen_b_intervention(self):
        saved = json.loads((ROOT / "eval/v4_ws13_g4_observations_20261015.json").read_text(encoding="utf-8"))
        observation = saved["observations"][0]["OBSERVATION"]
        original = observation["generation_input"]["application_level_model_visible_context"]
        headers = re.findall(r"^\[材料(\d+)｜([^\n]*)\]$", original[-1]["content"], re.MULTILINE)
        evidence = observation["retrieval"]["sent_evidence_records"]
        self.assertEqual([int(number) for number, _ in headers], list(range(1, 6)))
        # WS13 stores the complete material block, including its old header.
        # The live builder receives the body and reconstructs the current header.
        contexts = [SimpleNamespace(text=record["sent_evidence_text"].split("\n", 1)[1], location=location,
                                    id=record["sent_context_id"])
                    for record, (_, location) in zip(evidence, headers, strict=True)]
        messages, sent = build_messages(saved["canonical_query"], contexts, "qa")
        self.assertEqual(messages, arm_messages(original, "B"))
        self.assertEqual([chunk.id for chunk in sent], observation["generation_input"]["sent_context_ids"])
        self.assertTrue(all(left is right for left, right in zip(contexts, sent, strict=True)))

    def test_chunk_order_controls_numbers_even_with_repeated_document_titles(self):
        contexts = [SimpleNamespace(text="第一块有实质正文。", location="同一本教材 · PDF 第7页"),
                    SimpleNamespace(text="第二块有不同正文。", location="同一本教材 · PDF 第8页")]
        messages, sent = build_messages("请比较两处内容。", contexts, "qa")
        prompt = messages[-1]["content"]
        self.assertIn("[1] 同一本教材 · PDF 第7页\n第一块有实质正文。", prompt)
        self.assertIn("[2] 同一本教材 · PDF 第8页\n第二块有不同正文。", prompt)
        self.assertEqual(sent, contexts)
        self.assertNotIn("[材料", prompt)
        self.assertIn("例如[1]", messages[0]["content"])

    def test_no_case_facts_are_injected_and_unsupported_policy_remains(self):
        messages, _ = build_messages("未被材料覆盖的问题？", [SimpleNamespace(text="OFDMA材料。", location="材料位置")], "qa")
        self.assertNotIn("GMSK", json.dumps(messages, ensure_ascii=False))
        self.assertIn("不能确定就明确说材料不足", messages[0]["content"])
        self.assertNotIn("无论问题是否已包含", messages[0]["content"])


if __name__ == "__main__":
    unittest.main()
