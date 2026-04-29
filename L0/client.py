"""OpenRouter client. Thin wrapper around the OpenAI SDK pointed at OpenRouter.

Routes to the legacy `/completions` endpoint for completion-style models
(e.g. `gpt-3.5-turbo-instruct`) and `/chat/completions` for everything else.
This matters because completion-style models are trained on raw text, not
chat-templated turns — wrapping them in a chat template muddies the prompt.
"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MODEL_ID = os.environ.get("MODEL_ID", "mistralai/mistral-7b-instruct-v0.1")

# Models that route to the legacy /completions endpoint.
COMPLETION_MODELS = {
    "openai/gpt-3.5-turbo-instruct",
}


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


def complete(
    prompt: str,
    *,
    temperature: float = 0.0,
    max_tokens: int = 512,
    model: str | None = None,
) -> str:
    model = model or MODEL_ID
    client = get_client()
    if model in COMPLETION_MODELS:
        resp = client.completions.create(
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].text or ""
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""
