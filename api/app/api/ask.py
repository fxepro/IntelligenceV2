"""Ask — platform-context AI chat (control plane; short LLM round-trip)."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.services.ask_context import SYSTEM_PROMPT, build_platform_facts, local_reply

router = APIRouter()


class AskMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=8000)


class AskRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[AskMessage] = Field(default_factory=list, max_length=20)


class AskResponse(BaseModel):
    reply: str
    mode: str  # openai | local | rate_limited
    context_chars: int


def _is_rate_limit(exc: BaseException) -> bool:
    name = type(exc).__name__
    text = str(exc).lower()
    return name == "RateLimitError" or "rate limit" in text or "429" in text


@router.post("", response_model=AskResponse)
async def ask(payload: AskRequest, db: AsyncSession = Depends(get_db)):
    facts = await build_platform_facts(db)
    context = facts.as_context()
    settings = get_settings()
    question = payload.message.strip()

    if not settings.openai_api_key:
        reply = local_reply(
            question,
            facts,
            reason="OpenAI key is not configured — answering from local platform facts.",
        )
        return AskResponse(reply=reply, mode="local", context_chars=len(context))

    from app.services.openai_client import chat_messages

    messages: list[dict[str, str]] = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\n{context}"},
    ]
    # Keep history short to reduce token burn / rate-limit pressure.
    for turn in payload.history[-6:]:
        messages.append({"role": turn.role, "content": turn.content.strip()[:1500]})
    messages.append({"role": "user", "content": question})

    last_exc: BaseException | None = None
    for attempt in range(2):
        try:
            reply = await chat_messages(messages, temperature=0.2)
            return AskResponse(
                reply=(reply or "").strip() or "No reply.",
                mode="openai",
                context_chars=len(context),
            )
        except Exception as exc:
            last_exc = exc
            if _is_rate_limit(exc) and attempt == 0:
                await asyncio.sleep(1.5)
                continue
            break

    assert last_exc is not None
    if _is_rate_limit(last_exc):
        reason = (
            "OpenAI rate limit hit — answered from local platform facts. "
            "Wait a minute and try again for full model answers."
        )
        mode = "rate_limited"
    else:
        reason = (
            f"Model unavailable ({type(last_exc).__name__}) — "
            "answered from local platform facts."
        )
        mode = "local"

    reply = local_reply(question, facts, reason=reason)
    return AskResponse(reply=reply, mode=mode, context_chars=len(context))
