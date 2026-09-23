"""Social cards: light (LinkedIn) + dark (X), 1600x900.

Usage:  uv run python article/cards.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

IMG = Path(__file__).resolve().parent / "img"

MODES = {
    "light": {"surface": "#FBFAF7", "panel": "#F2F0EA", "ink": "#17160F",
              "ink2": "#55534A", "line": "#E4E1D8",
              "series": ["#2a78d6", "#eb6834", "#1baf7a"]},
    "dark": {"surface": "#1a1a19", "panel": "#242320", "ink": "#FFFFFF",
             "ink2": "#c3c2b7", "line": "#3a3934",
             "series": ["#3987e5", "#d95926", "#199e70"]},
}

TILES = [
    ("CATEGORY ACCURACY", "95%", "at 331ms median"),
    ("COST PER 1M ALERTS", "~$23", "vs ~$2,430 Sonnet 5"),
    ("HYBRID ROUTER", "97%", "escalating only 15%"),
    ("TOTAL EXPERIMENT SPEND", "$0.77", "measured, everything"),
]

# category / priority / page_human accuracy per model
BARS = {"Jev 1.13": [95, 72, 79], "Qwen3.8-27B": [97, 75, 87], "Sonnet 5": [98, 70, 88]}


def card(mode: str, c: dict) -> None:
    fig = plt.figure(figsize=(16, 9), dpi=100)
    fig.patch.set_facecolor(c["surface"])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1600)
    ax.set_ylim(0, 900)
    ax.invert_yaxis()
    ax.axis("off")

    # accent tick + eyebrow
    ax.add_patch(plt.Rectangle((80, 84), 46, 7, color=c["series"][0]))
    ax.text(142, 96, "LAB NOTEBOOK  /  SHADOW-MODE EVAL", fontsize=15,
            color=c["series"][0], fontweight="bold", family="Helvetica Neue", va="center")
    ax.text(1520, 96, "310 labeled AIOps alerts · suryal.dev", fontsize=14,
            color=c["ink2"], family="Helvetica Neue", va="center", ha="right")

    ax.text(80, 200, "Testing Jev:", fontsize=58, color=c["ink"],
            family="Helvetica Neue", fontweight="bold", va="center")
    ax.text(80, 288, "can a model that can't talk route my alerts?",
            fontsize=38, color=c["ink"], family="Helvetica Neue", va="center")
    ax.text(80, 360, "Jev 1.13  vs  Qwen3.8-27B (local)  vs  Claude Sonnet 5",
            fontsize=19, color=c["ink2"], family="Helvetica Neue", va="center")

    # accuracy mini-chart (right side)
    x0, y0, w = 900, 430, 620
    ax.text(x0, y0 - 14, "accuracy · category / priority / page-human",
            fontsize=13, color=c["ink2"], family="Helvetica Neue")
    bar_h, gap = 22, 10
    y = y0 + 16
    for mi, (model, vals) in enumerate(BARS.items()):
        ax.text(x0, y + bar_h * 1.5 + gap, model, fontsize=14, color=c["ink"],
                family="Helvetica Neue", fontweight="bold", va="center",
                rotation=0) if False else None
        for vi, v in enumerate(vals):
            yy = y + vi * (bar_h + 4)
            ax.add_patch(plt.Rectangle((x0 + 150, yy), w - 150, bar_h,
                                       color=c["panel"], ec=c["line"], lw=1))
            ax.add_patch(plt.Rectangle((x0 + 150, yy), (w - 150) * v / 100, bar_h,
                                       color=c["series"][mi]))
            ax.text(x0 + 150 + (w - 150) * v / 100 + 10, yy + bar_h / 2, f"{v}%",
                    fontsize=12, color=c["ink"], family="Helvetica Neue", va="center")
        ax.text(x0, y + (bar_h + 4) * 1.5 - 2, model, fontsize=13, color=c["ink"],
                family="Helvetica Neue", fontweight="bold", va="center")
        y += 3 * (bar_h + 4) + 18

    # stat tiles (left column, 2x2)
    tw, th, tx, ty, tgap = 380, 150, 80, 430, 20
    for i, (label, big, sub) in enumerate(TILES):
        px = tx + (i % 2) * (tw + tgap)
        py = ty + (i // 2) * (th + tgap)
        ax.add_patch(FancyBboxPatch((px, py), tw, th,
                                    boxstyle="round,pad=0,rounding_size=14",
                                    fc=c["panel"], ec=c["line"], lw=1.2))
        ax.text(px + 24, py + 36, label, fontsize=12, color=c["ink2"],
                family="Helvetica Neue", va="center")
        ax.text(px + 24, py + 84, big, fontsize=36, color=c["ink"],
                family="Helvetica Neue", fontweight="bold", va="center")
        ax.text(px + 24, py + 124, sub, fontsize=13, color=c["ink2"],
                family="Helvetica Neue", va="center")

    # takeaway strip
    ax.add_patch(plt.Rectangle((80, 786), 7, 26, color=c["series"][0]))
    ax.text(102, 799, "Fast, cheap, and it knows when it's unsure — a strong candidate "
                      "for AIOps & SRE agentic flows.",
            fontsize=19, color=c["ink"], family="Helvetica Neue",
            fontweight="bold", va="center")

    ax.text(102, 848, "One experiment, every result in the repo:  github.com/Suryals/jev-router-lab",
            fontsize=15, color=c["ink2"], family="Helvetica Neue", va="center")

    out = IMG / f"card_{mode}.png"
    fig.savefig(out, facecolor=c["surface"])
    plt.close(fig)
    print("wrote", out.name)


for mode, colors in MODES.items():
    card(mode, colors)
