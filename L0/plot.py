"""Render results.json into a labelled bar chart."""
from __future__ import annotations

import argparse
import json
import os

import matplotlib.pyplot as plt

DEFAULT_ORDER = [
    "zero-shot",
    "role",
    "few-shot",
    "zero-shot CoT",
    "few-shot CoT",
    "self-consistency",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results",
        default=os.path.join(os.path.dirname(__file__), "results", "results.json"),
    )
    parser.add_argument(
        "--out",
        default=os.path.join(os.path.dirname(__file__), "results", "accuracy.png"),
    )
    args = parser.parse_args()

    with open(args.results) as f:
        data = json.load(f)

    names = [n for n in DEFAULT_ORDER if n in data["techniques"]]
    accs = [data["techniques"][n]["accuracy"] * 100 for n in names]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(names, accs, color="#3a86ff", edgecolor="black", linewidth=0.5)
    for bar, acc in zip(bars, accs):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{acc:.0f}%",
            ha="center",
            fontsize=10,
        )

    ax.set_ylabel("GSM8K accuracy (%)")
    ax.set_ylim(0, max(accs) * 1.2 + 5)
    ax.set_title(
        f"L0 prompt engineering — {data['model']}\n"
        f"GSM8K test, n={data['n_problems']} (seed={data['seed']})"
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    plt.savefig(args.out, dpi=150)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
