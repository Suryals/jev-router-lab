"""Shadow-mode runner: answer every alert with Jev, log everything.

Usage:  uv run python -m src.shadow [--baseline]

Reads data/alerts.jsonl, calls Jev with the shared triage questions, and
appends one JSON line per alert to results/shadow_<timestamp>.jsonl with
the raw answers, probabilities, latency, and token usage. The gold labels
travel along in each record so evaluate.py needs no joins.

The baseline router (your current LLM-based routing) is a pluggable
function — wire it to LM Studio / LangChain later and pass --baseline
to record its answers side by side.
"""

import argparse
import json
import time
from pathlib import Path

from src.jev_client import ask
from src.triage import triage_questions

ROOT = Path(__file__).resolve().parent.parent
ALERTS = ROOT / "data" / "alerts.jsonl"
RESULTS_DIR = ROOT / "results"


def baseline_router(alert: str) -> dict | None:
    """Your existing router (e.g. local Qwen via LM Studio, or Opus).

    Return {"category": ..., "priority": ..., "page_human": bool} or None
    if no baseline is wired up yet.
    """
    return None


def run(with_baseline: bool) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"shadow_{time.strftime('%Y%m%d_%H%M%S')}.jsonl"
    questions = triage_questions()

    with ALERTS.open() as f, out_path.open("w") as out:
        for line in f:
            case = json.loads(line)
            jev = ask({"alert": case["alert"]}, questions)
            record = {
                "id": case["id"],
                "alert": case["alert"],
                "gold": case["gold"],
                "jev": {
                    "model": jev["model"],
                    "answers": jev["answers"],
                    "latency_ms": jev["latency_ms"],
                    "usage": jev["usage"],
                },
                "baseline": baseline_router(case["alert"]) if with_baseline else None,
            }
            out.write(json.dumps(record) + "\n")
            cat = jev["answers"]["category"]
            print(
                f"{case['id']}  {cat['choice']:<13} conf={cat['confidence']:.2f}  "
                f"page={jev['answers']['page_human']['noul']:.2f}  "
                f"{jev['latency_ms']:.0f}ms"
            )

    print(f"\nwrote {out_path}")
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", action="store_true")
    run(parser.parse_args().baseline)
