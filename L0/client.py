"""OpenRouter client. Thin wrapper around the OpenAI SDK pointed at OpenRouter."""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MODEL_ID = os.environ.get("MODEL_ID", "mistralai/mistral-7b-instruct-v0.1")


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    api_key = os.environ["OPENROUTER_API_KEY"]
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "https://github.com/Squamis/zero-to-hero",
            "X-Title": "zero-to-hero L0",
        },
    )


def complete(prompt: str, *, temperature: float = 0.0, max_tokens: int = 512) -> str:
    resp = get_client().chat.completions.create(
        model=MODEL_ID,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""
