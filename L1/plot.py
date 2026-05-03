"""Two-panel curve from L1 Best-of-N results: accuracy vs N (left), tokens vs N (right).

Single-model mode (one --results file): one accuracy curve, one cost curve.
Comparison mode (multiple --results files): one accuracy line per model overlaid,
one cost line per model overlaid. Mirrors L0's plot.py pattern.

Optional reference line on the accuracy panel for the L0 zero-shot CoT baseline
(40% on Mistral-7B-Instruct v0.1 at T=0) — useful to see how stochastic-T=0.7
single-sample compares to deterministic-T=0 single-sample.
"""
from __future__ import annotations

import argparse
import json
import os

import matplotlib.pyplot as plt

PALETTE = ["#3a86ff", "#fb5607", "#06a77d", "#ffbe0b", "#8338ec"]


def load_runs(paths: list[str]) -> list[dict]:
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
        default=[
            os.path.join(os.path.dirname(__file__), "results", "results_mistral.json")
        ],
        help="one or more results JSON files; multiple => comparison plot",
    )
    parser.add_argument(
        "--out",
        default=os.path.join(
            os.path.dirname(__file__), "results", "best_of_n_curve.png"
        ),
    )
    parser.add_argument("--title", default=None)
    parser.add_argument(
        "--l0-baseline",
        type=float,
        default=40.0,
        help="L0 zero-shot CoT accuracy reference line (percent). Set <0 to hide.",
    )
    args = parser.parse_args()

    runs = load_runs(args.results)

    fig, (ax_acc, ax_tok) = plt.subplots(1, 2, figsize=(13, 5))

    max_acc = 0.0
    for i, r in enumerate(runs):
        sweeps = sorted(r["sweeps"].values(), key=lambda s: s["n_samples"])
        ns = [s["n_samples"] for s in sweeps]
        accs = [s["accuracy"] * 100 for s in sweeps]
        tokens = [s["total_tokens"] for s in sweeps]
        max_acc = max(max_acc, max(accs) if accs else 0)

        label = r["model"].split("/", 1)[-1]
        color = PALETTE[i % len(PALETTE)]

        # Accuracy curve.
        ax_acc.plot(ns, accs, marker="o", color=color, linewidth=2, label=label)
        for x, y in zip(ns, accs):
            ax_acc.annotate(
                f"{y:.0f}%",
                (x, y),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
                fontsize=9,
                color=color,
            )

        # Cost curve.
        ax_tok.plot(ns, tokens, marker="o", color=color, linewidth=2, label=label)
        if len(runs) == 1:
            for x, y in zip(ns, tokens):
                ax_tok.annotate(
                    f"{y/1000:.0f}k",
                    (x, y),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha="center",
                    fontsize=9,
                )

    if args.l0_baseline >= 0:
        ax_acc.axhline(
            args.l0_baseline,
            color="#888",
            linestyle="--",
            linewidth=1.2,
            label=f"L0 zero-shot CoT @ T=0 ({args.l0_baseline:.0f}% on Mistral)",
        )

    ax_acc.set_xlabel("N (samples per problem)")
    ax_acc.set_ylabel("GSM8K accuracy (%)")
    ax_acc.set_title("Accuracy vs N")
    ymax = max(max_acc, args.l0_baseline if args.l0_baseline >= 0 else 0)
    ax_acc.set_ylim(0, max(ymax * 1.25, 50))

    ns_union = sorted({n for r in runs for n in [s["n_samples"] for s in r["sweeps"].values()]})
    ax_acc.set_xscale("log")
    ax_acc.set_xticks(ns_union)
    ax_acc.set_xticklabels([str(n) for n in ns_union])
    ax_acc.grid(True, linestyle="--", alpha=0.4)
    ax_acc.spines["top"].set_visible(False)
    ax_acc.spines["right"].set_visible(False)
    ax_acc.legend(loc="lower right", fontsize=9)

    ax_tok.set_xlabel("N (samples per problem)")
    ax_tok.set_ylabel("Total tokens (sum across all problems)")
    ax_tok.set_title("Cost vs N")
    ax_tok.set_xscale("log")
    ax_tok.set_yscale("log")
    ax_tok.set_xticks(ns_union)
    ax_tok.set_xticklabels([str(n) for n in ns_union])
    ax_tok.grid(True, linestyle="--", alpha=0.4, which="both")
    ax_tok.spines["top"].set_visible(False)
    ax_tok.spines["right"].set_visible(False)
    if len(runs) > 1:
        ax_tok.legend(loc="lower right", fontsize=9)

    if len(runs) == 1:
        r = runs[0]
        title = args.title or (
            f"L1.7c Best-of-N — {r['model']}\n"
            f"GSM8K test, n={r['n_problems']} (seed={r['seed']}, T={r['temperature']})"
        )
    else:
        seeds = sorted({r["seed"] for r in runs})
        ns_problems = sorted({r["n_problems"] for r in runs})
        temps = sorted({r["temperature"] for r in runs})
        title = args.title or (
            f"L1.7c Best-of-N — model comparison\n"
            f"GSM8K test, n={ns_problems} (seed={seeds}, T={temps})"
        )

    fig.suptitle(title)
    fig.tight_layout()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    plt.savefig(args.out, dpi=150)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
