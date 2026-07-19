"""Configuration and security primitives for the voice companion."""
from __future__ import annotations

import hmac
import os

from fastapi import HTTPException
from pydantic import BaseModel, Field

MAX_TEXT = 12_000
MAX_AUDIO_BYTES = 12 * 1024 * 1024


class Settings(BaseModel):
    app_name: str = Field(default="Voice Companion")
    greeting: str = Field(default="Hello")
    agent_api_url: str = Field(default="http://127.0.0.1:8080/v1/chat/completions")
    agent_api_key: str = Field(default="")
    agent_model: str = Field(default="your-agent-model")
    agent_system_prompt: str = Field(default="You are a helpful, concise voice companion.")
    stt_api_url: str = Field(default="http://127.0.0.1:9000/v1/transcribe")
    tts_api_url: str = Field(default="http://127.0.0.1:9001/v1/synthesize")
    voice_name: str = Field(default="default")
    voice_speed: float = Field(default=1.0, ge=0.5, le=2.0)
    access_token: str = Field(default="")

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("APP_NAME", "Voice Companion"),
            greeting=os.getenv("GREETING", "Hello"),
            agent_api_url=os.getenv("AGENT_API_URL", "http://127.0.0.1:8080/v1/chat/completions"),
            agent_api_key=os.getenv("AGENT_API_KEY", ""),
            agent_model=os.getenv("AGENT_MODEL", "your-agent-model"),
            agent_system_prompt=os.getenv("AGENT_SYSTEM_PROMPT", "You are a helpful, concise voice companion."),
            stt_api_url=os.getenv("STT_API_URL", "http://127.0.0.1:9000/v1/transcribe"),
            tts_api_url=os.getenv("TTS_API_URL", "http://127.0.0.1:9001/v1/synthesize"),
            voice_name=os.getenv("VOICE_NAME", "default"),
            voice_speed=float(os.getenv("VOICE_SPEED", "1.0")),
            access_token=os.getenv("VOICE_COMPANION_TOKEN", ""),
        )


def require_auth(settings: Settings, authorization: str | None) -> None:
    if not settings.access_token:
        return
    candidate = authorization.removeprefix("Bearer ") if authorization else ""
    if not hmac.compare_digest(candidate, settings.access_token):
        raise HTTPException(status_code=401, detail="Authentication required")


def validate_bind_host(host: str) -> None:
    if host not in {"127.0.0.1", "::1", "localhost"} and not Settings.from_env().access_token:
        raise SystemExit("Refusing non-loopback binding without VOICE_COMPANION_TOKEN. Configure a token first.")
