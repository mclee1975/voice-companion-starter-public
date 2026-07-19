"""Generic self-hosted voice companion bridge.

The browser is untrusted: it never receives agent or speech-service credentials.
Run loopback-only by default. Set VOICE_COMPANION_TOKEN before binding beyond localhost.
"""
from __future__ import annotations

import os

import httpx  # Re-exported for simple test-time upstream mocking.

from voice_companion.config import MAX_AUDIO_BYTES, MAX_TEXT, Settings, validate_bind_host
from voice_companion.services import chat as _chat
from voice_companion.services import synthesize as _synthesize
from voice_companion.services import transcribe as _transcribe
from voice_companion.web import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("VOICE_COMPANION_HOST", "127.0.0.1")
    validate_bind_host(host)
    uvicorn.run(app, host=host, port=int(os.getenv("VOICE_COMPANION_PORT", "8787")))
