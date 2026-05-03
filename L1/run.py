"""Run the L1.7c Best-of-N sweep across N values, save results to JSON.

For each N in --ns, run all problems with N samples at temperature 0.7 and
majority-vote the extracted answer. Persists `results/results.json` after
every N value so partial runs survive interruption.

Outer parallelism: --workers problems run concurrently.
Inner parallelism: each problem's N samples run concurrently up to
                   --inner-workers.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

# Allow running as `python L1/run.py` from repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tqdm import tqdm

import client
from data import load_problems
from grader import is_correct
from techniques import best_of_n_cot


DEFAULT_NS = [1, 3, 5, 10, 20, 40]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=50, help="number of GSM8K problems")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument(
        "--ns",
        nargs="+",
        type=int,
        default=DEFAULT_NS,
        help="N values to sweep (samples per problem before majority vote)",
    )
    parser.add_argument(
        "--out",
        default=os.path.join(os.path.dirname(__file__), "results", "results.json"),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="problem-level concurrency (each problem also fans out N samples)",
    )
    parser.add_argument(
        "--inner-workers",
        type=int,
        default=10,
        help="cap on per-problem sample concurrency",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="override MODEL_ID from .env",
    )
    args = parser.parse_args()

    if args.model:
        client.MODEL_ID = args.model

    problems = load_problems(n=args.n, seed=args.seed)
    active_model = client.MODEL_ID
    print(f"Loaded {len(problems)} GSM8K problems (seed={args.seed})")
    print(f"Model: {active_model}")
    print(f"Temperature: {args.temperature}")
    print(f"Sweeping N values: {args.ns}\n")

    results: dict = {
        "model": active_model,
        "n_problems": len(problems),
        "seed": args.seed,
        "temperature": args.temperature,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "sweeps": {},
    }

    def run_one(prob, n_value):
        try:
            pred, tokens = best_of_n_cot(
                prob.question,
                n_value,
                temperature=args.temperature,
                inner_workers=args.inner_workers,
            )
            err = None
        except Exception as e:
            pred, tokens = None, 0
            err = f"{type(e).__name__}: {e}"
            traceback.print_exc()
        return prob, pred, tokens, err

    for n_val in args.ns:
        per_problem = [None] * len(problems)
        n_correct = 0
        total_tokens = 0
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(run_one, p, n_val): i for i, p in enumerate(problems)}
            with tqdm(total=len(problems), desc=f"N={n_val}") as pbar:
                for fut in as_completed(futures):
                    i = futures[fut]
                    prob, pred, tokens, err = fut.result()
                    ok = is_correct(pred, prob.answer)
                    n_correct += int(ok)
                    total_tokens += tokens
                    per_problem[i] = {
                        "question": prob.question,
                        "gold": prob.answer,
                        "predicted": pred,
                        "correct": ok,
                        "tokens": tokens,
                        "error": err,
                    }
                    pbar.update(1)
        elapsed = time.time() - t0
        accuracy = n_correct / len(problems)
        results["sweeps"][str(n_val)] = {
            "n_samples": n_val,
            "accuracy": accuracy,
            "n_correct": n_correct,
            "total_tokens": total_tokens,
            "elapsed_seconds": elapsed,
            "per_problem": per_problem,
        }
        print(
            f"  N={n_val}: {n_correct}/{len(problems)} = {accuracy:.1%} "
            f"({total_tokens:,} tokens, {elapsed:.1f}s)\n"
        )

        # Persist after every N so partial runs aren't lost.
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(results, f, indent=2)

    results["finished_at"] = datetime.now(timezone.utc).isoformat()
    with open(args.out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
