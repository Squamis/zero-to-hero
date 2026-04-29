"""Run the L0 benchmark across all techniques and save results to JSON."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone

# Allow running as `python L0/run.py` from repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tqdm import tqdm

from client import MODEL_ID
from data import load_problems
from grader import is_correct
from techniques import TECHNIQUES


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=50, help="number of GSM8K problems")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--techniques",
        nargs="+",
        default=list(TECHNIQUES.keys()),
        help="subset of techniques to run",
    )
    parser.add_argument(
        "--out",
        default=os.path.join(os.path.dirname(__file__), "results", "results.json"),
    )
    args = parser.parse_args()

    problems = load_problems(n=args.n, seed=args.seed)
    print(f"Loaded {len(problems)} GSM8K problems (seed={args.seed})")
    print(f"Model: {MODEL_ID}")
    print(f"Techniques: {args.techniques}\n")

    results: dict = {
        "model": MODEL_ID,
        "n_problems": len(problems),
        "seed": args.seed,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "techniques": {},
    }

    for name in args.techniques:
        if name not in TECHNIQUES:
            print(f"  unknown technique '{name}', skipping")
            continue
        fn = TECHNIQUES[name]
        per_problem = []
        n_correct = 0
        t0 = time.time()
        for prob in tqdm(problems, desc=name):
            try:
                pred = fn(prob.question)
                err = None
            except Exception as e:
                pred = None
                err = f"{type(e).__name__}: {e}"
                traceback.print_exc()
            ok = is_correct(pred, prob.answer)
            n_correct += int(ok)
            per_problem.append(
                {
                    "question": prob.question,
                    "gold": prob.answer,
                    "predicted": pred,
                    "correct": ok,
                    "error": err,
                }
            )
        elapsed = time.time() - t0
        accuracy = n_correct / len(problems)
        results["techniques"][name] = {
            "accuracy": accuracy,
            "n_correct": n_correct,
            "elapsed_seconds": elapsed,
            "per_problem": per_problem,
        }
        print(f"  {name}: {n_correct}/{len(problems)} = {accuracy:.1%} ({elapsed:.1f}s)\n")

        # Persist after every technique so partial runs aren't lost.
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(results, f, indent=2)

    results["finished_at"] = datetime.now(timezone.utc).isoformat()
    with open(args.out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
