import unittest

from src.scoring.compute_score import calcular_score, validate_scoring


class ScoringValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.top50 = calcular_score()

    def test_calcular_score_returns_expected_portfolio_shape(self):
        self.assertEqual(len(self.top50), 50)
        self.assertEqual(int((self.top50["tier"] == "A").sum()), 15)
        self.assertEqual(int((self.top50["tier"] == "B").sum()), 35)
        self.assertFalse(self.top50["brand_id"].duplicated().any())

    def test_tier_b_has_scores_and_sorted_ranks(self):
        tier_b = self.top50[self.top50["tier"].eq("B")]
        self.assertFalse(tier_b["final_score"].isna().any())
        self.assertEqual(tier_b["rank"].tolist(), list(range(16, 51)))
        self.assertGreaterEqual(float(tier_b["final_score"].max()), float(tier_b["final_score"].min()))

    def test_validate_scoring_all_pass(self):
        results = validate_scoring()
        failed = [result for result in results if not result.passed]
        self.assertEqual(failed, [])
        self.assertGreaterEqual(len(results), 8)


if __name__ == "__main__":
    unittest.main()
