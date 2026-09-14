# LLM Reliability Bench

A small, reproducible check for a dangerous cache assumption: similar prompts do not necessarily deserve the same answer.

The frozen baseline contains paraphrases, answer-changing negations and requests that look identical but belong to different authorization or evidence scopes. A threshold is selected on the development split only, then checked against a holdout split.

`fixtures/vietnamese_business_contrasts.json` adds 24 fact-grounded Vietnamese business cases covering diacritics, negation, short queries, near-identical IDs, numbers and units, permissions, effective dates and source revisions. Scenario families never cross the development/holdout boundary.

## Baseline result

With `multilingual-e5-small`, several answer-changing pairs scored above valid paraphrases. The only zero-false-hit threshold reused no answers, so semantic caching stays disabled.

## Run

```bash
python3 -m unittest discover -s tests -q
python3 benchmark.py
python3 replay.py
```

The default run uses frozen similarity measurements, so it needs no API key, model download or third-party package.

The replay compares no cache, exact matching, semantic similarity with a TTL, and a dependency-aware EvidenceGate. Changes to source revision, record state, actor role, prompt/model version or policy validity must force a fresh answer even when the query is identical.
