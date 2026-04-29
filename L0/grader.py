"""Extract numeric answers from model outputs and grade against gold."""
from __future__ import annotations

import re

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
