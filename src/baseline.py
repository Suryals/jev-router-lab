"""Baseline LLM router: same 310 alerts, same three decisions, via a local
LLM (LM Studio, OpenAI-compatible API) instead of Jev.

Usage:  uv run python -m src.baseline

Writes results/baseline_<timestamp>.jsonl with the same record shape as the
shadow runner (gold travels along), plus latency and token usage, and prints
accuracy at the end so runs are self-scoring.
"""

import json
import time
from pathlib import Path

import httpx

from src.triage import CATEGORIES, PRIORITIES

LMSTUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL = "qwen/qwen3.8-27b"

ROOT = Path(__file__).resolve().parent.parent
ALERTS = ROOT / "data" / "alerts.jsonl"
RESULTS_DIR = ROOT / "results"

SYSTEM_PROMPT = f"""You are an L1 triage router for a big-data platform ops team.
Given one alert, decide three things and reply with ONLY a JSON object, no other text:

{{"category": "<one of: {", ".join(CATEGORIES)}>", "priority": "<one of: {", ".join(PRIORITIES)}>", "page_human": <true|false>}}

Definitions:
- category: {"; ".join(f"{k} = {v}" for k, v in CATEGORIES.items())}
- priority: {"; ".join(f"{k} = {v}" for k, v in PRIORITIES.items())}
- page_human: should this page an on-call human right now, vs automation or a ticket.
/no_think"""


def route_one(client: httpx.Client, alert: str) -> tuple[dict | None, dict]:
    """Returns (parsed answer or None, metadata with latency/tokens/raw)."""
    started = time.perf_counter()
    resp = client.post(
        LMSTUDIO_URL,
        json={
            "model": MODEL,
            "temperature": 0,
            # LM Studio only accepts json_schema / text for response_format
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "triage",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "enum": list(CATEGORIES)},
                            "priority": {"type": "string", "enum": list(PRIORITIES)},
                            "page_human": {"type": "boolean"},
                        },
                        "required": ["category", "priority", "page_human"],
                        "additionalProperties": False,
                    },
                },
            },
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": alert},
            ],
        },
        timeout=120.0,
    )
    resp.raise_for_status()
    body = resp.json()
    meta = {
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        "usage": body.get("usage", {}),
    }
    msg = body["choices"][0]["message"]
    # LM Studio + Qwen3 thinking mode: structured output can land in
    # reasoning_content with an empty content field
    raw = msg["content"] or msg.get("reasoning_content", "")
    try:
        parsed = json.loads(raw)
        assert parsed.get("category") in CATEGORIES
        assert parsed.get("priority") in PRIORITIES
        assert isinstance(parsed.get("page_human"), bool)
        return parsed, meta
    except (json.JSONDecodeError, AssertionError):
        meta["raw"] = raw  # keep the malformed output for the error analysis
        return None, meta


def run() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"baseline_{time.strftime('%Y%m%d_%H%M%S')}.jsonl"
    hits = {"category": 0, "priority": 0, "page_human": 0}
    n = malformed = 0
    latencies: list[float] = []

    with httpx.Client() as client, ALERTS.open() as f, out_path.open("w") as out:
        for line in f:
            case = json.loads(line)
            answer, meta = route_one(client, case["alert"])
            n += 1
            latencies.append(meta["latency_ms"])
            if answer is None:
                malformed += 1
            else:
                for k in hits:
                    if answer[k] == case["gold"][k]:
                        hits[k] += 1
            out.write(json.dumps({
                "id": case["id"], "alert": case["alert"], "gold": case["gold"],
                "model": MODEL, "answer": answer, **meta,
            }) + "\n")
            if n % 25 == 0:
                print(f"{n} done, last {meta['latency_ms']:.0f}ms")

    latencies.sort()
    print(f"\nn={n}  malformed={malformed}")
    for k, v in hits.items():
        print(f"  {k:<12} accuracy {v / n:.0%}")
    print(f"  latency p50 {latencies[n // 2]:.0f}ms  max {latencies[-1]:.0f}ms")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    run()
