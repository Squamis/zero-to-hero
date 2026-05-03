"""Extract numeric answers from model outputs, grade against gold, and
majority-vote across samples for Best-of-N."""
from __future__ import annotations

import re
from collections import Counter

NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*")


def extract_answer(text: str) -> float | None:
    """Pull a single numeric answer from a model response.

    Strategy: prefer a number that follows an explicit cue ("answer:", "####",
    "= ..."). Fall back to the last number in the text.
    """
    if not text:
        return None

    cues = [
        r"####\s*(-?\d[\d,]*\.?\d*)",
        r"answer\s*(?:is)?\s*[:=]?\s*\$?\s*(-?\d[\d,]*\.?\d*)",
        r"final\s*answer\s*[:=]?\s*\$?\s*(-?\d[\d,]*\.?\d*)",
        r"=\s*\$?\s*(-?\d[\d,]*\.?\d*)\s*\.?\s*$",
        r"\\boxed\{\s*\$?\s*(-?\d[\d,]*\.?\d*)\s*\}",
    ]
    for pat in cues:
        m = re.search(pat, text, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                continue

    matches = NUMBER_RE.findall(text)
    if not matches:
        return None
    try:
        return float(matches[-1].replace(",", ""))
    except ValueError:
        return None


def is_correct(predicted: float | None, gold: float, tol: float = 1e-3) -> bool:
    if predicted is None:
        return False
    return abs(predicted - gold) < tol


def majority_vote(answers: list[float | None]) -> float | None:
    """Take the most common non-None answer.

    Ties broken by Counter's insertion order (first-occurrence wins).
    Returns None only if all samples failed to produce an extractable answer.
    """
    valid = [a for a in answers if a is not None]
    if not valid:
        return None
    return Counter(valid).most_common(1)[0][0]
