"""Render article figures from the result files. Light + dark variants.

Usage:  uv run python article/figs.py   (needs matplotlib: uv add --dev matplotlib)
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "article" / "img"
IMG.mkdir(parents=True, exist_ok=True)

MODES = {
    "light": {"surface": "#ffffff", "ink": "#1a1a19", "ink2": "#5f5e56",
              "grid": "#e6e5df", "series": ["#2a78d6", "#eb6834", "#1baf7a"]},
    "dark": {"surface": "#1a1a19", "ink": "#ffffff", "ink2": "#c3c2b7",
             "grid": "#3a3934", "series": ["#3987e5", "#d95926", "#199e70"]},
}

jev = [json.loads(l) for l in (ROOT / "results/shadow_20260922_020917.jsonl").open()]
qwen = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / "results/baseline_20260922_021237.jsonl").open()}
son = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / "results/sonnet_20260922_025205.jsonl").open()}


def accuracy_fig(mode: str, c: dict) -> None:
    decisions = ["category", "priority", "page_human"]
    models = ["Jev 1.13", "Qwen3.8-27B", "Sonnet 5"]
    acc = {m: [] for m in models}
    n = len(jev)
    for d in decisions:
        hits = [0, 0, 0]
        for r in jev:
            gold = r["gold"][d]
            a = r["jev"]["answers"][d]
            jans = (a["noul"] >= 0.5) if d == "page_human" else a["choice"]
            hits[0] += jans == gold
            hits[1] += qwen[r["id"]]["answer"][d] == gold
            hits[2] += son[r["id"]]["answer"][d] == gold
        for m, h in zip(models, hits):
            acc[m].append(h / n)

    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=200)
    fig.patch.set_facecolor(c["surface"])
    ax.set_facecolor(c["surface"])
    w = 0.26
    for i, m in enumerate(models):
        x = [j + (i - 1) * w for j in range(len(decisions))]
        bars = ax.bar(x, acc[m], width=w - 0.02, color=c["series"][i],
                      edgecolor=c["surface"], linewidth=2, label=m)
        for b, v in zip(bars, acc[m]):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.015, f"{v:.0%}",
                    ha="center", fontsize=8.5, color=c["ink"])
    ax.set_xticks(range(len(decisions)))
    ax.set_xticklabels(["category", "priority", "page human"], color=c["ink"], fontsize=10)
    ax.set_ylim(0, 1.12)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], color=c["ink2"], fontsize=8.5)
    ax.grid(axis="y", color=c["grid"], linewidth=0.7)
    ax.set_axisbelow(True)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    ax.legend(loc="upper right", frameon=False, fontsize=9, labelcolor=c["ink"], ncol=3,
              bbox_to_anchor=(1.0, 1.12))
    ax.set_title("Routing accuracy on 310 labeled AIOps alerts", color=c["ink"],
                 fontsize=12, loc="left", pad=26)
    fig.tight_layout()
    fig.savefig(IMG / f"accuracy_{mode}.png", facecolor=c["surface"])
    plt.close(fig)


def calibration_fig(mode: str, c: dict) -> None:
    buckets = [(0.0, 0.5), (0.5, 0.7), (0.7, 0.9), (0.9, 1.01)]
    labels = ["<0.5", "0.5–0.7", "0.7–0.9", "≥0.9"]
    stats = []
    for lo, hi in buckets:
        oks, confs = [], []
        for r in jev:
            a = r["jev"]["answers"]["category"]
            if lo <= a["confidence"] < hi:
                oks.append(a["choice"] == r["gold"]["category"])
                confs.append(a["confidence"])
        stats.append((sum(oks) / len(oks), sum(confs) / len(confs), len(oks)))

    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=200)
    fig.patch.set_facecolor(c["surface"])
    ax.set_facecolor(c["surface"])
    x = range(len(buckets))
    bars = ax.bar(x, [s[0] for s in stats], width=0.55, color=c["series"][0],
                  edgecolor=c["surface"], linewidth=2, label="actual hit rate")
    ax.scatter(x, [s[1] for s in stats], color=c["series"][1], zorder=3, s=55,
               label="mean stated confidence")
    for i, (hit, conf, n) in enumerate(stats):
        top = max(hit, conf)
        ax.text(i, top + 0.05, f"{hit:.0%}", ha="center", fontsize=9, color=c["ink"])
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{lb}\nn={s[2]}" for lb, s in zip(labels, stats)],
                       color=c["ink"], fontsize=9.5)
    ax.set_ylim(0, 1.15)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], color=c["ink2"], fontsize=8.5)
    ax.grid(axis="y", color=c["grid"], linewidth=0.7)
    ax.set_axisbelow(True)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    ax.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=c["ink"])
    ax.set_title("Jev is honest about what it doesn't know (category decision)",
                 color=c["ink"], fontsize=12, loc="left", pad=10)
    ax.set_xlabel("stated confidence bucket", color=c["ink2"], fontsize=9, labelpad=8)
    fig.tight_layout()
    fig.savefig(IMG / f"calibration_{mode}.png", facecolor=c["surface"])
    plt.close(fig)


for mode, colors in MODES.items():
    accuracy_fig(mode, colors)
    calibration_fig(mode, colors)
print("wrote", *sorted(p.name for p in IMG.glob("*.png")))
