# Social copy — Jev article

Attach: `card_light.png` on LinkedIn, `card_dark.png` on X.
Article: https://suryal.dev/articles/jev-vs-qwen3-8-27b-vs-claude-sonnet-5.html
Repo: https://github.com/Suryals/jev-router-lab

---

## LinkedIn (light card)

Jev launched last week. It's a model that doesn't generate text. You send it
a question with typed options and it sends back probabilities. That's the
whole model.

The launch claims (100x faster, 200x cheaper than an LLM on the same
decision) read like launch claims, but I have an actual use for this: the
ops agent I'm building makes every routing decision through an LLM call
today. So I ran Jev against 310 labeled alerts, with a local Qwen3.8-27B and
Claude Sonnet 5 as the bar to clear. Shadow mode, everything logged.

On categorising alerts Jev got 95% to Sonnet's 98%, at 331ms instead of
4.6s, for about 1% of the cost. Fine. The part I actually care about is that
its confidence numbers turned out to be honest: when it says 0.9 or above,
it's right 98% of the time. Which means you can let Jev route everything and
only send the uncertain 15% to an LLM. That hybrid scored the same 97% as
the LLMs did on their own.

It's noticeably worse at the yes/no "page a human?" call. And all three
models were mediocre at assigning priority, which probably says more about
my labels than about any of the models. Both of those are in the caveats
section, where they belong.

I also spent the first hour of this benchmarking my own TLS handshakes
instead of the model. That's in the write-up too.

Total API spend for the whole experiment: $0.77.

Write-up: https://suryal.dev/articles/jev-vs-qwen3-8-27b-vs-claude-sonnet-5.html
Dataset and every result: https://github.com/Suryals/jev-router-lab

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
