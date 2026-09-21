# jev-router-lab

Shadow-mode evaluation of [TypeSafe Jev](https://www.typesafe.ai) (`jev-1.13.0`,
the decision-only "System One" model) as the L1 triage router for the AIOps
prototype: can a ~100ms, $0.042/MTok classifier replace an LLM at the
supervisor's routing decisions?

## The experiment

Every alert gets three typed questions (`src/triage.py`): **category**
(choice), **priority** (P1/P2/P3 choice), **page_human** (noul). Jev answers
in shadow mode — nothing acts on its output — and every answer, probability,
latency, and token count is logged against hand-written gold labels.

Measured: accuracy per decision, **calibration** (does confidence 0.9 mean
right 90% of the time?), latency, cost per 1k routing decisions. Baseline
comparison (local Qwen via LM Studio, frontier LLM) plugs into
`baseline_router()` in `src/shadow.py`.

## Run it

```bash
cp .env.example .env        # put JEV_API_KEY in it
uv sync
uv run python -m src.shadow
uv run python -m src.evaluate results/shadow_<timestamp>.jsonl
```

## Layout

| Path | What |
|---|---|
| `src/jev_client.py` | raw httpx client (verified API quirks documented inline) |
| `src/triage.py` | the shared decision schema both routers answer |
| `src/shadow.py` | shadow runner → `results/*.jsonl` |
| `src/evaluate.py` | accuracy scaffold + `calibration()` **(spine, TODO Chief)** |
| `src/policy.py` | automate / escalate_llm / page_human ladder **(spine, TODO Chief)** |
| `data/alerts.jsonl` | 10 labeled synthetic alerts — expand to 20-30 before trusting numbers |

## Status

- [x] scaffold + live smoke test against jev-1.13.0
- [ ] expand dataset to 20-30 labeled alerts
- [ ] hand-write `calibration()` and `policy.route()`
- [ ] wire `baseline_router()` to local model
- [ ] write up (MLX Lab episode candidate)
