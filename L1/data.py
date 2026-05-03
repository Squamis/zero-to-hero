"""GSM8K loader. Samples N problems from the test split with a fixed seed.

Verbatim from L0 so the L1 sweep operates on the same 50 problems as L0's
self-consistency baseline (seed=42). Direct apples-to-apples comparison.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from datasets import load_dataset


@dataclass
class Problem:
    question: str
    answer_text: str
    answer: float


def _parse_gold(answer_text: str) -> float:
    # GSM8K gold answers end with "#### <number>"
    final = answer_text.split("####")[-1].strip().replace(",", "")
    return float(final)


def load_problems(n: int = 50, seed: int = 42) -> list[Problem]:
    ds = load_dataset("gsm8k", "main", split="test")
    rng = random.Random(seed)
    indices = rng.sample(range(len(ds)), n)
    return [
        Problem(
            question=ds[i]["question"],
            answer_text=ds[i]["answer"],
            answer=_parse_gold(ds[i]["answer"]),
        )
        for i in indices
    ]
