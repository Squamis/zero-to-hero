"""OpenRouter client for L1.

Same wire-up as L0 but `complete()` returns a `CompletionResult` (text + token
usage) so Best-of-N can track cost. The text-only L0 signature is preserved as
`complete_text()` in case anything wants the original shape.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MODEL_ID = os.environ.get("MODEL_ID", "mistralai/mistral-7b-instruct-v0.1")

# Models that route to the legacy /completions endpoint.
COMPLETION_MODELS = {
    "openai/gpt-3.5-turbo-instruct",
}


@dataclass
class CompletionResult:
    text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    api_key = os.environ["OPENROUTER_API_KEY"]
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "https://github.com/Squamis/zero-to-hero",
            "X-Title": "zero-to-hero L1",
        },
    )


def complete(
    prompt: str,
    *,
    temperature: float = 0.0,
    max_tokens: int = 512,
    model: str | None = None,
) -> CompletionResult:
    model = model or MODEL_ID
    client = get_client()
    if model in COMPLETION_MODELS:
        resp = client.completions.create(
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text = resp.choices[0].text or ""
    else:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text = resp.choices[0].message.content or ""
    usage = resp.usage
    return CompletionResult(
        text=text,
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
        total_tokens=usage.total_tokens if usage else 0,
    )


def complete_text(
    prompt: str,
    *,
    temperature: float = 0.0,
    max_tokens: int = 512,
    model: str | None = None,
) -> str:
    """Backward-compatible text-only wrapper. Same signature as L0's `complete`."""
    return complete(
        prompt, temperature=temperature, max_tokens=max_tokens, model=model
    ).text
