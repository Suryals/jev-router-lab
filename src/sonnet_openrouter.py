"""Frontier-LLM baseline via OpenRouter: Claude Sonnet 5, same 310 alerts,
same three decisions, JSON-schema structured output.

Usage:  uv run python -m src.sonnet_openrouter
Needs OPENROUTER_API_KEY in the repo .env.

Writes results/sonnet_<timestamp>.jsonl, self-scores, and reports exact cost
(OpenRouter returns per-request cost when usage accounting is requested).
"""

import json
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

from src.triage import CATEGORIES, PRIORITIES

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-sonnet-5"
ALERTS = ROOT / "data" / "alerts.jsonl"
RESULTS_DIR = ROOT / "results"

SYSTEM_PROMPT = f"""You are an L1 triage router for a big-data platform ops team.
Given one alert, decide its category, priority, and whether to page a human.

Definitions:
- category: {"; ".join(f"{k} = {v}" for k, v in CATEGORIES.items())}
- priority: {"; ".join(f"{k} = {v}" for k, v in PRIORITIES.items())}
- page_human: should this page an on-call human right now, vs automation or a ticket."""

SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": list(CATEGORIES)},
        "priority": {"type": "string", "enum": list(PRIORITIES)},
        "page_human": {"type": "boolean"},
    },
    "required": ["category", "priority", "page_human"],
    "additionalProperties": False,
}


def route_one(client: httpx.Client, alert: str) -> tuple[dict | None, dict]:
    started = time.perf_counter()
    for attempt in range(4):
        try:
            resp = _post(client, alert)
            break
        except (httpx.TransportError, httpx.HTTPStatusError) as e:
            if isinstance(e, httpx.HTTPStatusError) and e.response.status_code < 500:
                raise
            if attempt == 3:
                raise
            time.sleep(2**attempt)
    body = resp.json()
    meta = {
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        "usage": body.get("usage", {}),
    }
    raw = body["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(raw)
        assert parsed.get("category") in CATEGORIES
        assert parsed.get("priority") in PRIORITIES
        assert isinstance(parsed.get("page_human"), bool)
        return parsed, meta
    except (json.JSONDecodeError, AssertionError):
        meta["raw"] = raw
        return None, meta


def _post(client: httpx.Client, alert: str) -> httpx.Response:
    resp = client.post(URL, json={
        "model": MODEL,
        "temperature": 0,
        "max_tokens": 2000,
        "usage": {"include": True},
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "triage", "strict": True, "schema": SCHEMA}},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": alert},
        ],
    }, timeout=120.0)
    resp.raise_for_status()
    return resp


def run(resume_path: str | None = None) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    done_ids: set[str] = set()
    if resume_path:
        out_path = Path(resume_path)
        done_ids = {json.loads(l)["id"] for l in out_path.open() if l.strip()}
        print(f"resuming, {len(done_ids)} already done")
    else:
        out_path = RESULTS_DIR / f"sonnet_{time.strftime('%Y%m%d_%H%M%S')}.jsonl"
    hits = {"category": 0, "priority": 0, "page_human": 0}
    n = malformed = 0
    cost = 0.0
    latencies: list[float] = []
    headers = {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"}

    with httpx.Client(headers=headers) as client, ALERTS.open() as f, out_path.open("a") as out:
        for line in f:
            case = json.loads(line)
            if case["id"] in done_ids:
                continue
            answer, meta = route_one(client, case["alert"])
            n += 1
            latencies.append(meta["latency_ms"])
            cost += meta["usage"].get("cost", 0.0)
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
                print(f"{n} done, last {meta['latency_ms']:.0f}ms, cost so far ${cost:.4f}")

    latencies.sort()
    print(f"\nn={n}  malformed={malformed}")
    for k, v in hits.items():
        print(f"  {k:<12} accuracy {v / n:.0%}")
    print(f"  latency p50 {latencies[n // 2]:.0f}ms  max {latencies[-1]:.0f}ms")
    print(f"  cost ${cost:.4f}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    import sys

    run(sys.argv[1] if len(sys.argv) > 1 else None)
