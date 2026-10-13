"""Figures for the midterm report.

Every value is read from the saved run summaries, so the figures cannot drift
from the tables.
"""

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

ACCENT = "#C00000"
GREY = "#8C8C8C"
INK = "#222222"

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 8,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


def fig_prf(summary, out):
    base, lite = summary["baseline"], summary["verifact_lite"]
    labels = ["Precision", "Recall", "F1"]
    b = [base["precision"], base["recall"], base["f1"]]
    v = [lite["precision"], lite["recall"], lite["f1"]]

    fig, ax = plt.subplots(figsize=(3.4, 2.1), dpi=300)
    x = range(len(labels))
    w = 0.36
    ax.bar([i - w / 2 for i in x], b, w, label="Baseline", color=GREY)
    ax.bar([i + w / 2 for i in x], v, w, label="VERIFACT-Lite", color=ACCENT)
    for i, (bb, vv) in enumerate(zip(b, v)):
        ax.text(i - w / 2, bb + 0.012, f"{bb:.3f}", ha="center", fontsize=6.5)
        ax.text(i + w / 2, vv + 0.012, f"{vv:.3f}", ha="center", fontsize=6.5)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 0.55)
    ax.set_ylabel("score")
    ax.legend(frameon=False, fontsize=7, loc="upper right", ncol=1)
    ax.grid(axis="y", color="#E6E6E6", linewidth=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout(pad=0.3)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig_judge(laptop, colab_a, out):
    """The same baseline facts, scored by detectors of different size."""
    labels = ["3B detector", "7B detector", "GPT-4o\n(paper, SAFE)"]
    values = [
        laptop["baseline"]["incomplete_rate"],
        colab_a["baseline"]["incomplete_rate"],
        0.567,
    ]
    colors = [GREY, ACCENT, "#D9D9D9"]

    fig, ax = plt.subplots(figsize=(3.4, 2.1), dpi=300)
    bars = ax.bar(labels, values, 0.5, color=colors, edgecolor=INK, linewidth=0.4)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.012, f"{value:.3f}", ha="center", fontsize=7)
    ax.set_ylim(0, 0.68)
    ax.set_ylabel("incomplete-fact rate")
    ax.grid(axis="y", color="#E6E6E6", linewidth=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout(pad=0.3)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def main():
    laptop = load("outputs/summary.json")
    colab_a = load("outputs_colab_a/summary.json")
    fig_prf(laptop, os.path.join(HERE, "fig_prf.png"))
    fig_judge(laptop, colab_a, os.path.join(HERE, "fig_judge.png"))
    print("wrote fig_prf.png and fig_judge.png")


if __name__ == "__main__":
    main()
