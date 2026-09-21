"""Frontier-LLM baseline: same 310 alerts, same three decisions, via
Claude Sonnet 5 with structured outputs.

Usage:  uv run python -m src.baseline_sonnet
Needs ANTHROPIC_API_KEY in the repo .env (or the environment).

Writes results/sonnet_<timestamp>.jsonl in the same record shape as the
other runners, self-scores at the end, and reports the measured dollar
cost from token usage.
"""

import json
import time
from enum import Enum
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel

from src.triage import CATEGORIES, PRIORITIES

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MODEL = "claude-sonnet-5"
PRICE_IN, PRICE_OUT = 2.00, 10.00  # $/MTok

ROOT = Path(__file__).resolve().parent.parent
ALERTS = ROOT / "data" / "alerts.jsonl"
RESULTS_DIR = ROOT / "results"

Category = Enum("Category", {k: k for k in CATEGORIES})
Priority = Enum("Priority", {k: k for k in PRIORITIES})


class Triage(BaseModel):
    category: Category
    priority: Priority
    page_human: bool


SYSTEM_PROMPT = f"""You are an L1 triage router for a big-data platform ops team.
Given one alert, decide its category, priority, and whether to page a human.

Definitions:
- category: {"; ".join(f"{k} = {v}" for k, v in CATEGORIES.items())}
- priority: {"; ".join(f"{k} = {v}" for k, v in PRIORITIES.items())}
- page_human: should this page an on-call human right now, vs automation or a ticket."""


def run() -> None:
    client = anthropic.Anthropic()
    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"sonnet_{time.strftime('%Y%m%d_%H%M%S')}.jsonl"
    hits = {"category": 0, "priority": 0, "page_human": 0}
    n = 0
    tokens_in = tokens_out = 0
    latencies: list[float] = []

    with ALERTS.open() as f, out_path.open("w") as out:
        for line in f:
            case = json.loads(line)
            started = time.perf_counter()
            response = client.messages.parse(
                model=MODEL,
                max_tokens=2000,
                output_config={"effort": "low"},
                system=[{"type": "text", "text": SYSTEM_PROMPT,
                         "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": case["alert"]}],
                output_format=Triage,
            )
            latency_ms = round((time.perf_counter() - started) * 1000, 1)
            t = response.parsed_output
            answer = {"category": t.category.value, "priority": t.priority.value,
                      "page_human": t.page_human}
            n += 1
            latencies.append(latency_ms)
            tokens_in += response.usage.input_tokens + (response.usage.cache_read_input_tokens or 0)
            tokens_out += response.usage.output_tokens
            for k in hits:
                if answer[k] == case["gold"][k]:
                    hits[k] += 1
            out.write(json.dumps({
                "id": case["id"], "alert": case["alert"], "gold": case["gold"],
                "model": MODEL, "answer": answer, "latency_ms": latency_ms,
                "usage": response.usage.to_dict(),
            }) + "\n")
            if n % 25 == 0:
                print(f"{n} done, last {latency_ms:.0f}ms")

    latencies.sort()
    # cache reads bill at ~0.1x; this treats them as full price, so cost shown
    # is an upper bound
    cost = tokens_in * PRICE_IN / 1e6 + tokens_out * PRICE_OUT / 1e6
    print(f"\nn={n}")
    for k, v in hits.items():
        print(f"  {k:<12} accuracy {v / n:.0%}")
    print(f"  latency p50 {latencies[n // 2]:.0f}ms  max {latencies[-1]:.0f}ms")
    print(f"  tokens in {tokens_in} out {tokens_out}  cost <= ${cost:.4f}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    run()
