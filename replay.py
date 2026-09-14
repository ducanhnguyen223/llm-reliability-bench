"""Replay fact changes against four cache strategies."""

import argparse
import json
from pathlib import Path


def run_strategy(scenarios, strategy, threshold=0.9, ttl_seconds=300):
    counts = {
        "requests": 0,
        "hits": 0,
        "true_hits": 0,
        "false_reuse": 0,
        "upstream_calls": 0,
        "reusable_cases": 0,
        "unnecessary_invalidations": 0,
        "stale_cases": 0,
        "stale_detected": 0,
    }
    decisions = []
    for scenario in scenarios:
        cache = {}
        for event in scenario["events"]:
            counts["requests"] += 1
            gold_candidate = cache.get(event.get("candidate_id"))
            if gold_candidate:
                counts["reusable_cases" if gold_candidate["answer"] == event["answer"] else "stale_cases"] += 1
            candidate = None
            if strategy == "exact":
                candidate = next((item for item in cache.values() if item["query"] == event["query"]), None)
            elif strategy in {"semantic_ttl", "evidence_gate"} and event.get("candidate_id"):
                item = cache.get(event["candidate_id"])
                fresh = item and event["at_seconds"] - item["at_seconds"] <= ttl_seconds
                similar = event.get("candidate_similarity", 0) >= threshold
                dependencies_match = item and item["dependencies"] == event["dependencies"]
                if fresh and similar and (strategy != "evidence_gate" or dependencies_match):
                    candidate = item

            if candidate:
                correct = candidate["answer"] == event["answer"]
                counts["hits"] += 1
                counts["true_hits" if correct else "false_reuse"] += 1
                decision = "reuse" if correct else "false_reuse"
            else:
                counts["upstream_calls"] += 1
                cache[event["id"]] = event
                decision = "upstream"
                if gold_candidate:
                    counts["unnecessary_invalidations" if gold_candidate["answer"] == event["answer"] else "stale_detected"] += 1
            decisions.append({"scenario": scenario["id"], "event": event["id"], "decision": decision})
    counts["true_hit_rate"] = counts["true_hits"] / counts["reusable_cases"] if counts["reusable_cases"] else 0
    counts["false_reuse_rate"] = counts["false_reuse"] / counts["stale_cases"] if counts["stale_cases"] else 0
    counts["stale_detection_rate"] = counts["stale_detected"] / counts["stale_cases"] if counts["stale_cases"] else 0
    return {"strategy": strategy, "counts": counts, "decisions": decisions}


def run_replay(fixture):
    return {
        "dataset": fixture["dataset"],
        "threshold": fixture["semantic_threshold"],
        "ttl_seconds": fixture["ttl_seconds"],
        "latency_ms": None,
        "token_usage": None,
        "cost": None,
        "measurement_note": "Deterministic replay measures safety and upstream-call counts; no model is called, so latency, tokens and cost are not fabricated.",
        "results": [
            run_strategy(fixture["scenarios"], strategy, fixture["semantic_threshold"], fixture["ttl_seconds"])
            for strategy in ("no_cache", "exact", "semantic_ttl", "evidence_gate")
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=Path("fixtures/case_replay.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/case_replay.json"))
    args = parser.parse_args()
    report = run_replay(json.loads(args.fixture.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
