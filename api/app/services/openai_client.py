"""Optional OpenAI helpers (research ranker / future intelligence)."""
from __future__ import annotations

from app.config import get_settings

_client = None


def get_client():
    global _client
    if _client is None:
        from openai import AsyncOpenAI

        _client = AsyncOpenAI(api_key=get_settings().openai_api_key)
    return _client


async def chat_completion(
    system: str,
    user: str,
    model: str | None = None,
    response_format: dict | None = None,
) -> str:
    return await chat_messages(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        model=model,
        response_format=response_format,
    )


async def chat_messages(
    messages: list[dict[str, str]],
    model: str | None = None,
    response_format: dict | None = None,
    temperature: float = 0.2,
) -> str:
    client = get_client()
    kwargs: dict = {
        "model": model or "gpt-4o-mini",
        "messages": messages,
        "temperature": temperature,
    }
    if response_format:
        kwargs["response_format"] = response_format
    response = await client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""
