import unittest

from benchmark import evaluate


class BenchmarkTest(unittest.TestCase):
    def test_unsafe_negation_disables_cache(self):
        fixture = {
            "dataset": "test",
            "measurement_source": {},
            "acceptance": {"max_holdout_false_hits": 0, "min_holdout_true_hit_rate": 0.8},
            "rows": [
                {"id": "D1", "split": "development", "same_answer": True, "scope_match": True, "similarity": 0.80},
                {"id": "D2", "split": "development", "same_answer": False, "scope_match": True, "similarity": 0.90},
                {"id": "H1", "split": "holdout", "same_answer": True, "scope_match": True, "similarity": 0.82},
                {"id": "H2", "split": "holdout", "same_answer": False, "scope_match": False, "similarity": 1.0},
            ],
        }
        report = evaluate(fixture)
        self.assertEqual(report["threshold"], 1.000001)
        self.assertEqual(report["metrics"]["holdout"]["scope_blocked"], 1)
        self.assertFalse(report["recommend_enable"])


if __name__ == "__main__":
    unittest.main()
