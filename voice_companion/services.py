"""Bounded upstream calls with opaque client-facing errors."""
from __future__ import annotations

import httpx
from fastapi import HTTPException

from .config import MAX_AUDIO_BYTES, Settings

TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def _upstream_error() -> HTTPException:
    return HTTPException(status_code=502, detail="The configured upstream service did not complete the request.")


async def chat(settings: Settings, text: str) -> str:
    payload = {"model": settings.agent_model, "messages": [
        {"role": "system", "content": settings.agent_system_prompt},
        {"role": "user", "content": text},
    ], "stream": False}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            result = await client.post(settings.agent_api_url, json=payload, headers=_headers(settings.agent_api_key))
            result.raise_for_status()
            reply = result.json()["choices"][0]["message"]["content"]
        if not isinstance(reply, str) or not reply.strip():
            raise ValueError("empty agent reply")
        return reply.strip()
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        raise _upstream_error() from None


async def transcribe(settings: Settings, audio: bytes, content_type: str) -> str:
    if not audio or len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio must be between 1 byte and 12 MB.")
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            result = await client.post(settings.stt_api_url, content=audio, headers={"Content-Type": content_type})
            result.raise_for_status()
            text = result.json().get("text", "")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("empty transcription")
        return text.strip()
    except (httpx.HTTPError, ValueError, TypeError):
        raise _upstream_error() from None


async def synthesize(settings: Settings, text: str) -> tuple[bytes, str]:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            result = await client.post(settings.tts_api_url, json={"text": text, "voice": settings.voice_name, "speed": settings.voice_speed})
            result.raise_for_status()
        return result.content, result.headers.get("content-type", "audio/wav")
    except httpx.HTTPError:
        raise _upstream_error() from None
