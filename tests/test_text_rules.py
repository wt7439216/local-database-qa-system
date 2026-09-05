import unittest

from core.text_rules import is_book_overview_query, is_book_toc_query, normalize_query, route_by_rules


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

    def test_natural_book_level_phrasing_is_normalized(self):
        self.assertEqual(normalize_query("介绍一下这本教材。"), "介绍本书")
        self.assertTrue(is_book_overview_query("这本书主要讲了什么？"))
        self.assertTrue(is_book_overview_query("介绍下这本书"))
        self.assertTrue(is_book_toc_query("这本书有哪些章节？"))
        self.assertTrue(is_book_toc_query("本书一共几章？"))
        self.assertEqual(route_by_rules("这本书有哪些章节？"), "toc")

    def test_specific_question_uses_retrieval(self):
        self.assertEqual(route_by_rules("为什么存在多径衰落"), "retrieval")
        self.assertEqual(route_by_rules("介绍扩频技术"), "retrieval")


if __name__ == "__main__":
    unittest.main()
