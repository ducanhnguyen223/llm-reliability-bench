import json
import unittest
from pathlib import Path

from benchmark import REQUIRED_CATEGORIES, evaluate, validate_contrast_set
from replay import run_replay


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

    def test_vietnamese_contrast_set_is_complete_and_split_safe(self):
        dataset = json.loads(Path("fixtures/vietnamese_business_contrasts.json").read_text())
        summary = validate_contrast_set(dataset)
        self.assertEqual(summary, {"cases": 24, "families": 8, "categories": len(REQUIRED_CATEGORIES)})

    def test_evidence_gate_reuses_only_unchanged_dependencies(self):
        fixture = json.loads(Path("fixtures/case_replay.json").read_text())
        results = {item["strategy"]: item["counts"] for item in run_replay(fixture)["results"]}
        self.assertGreater(results["semantic_ttl"]["false_reuse"], 0)
        self.assertEqual(results["evidence_gate"]["false_reuse"], 0)
        self.assertGreater(results["evidence_gate"]["true_hits"], 0)
        self.assertEqual(results["no_cache"]["upstream_calls"], results["no_cache"]["requests"])


if __name__ == "__main__":
    unittest.main()
