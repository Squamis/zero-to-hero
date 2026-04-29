"""Render results.json into a labelled bar chart.

Single-model mode (one --results file): one bar per technique.
Multi-model comparison (multiple --results files): grouped bars per technique,
one bar per model. Useful for showing "each generation absorbs prior techniques."
"""
from __future__ import annotations

import argparse
import json
import os

import matplotlib.pyplot as plt
import numpy as np

DEFAULT_ORDER = [
    "zero-shot",
    "role",
    "few-shot",
    "zero-shot CoT",
    "few-shot CoT",
    "self-consistency",
]

PALETTE = ["#3a86ff", "#fb5607", "#06a77d", "#ffbe0b", "#8338ec"]


def load_results(paths: list[str]) -> list[dict]:
    out = []
    for p in paths:
        with open(p) as f:
            out.append(json.load(f))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results",
        nargs="+",
        default=[os.path.join(os.path.dirname(__file__), "results", "results.json")],
        help="one or more results.json files; multiple => comparison plot",
    )
    parser.add_argument(
        "--out",
        default=os.path.join(os.path.dirname(__file__), "results", "accuracy.png"),
    )
    parser.add_argument("--title", default=None)
    args = parser.parse_args()

    runs = load_results(args.results)

    # All techniques present across runs, in canonical order.
    techniques = [
        n for n in DEFAULT_ORDER if any(n in r["techniques"] for r in runs)
    ]

    fig, ax = plt.subplots(figsize=(11, 6))

    if len(runs) == 1:
        r = runs[0]
        accs = [r["techniques"].get(n, {}).get("accuracy", 0) * 100 for n in techniques]
        bars = ax.bar(techniques, accs, color=PALETTE[0], edgecolor="black", linewidth=0.5)
        for bar, acc in zip(bars, accs):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{acc:.0f}%",
                ha="center",
                fontsize=10,
            )
        title = args.title or (
            f"L0 prompt engineering — {r['model']}\n"
            f"GSM8K test, n={r['n_problems']} (seed={r['seed']})"
        )
    else:
        n_models = len(runs)
        x = np.arange(len(techniques))
        bar_w = 0.8 / n_models
        for i, r in enumerate(runs):
            accs = [r["techniques"].get(n, {}).get("accuracy", 0) * 100 for n in techniques]
            offsets = x + (i - (n_models - 1) / 2) * bar_w
            label = r["model"].split("/", 1)[-1]
            bars = ax.bar(
                offsets, accs, bar_w, label=label,
                color=PALETTE[i % len(PALETTE)], edgecolor="black", linewidth=0.5,
            )
            for bar, acc in zip(bars, accs):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 1,
                    f"{acc:.0f}",
                    ha="center", fontsize=8,
                )
        ax.set_xticks(x)
        ax.set_xticklabels(techniques, rotation=15, ha="right")
        ax.legend(loc="upper left")
        seeds = sorted({r["seed"] for r in runs})
        ns = sorted({r["n_problems"] for r in runs})
        title = args.title or (
            f"L0 prompt engineering — model comparison\n"
            f"GSM8K test, n={ns} (seed={seeds})"
        )

    ax.set_ylabel("GSM8K accuracy (%)")
    ax.set_title(title)
    ax.set_ylim(0, 100)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    if len(runs) == 1:
        plt.xticks(rotation=15, ha="right")
    plt.tight_layout()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    plt.savefig(args.out, dpi=150)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
