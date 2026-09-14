"""Recompute a semantic-cache safety decision from frozen measurements."""

import argparse
import hashlib
import json
import math
from pathlib import Path


def select_threshold(rows):
    development = [r for r in rows if r["split"] == "development" and r["scope_match"]]
    candidates = sorted({r["similarity"] for r in development} | {1.000001})
    safe = []
    for threshold in candidates:
        false_hits = sum(not r["same_answer"] and r["similarity"] >= threshold for r in development)
        true_hits = sum(r["same_answer"] and r["similarity"] >= threshold for r in development)
        if false_hits == 0:
            safe.append((true_hits, -threshold, threshold))
    return max(safe)[2]


def split_metrics(rows, split, threshold):
    selected = [r for r in rows if r["split"] == split]
    positives = sum(r["same_answer"] and r["scope_match"] for r in selected)
    negatives = sum(not r["same_answer"] and r["scope_match"] for r in selected)
    true_hits = sum(r["same_answer"] and r["scope_match"] and r["similarity"] >= threshold for r in selected)
    false_hits = sum(not r["same_answer"] and r["scope_match"] and r["similarity"] >= threshold for r in selected)
    return {
        "pairs": len(selected),
        "scope_blocked": sum(not r["scope_match"] for r in selected),
        "true_hits": true_hits,
        "false_hits": false_hits,
        "true_hit_rate": true_hits / positives if positives else 0,
        "false_hit_rate": false_hits / negatives if negatives else 0,
    }


def evaluate(fixture):
    rows = fixture["rows"]
    ids = [r["id"] for r in rows]
    if not rows or len(ids) != len(set(ids)):
        raise ValueError("rows must be non-empty and have unique ids")
    for row in rows:
        if row["split"] not in {"development", "holdout"}:
            raise ValueError(f"invalid split for {row['id']}")
        if not math.isfinite(row["similarity"]) or not -1 <= row["similarity"] <= 1:
            raise ValueError(f"invalid similarity for {row['id']}")

    threshold = select_threshold(rows)
    metrics = {split: split_metrics(rows, split, threshold) for split in ("development", "holdout")}
    acceptance = fixture["acceptance"]
    recommend = (
        metrics["holdout"]["false_hits"] <= acceptance["max_holdout_false_hits"]
        and metrics["holdout"]["true_hit_rate"] >= acceptance["min_holdout_true_hit_rate"]
    )
    return {
        "kind": "semantic-cache safety benchmark",
        "dataset": fixture["dataset"],
        "measurement_source": fixture["measurement_source"],
        "threshold_selected_on": "development",
        "threshold": threshold,
        "acceptance": acceptance,
        "metrics": metrics,
        "recommend_enable": recommend,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=Path("fixtures/frozen_measurements.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/baseline.json"))
    args = parser.parse_args()
    raw = args.fixture.read_bytes()
    report = evaluate(json.loads(raw))
    report["fixture_sha256"] = hashlib.sha256(raw).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
