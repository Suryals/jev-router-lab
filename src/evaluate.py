"""Score a shadow run against gold labels.

Usage:  uv run python -m src.evaluate results/shadow_<timestamp>.jsonl

Scaffolding computes plain accuracy per decision. The two functions that
make this an eval worth publishing — calibration() and the escalation
policy in src/policy.py — are the hand-written spine. See their TODOs.
"""

import json
import sys
from pathlib import Path


def load(path: str) -> list[dict]:
    return [json.loads(line) for line in Path(path).open()]


def accuracy(records: list[dict]) -> dict[str, float]:
    """Fraction of alerts where Jev's top answer matches gold, per decision."""
    hits = {"category": 0, "priority": 0, "page_human": 0}
    for r in records:
        a = r["jev"]["answers"]
        if a["category"]["choice"] == r["gold"]["category"]:
            hits["category"] += 1
        if a["priority"]["choice"] == r["gold"]["priority"]:
            hits["priority"] += 1
        if (a["page_human"]["noul"] >= 0.5) == r["gold"]["page_human"]:
            hits["page_human"] += 1
    return {k: v / len(records) for k, v in hits.items()}


def calibration(records: list[dict]) -> dict:
    """SPINE — hand-write this (Chief).

    The question: when Jev says confidence 0.9, is it right ~90% of the time?

    Plan:
      1. Collect (confidence, was_correct) pairs for the `category` decision.
      2. Bucket them (e.g. 0.5-0.7, 0.7-0.9, 0.9-1.0).
      3. Per bucket: mean confidence vs actual hit rate. A calibrated model
         has these nearly equal; the gap is the calibration error.
      4. Return {bucket: {"mean_conf": ..., "hit_rate": ..., "n": ...}}.

    Watch out: with only 10 alerts the buckets will be thin — expand
    data/alerts.jsonl toward 20-30 per your shadow-mode methodology first.
    """
    raise NotImplementedError("calibration() is Chief's to write")


if __name__ == "__main__":
    records = load(sys.argv[1])
    print(f"n={len(records)}")
    for decision, acc in accuracy(records).items():
        print(f"  {decision:<12} accuracy {acc:.0%}")
    latencies = sorted(r["jev"]["latency_ms"] for r in records)
    print(f"  latency p50 {latencies[len(latencies) // 2]:.0f}ms  max {latencies[-1]:.0f}ms")
    tokens = sum(r["jev"]["usage"]["input_tokens"] for r in records)
    print(f"  input tokens {tokens}  (~${tokens * 0.042 / 1_000_000:.6f})")
