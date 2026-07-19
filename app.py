"""Generic self-hosted voice companion bridge.

The browser is untrusted: it never receives agent or speech-service credentials.
Run loopback-only by default. Set VOICE_COMPANION_TOKEN before binding beyond localhost.
"""
from __future__ import annotations

import asyncio
import hmac
import os
from pathlib import Path

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field

ROOT = Path(__file__).parent
STATIC = ROOT / "static"
MAX_TEXT = 12_000
MAX_AUDIO_BYTES = 12 * 1024 * 1024
TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)


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
        values = {
            "app_name": os.getenv("APP_NAME", "Voice Companion"),
            "greeting": os.getenv("GREETING", "Hello"),
            "agent_api_url": os.getenv("AGENT_API_URL", "http://127.0.0.1:8080/v1/chat/completions"),
            "agent_api_key": os.getenv("AGENT_API_KEY", ""),
            "agent_model": os.getenv("AGENT_MODEL", "your-agent-model"),
            "agent_system_prompt": os.getenv("AGENT_SYSTEM_PROMPT", "You are a helpful, concise voice companion."),
            "stt_api_url": os.getenv("STT_API_URL", "http://127.0.0.1:9000/v1/transcribe"),
            "tts_api_url": os.getenv("TTS_API_URL", "http://127.0.0.1:9001/v1/synthesize"),
            "voice_name": os.getenv("VOICE_NAME", "default"),
            "voice_speed": float(os.getenv("VOICE_SPEED", "1.0")),
            "access_token": os.getenv("VOICE_COMPANION_TOKEN", ""),
        }
        return cls(**values)


class ChatRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_TEXT)


class SynthesisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_TEXT)


def _auth(settings: Settings, authorization: str | None) -> None:
    """Require a bearer token only when the operator configured one."""
    if not settings.access_token:
        return
    candidate = authorization.removeprefix("Bearer ") if authorization else ""
    if not hmac.compare_digest(candidate, settings.access_token):
        raise HTTPException(status_code=401, detail="Authentication required")


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def _upstream_error() -> HTTPException:
    return HTTPException(status_code=502, detail="The configured upstream service did not complete the request.")


async def _chat(settings: Settings, text: str) -> str:
    payload = {
        "model": settings.agent_model,
        "messages": [
            {"role": "system", "content": settings.agent_system_prompt},
            {"role": "user", "content": text},
        ],
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            result = await client.post(settings.agent_api_url, json=payload, headers=_headers(settings.agent_api_key))
            result.raise_for_status()
            data = result.json()
        reply = data["choices"][0]["message"]["content"]
        if not isinstance(reply, str) or not reply.strip():
            raise ValueError("empty agent reply")
        return reply.strip()
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        raise _upstream_error() from None


async def _transcribe(settings: Settings, audio: bytes, content_type: str) -> str:
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


async def _synthesize(settings: Settings, text: str) -> tuple[bytes, str]:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            result = await client.post(settings.tts_api_url, json={"text": text, "voice": settings.voice_name, "speed": settings.voice_speed})
            result.raise_for_status()
        return result.content, result.headers.get("content-type", "audio/wav")
    except httpx.HTTPError:
        raise _upstream_error() from None


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title=settings.app_name, docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def bounded_request_log(request: Request, call_next):
        response = await call_next(request)
        print(f"voice_companion method={request.method} path={request.url.path} status={response.status_code}", flush=True)
        return response

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    async def ui(authorization: str | None = Header(default=None)) -> FileResponse:
        _auth(settings, authorization)
        return FileResponse(STATIC / "index.html", media_type="text/html", headers={"Cache-Control": "no-store"})

    @app.get("/app.js")
    async def js(authorization: str | None = Header(default=None)) -> FileResponse:
        _auth(settings, authorization)
        return FileResponse(STATIC / "app.js", media_type="text/javascript", headers={"Cache-Control": "no-store"})

    @app.get("/styles.css")
    async def css(authorization: str | None = Header(default=None)) -> FileResponse:
        _auth(settings, authorization)
        return FileResponse(STATIC / "styles.css", media_type="text/css", headers={"Cache-Control": "no-store"})

    @app.get("/api/config")
    async def config(authorization: str | None = Header(default=None)) -> dict[str, str]:
        _auth(settings, authorization)
        return {"app_name": settings.app_name, "greeting": settings.greeting, "voice_name": settings.voice_name}

    @app.post("/api/chat")
    async def chat(payload: ChatRequest, authorization: str | None = Header(default=None)) -> dict[str, str]:
        _auth(settings, authorization)
        return {"text": await _chat(settings, payload.text)}

    @app.post("/api/transcribe")
    async def transcribe(request: Request, authorization: str | None = Header(default=None)) -> dict[str, str]:
        _auth(settings, authorization)
        return {"text": await _transcribe(settings, await request.body(), request.headers.get("content-type", "audio/webm"))}

    @app.post("/api/synthesize")
    async def synthesize(payload: SynthesisRequest, authorization: str | None = Header(default=None)) -> Response:
        _auth(settings, authorization)
        audio, content_type = await _synthesize(settings, payload.text)
        return Response(audio, media_type=content_type, headers={"Cache-Control": "no-store"})

    return app


app = create_app()


def validate_bind_host(host: str) -> None:
    if host not in {"127.0.0.1", "::1", "localhost"} and not Settings.from_env().access_token:
        raise SystemExit("Refusing non-loopback binding without VOICE_COMPANION_TOKEN. Configure a token first.")


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("VOICE_COMPANION_HOST", "127.0.0.1")
    validate_bind_host(host)
    uvicorn.run(app, host=host, port=int(os.getenv("VOICE_COMPANION_PORT", "8787")))
