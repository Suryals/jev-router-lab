# Social copy — Jev article

Attach: `card_light.png` on LinkedIn, `card_dark.png` on X.
Article: https://suryal.dev/articles/jev-vs-qwen3-8-27b-vs-claude-sonnet-5.html
Repo: https://github.com/Suryals/jev-router-lab

---

## LinkedIn (light card)

A model that can't generate text just out-routed my LLM.

TypeSafe launched Jev last week — a "System One model." No text generation at
all: you send state plus typed questions, it returns probability
distributions. Their pitch is "a smart if statement."

I route alerts through an LLM today, so I tested the claim properly: 310
labeled AIOps alerts, three decisions each (category, priority,
page-or-not). Jev vs a local Qwen3.8-27B vs Claude Sonnet 5, shadow mode,
everything logged and scored.

What held up:

— Jev: 95% category accuracy at 331ms median, ~$23 per million alerts.
Sonnet 5: 98% at 4.6s and ~$2,430 per million.
— Calibration is the real story. When Jev states ≥0.9 confidence it's right
98% of the time, so a hybrid — Jev decides everything, the LLM only sees the
low-confidence 15% — matches the LLMs at 97% for roughly 1% of the cost.
— Most useful failure: my first benchmark measured my own TLS handshakes,
not the model. One persistent HTTP client took "Jev latency" from 850ms to
331ms.

What didn't hold up: yes/no paging decisions (Jev 79% vs 87–88% for the
LLMs), and priority was mediocre for all three models — which smells like my
gold labels, not the models. That's in the caveats.

Total spend for the whole experiment: $0.77.

Write-up with charts: https://suryal.dev/articles/jev-vs-qwen3-8-27b-vs-claude-sonnet-5.html
Code, dataset, every result: https://github.com/Suryals/jev-router-lab

---

## X (dark card) — single post

Jev can't write a sentence. It might still take the routing layer of my
agent stack.

310 AIOps alerts, shadow mode: Jev vs local Qwen3.8-27B vs Claude Sonnet 5.

Jev: 95% category @ 331ms, ~$23/1M alerts
Sonnet 5: 98% @ 4.6s, ~$2,430/1M

The story is calibration: conf ≥0.9 → right 98% of the time. Gate on it and
a Jev+local-LLM hybrid hits 97% while the LLM sees only 15% of traffic.

https://suryal.dev/articles/jev-vs-qwen3-8-27b-vs-claude-sonnet-5.html

---

## X — optional follow-up replies (thread)

2/ Favorite single result: Dataproc cluster losing workers, autoscaler
recovering. Jev answered correctly at 0.34 confidence — "here's my guess,
escalate this one." That's exactly what you want from an L1.

3/ Most useful failure: my first run measured p50 850ms and I nearly wrote
off their latency claims. It was my own TLS handshakes — fresh connection
per call. Pooled client: 331ms. Benchmark your client before you benchmark
the model.

4/ Where Jev loses: yes/no paging (79% vs 87–88%) and everyone was mediocre
at priority (70–75%) — three very different models agreeing to be mediocre
usually means the labels are the problem. Caveats in the post. Repo:
github.com/Suryals/jev-router-lab
