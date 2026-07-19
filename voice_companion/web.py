"""FastAPI application factory and browser routes."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Header, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from .config import MAX_TEXT, Settings, require_auth
from .services import chat, synthesize, transcribe

STATIC = Path(__file__).parent.parent / "static"


class ChatRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_TEXT)


class SynthesisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_TEXT)


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
        require_auth(settings, authorization)
        return FileResponse(STATIC / "index.html", media_type="text/html", headers={"Cache-Control": "no-store"})

    @app.get("/app.js")
    async def js(authorization: str | None = Header(default=None)) -> FileResponse:
        require_auth(settings, authorization)
        return FileResponse(STATIC / "app.js", media_type="text/javascript", headers={"Cache-Control": "no-store"})

    @app.get("/styles.css")
    async def css(authorization: str | None = Header(default=None)) -> FileResponse:
        require_auth(settings, authorization)
        return FileResponse(STATIC / "styles.css", media_type="text/css", headers={"Cache-Control": "no-store"})

    @app.get("/api/config")
    async def config(authorization: str | None = Header(default=None)) -> dict[str, str]:
        require_auth(settings, authorization)
        return {"app_name": settings.app_name, "greeting": settings.greeting, "voice_name": settings.voice_name}

    @app.post("/api/chat")
    async def chat_route(payload: ChatRequest, authorization: str | None = Header(default=None)) -> dict[str, str]:
        require_auth(settings, authorization)
        return {"text": await chat(settings, payload.text)}

    @app.post("/api/transcribe")
    async def transcribe_route(request: Request, authorization: str | None = Header(default=None)) -> dict[str, str]:
        require_auth(settings, authorization)
        return {"text": await transcribe(settings, await request.body(), request.headers.get("content-type", "audio/webm"))}

    @app.post("/api/synthesize")
    async def synthesize_route(payload: SynthesisRequest, authorization: str | None = Header(default=None)) -> Response:
        require_auth(settings, authorization)
        audio, content_type = await synthesize(settings, payload.text)
        return Response(audio, media_type=content_type, headers={"Cache-Control": "no-store"})

    return app
