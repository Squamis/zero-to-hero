"""L1.7c Best-of-N over zero-shot CoT.

Sample N completions at temperature 0.7, majority-vote the extracted answer.
The single function `best_of_n_cot` is the entire L1.7c surface — `run.py`
sweeps N values across this one function instead of L0's six-technique loop.

Why zero-shot CoT as the base prompt: on Mistral-7B-Instruct v0.1 (the L0
era-boundary model carried into L1), zero-shot CoT was the strongest L0
baseline at 40%. We sweep test-time compute on top of the best L0 prompt,
not on top of a weak baseline.

Why temperature 0.7: Best-of-N requires variance across samples to function.
At T=0 every sample is identical (greedy path), so majority-voting N copies
of the same answer is just N=1 with extra cost. T=0.7 is the practitioner
default from Wang et al. 2022 — hot enough for real reasoning-path variance,
cold enough to keep arithmetic coherent.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from client import complete
from grader import extract_answer, majority_vote


def _one_sample(
    prompt: str, temperature: float, max_tokens: int
) -> tuple[float | None, int]:
    res = complete(prompt, temperature=temperature, max_tokens=max_tokens)
    return extract_answer(res.text), res.total_tokens


def best_of_n_cot(
    question: str,
    n: int,
    *,
    temperature: float = 0.7,
    max_tokens: int = 768,
    inner_workers: int | None = None,
) -> tuple[float | None, int]:
    """Sample N zero-shot CoT completions, majority-vote the answer.

    Returns (predicted_answer, total_tokens_used) so the run loop can plot
    the cost-vs-accuracy curve.
    """
    prompt = f"Question: {question}\nAnswer: Let's think step by step."

    if n == 1:
        return _one_sample(prompt, temperature, max_tokens)

    workers = inner_workers if inner_workers is not None else min(n, 10)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(
            pool.map(
                lambda _: _one_sample(prompt, temperature, max_tokens),
                range(n),
            )
        )
    answers = [a for (a, _) in results]
    total_tokens = sum(t for (_, t) in results)
    return majority_vote(answers), total_tokens
