import unittest

from core.text_rules import route_by_rules


class RouteByRulesTests(unittest.TestCase):
    def test_hybrid_route_has_priority_over_summary_keywords(self):
        cases = [
            "结合全书说明模型细节",
            "整体来看有哪些技术细节",
        ]

        for query in cases:
            with self.subTest(query=query):
                self.assertEqual(route_by_rules(query), "hybrid")

    def test_summary_route_remains_available(self):
        self.assertEqual(route_by_rules("本书主要讲什么"), "summary")

    def test_specific_question_uses_retrieval(self):
        self.assertEqual(route_by_rules("为什么存在多径衰落"), "retrieval")


if __name__ == "__main__":
    unittest.main()
