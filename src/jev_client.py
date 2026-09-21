"""Thin HTTP client for TypeSafe Jev (System One API).

Deliberately raw httpx instead of langchain-typesafe (0.0.1a3 alpha) so the
request/response shapes stay visible and stable while the SDK churns.

API notes (verified 2026-09-21 against jev-1.13.0):
  - POST https://api.typesafe.ai/v1/systemone, Bearer auth
  - `choice` questions take a `criteria` dict (NOT `options`)
  - response: {"model", "answers": {qid: {...}}, "usage": {...}}
"""

import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

JEV_URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"


def noul(instructions: str) -> dict:
    """Yes/no question -> {"noul": probability 0..1}."""
    return {"type": "noul", "instructions": instructions}


def choice(instructions: str, criteria: dict[str, str]) -> dict:
    """Pick-one question -> {"choice", "confidence", "probabilities"}."""
    return {"type": "choice", "instructions": instructions, "criteria": criteria}


def ask(state: dict | str, questions: dict[str, dict]) -> dict:
    """Send one state + question fan-out to Jev.

    Returns {"answers": ..., "usage": ..., "model": ..., "latency_ms": float}.
    """
    key = os.environ["JEV_API_KEY"]
    started = time.perf_counter()
    resp = httpx.post(
        JEV_URL,
        headers={"Authorization": f"Bearer {key}"},
        json={"model": MODEL, "state": state, "questions": questions},
        timeout=30.0,
    )
    resp.raise_for_status()
    body = resp.json()
    body["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
    return body
