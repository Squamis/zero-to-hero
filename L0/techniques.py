"""The six L0 prompting techniques.

Each technique is a function that takes a question and returns a final-answer
prediction (float or None). All techniques use the shared `client.complete()`
under the hood. Few-shot exemplars are drawn from the GSM8K training split
(see `FEW_SHOT_EXEMPLARS` below) — fixed, hand-picked, not retrieved.
"""
from __future__ import annotations

from collections import Counter

from client import complete
from grader import extract_answer

# 4 fixed few-shot exemplars from the GSM8K training set.
# Verified against datasets viewer; answers cross-checked.
FEW_SHOT_EXEMPLARS = [
    {
        "q": "Janet's ducks lay 16 eggs per day. She eats three for breakfast every morning and bakes muffins for her friends every day with four. She sells the remainder at the farmers' market daily for $2 per fresh duck egg. How much in dollars does she make every day at the farmers' market?",
        "a": "16 - 3 - 4 = 9 eggs sold. 9 * $2 = $18. The answer is 18.",
    },
    {
        "q": "A robe takes 2 bolts of blue fiber and half that much white fiber. How many bolts in total does it take?",
        "a": "Blue: 2 bolts. White: 2/2 = 1 bolt. Total: 2 + 1 = 3. The answer is 3.",
    },
    {
        "q": "Josh decides to try flipping a house. He buys a house for $80,000 and then puts in $50,000 in repairs. This increased the value of the house by 150%. How much profit did he make?",
        "a": "Increase: 80000 * 1.5 = 120000. New value: 80000 + 120000 = 200000. Cost: 80000 + 50000 = 130000. Profit: 200000 - 130000 = 70000. The answer is 70000.",
    },
    {
        "q": "James decides to run 3 sprints 3 times a week. He runs 60 meters each sprint. How many total meters does he run a week?",
        "a": "Sprints per week: 3 * 3 = 9. Meters per week: 9 * 60 = 540. The answer is 540.",
    },
]


# --- Technique 1: zero-shot ----------------------------------------------------

def zero_shot(question: str) -> float | None:
    prompt = f"Question: {question}\nAnswer:"
    out = complete(prompt, temperature=0.0)
    return extract_answer(out)


# --- Technique 2: role prompting -----------------------------------------------

def role_prompt(question: str) -> float | None:
    prompt = (
        "You are an expert mathematician who solves arithmetic word problems "
        "carefully and accurately.\n\n"
        f"Question: {question}\nAnswer:"
    )
    out = complete(prompt, temperature=0.0)
    return extract_answer(out)


# --- Technique 3: few-shot (no reasoning shown) --------------------------------

def few_shot(question: str) -> float | None:
    blocks = [
        f"Question: {ex['q']}\nAnswer: The answer is "
        f"{ex['a'].split('The answer is ')[1]}"
        for ex in FEW_SHOT_EXEMPLARS
    ]
    prompt = "\n\n".join(blocks) + f"\n\nQuestion: {question}\nAnswer:"
    out = complete(prompt, temperature=0.0)
    return extract_answer(out)


# --- Technique 4: zero-shot CoT ("Let's think step by step") -------------------

def zero_shot_cot(question: str) -> float | None:
    prompt = f"Question: {question}\nAnswer: Let's think step by step."
    out = complete(prompt, temperature=0.0, max_tokens=768)
    return extract_answer(out)


# --- Technique 5: few-shot CoT (Wei et al. 2022) -------------------------------

def few_shot_cot(question: str) -> float | None:
    blocks = [f"Question: {ex['q']}\nAnswer: {ex['a']}" for ex in FEW_SHOT_EXEMPLARS]
    prompt = "\n\n".join(blocks) + f"\n\nQuestion: {question}\nAnswer:"
    out = complete(prompt, temperature=0.0, max_tokens=768)
    return extract_answer(out)


# --- Technique 6: self-consistency (Wang et al. 2022) --------------------------
#
# Sample N CoT traces at temp=0.7, take the majority vote on extracted answer.

SELF_CONSISTENCY_N = 5


def self_consistency(question: str) -> float | None:
    blocks = [f"Question: {ex['q']}\nAnswer: {ex['a']}" for ex in FEW_SHOT_EXEMPLARS]
    prompt = "\n\n".join(blocks) + f"\n\nQuestion: {question}\nAnswer:"
    answers: list[float] = []
    for _ in range(SELF_CONSISTENCY_N):
        out = complete(prompt, temperature=0.7, max_tokens=768)
        ans = extract_answer(out)
        if ans is not None:
            answers.append(ans)
    if not answers:
        return None
    return Counter(answers).most_common(1)[0][0]


TECHNIQUES = {
    "zero-shot": zero_shot,
    "role": role_prompt,
    "few-shot": few_shot,
    "zero-shot CoT": zero_shot_cot,
    "few-shot CoT": few_shot_cot,
    "self-consistency": self_consistency,
}
