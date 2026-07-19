# Architecture

Voice Companion Starter is a deliberately small **browser-to-private-services bridge**. It is not a hosted AI service and does not bundle a model, speech engine, identity provider, or cloud account.

```text
Browser
  │ typed text or recorded microphone audio
  ▼
Voice Companion Starter (FastAPI)
  ├── POST /api/transcribe ──► private STT endpoint
  ├── POST /api/chat ────────► OpenAI-compatible agent endpoint
  └── POST /api/synthesize ─► private TTS endpoint
  │
  ▼
Browser transcript + locally played audio
```

## Components

| Component | Responsibility | Trust boundary |
|---|---|---|
| Browser UI | Records audio, displays transcript, plays returned audio | Untrusted client |
| FastAPI bridge | Validates input, owns credentials and system prompt, calls upstreams | Trusted server |
| Agent endpoint | Produces text replies through OpenAI-compatible chat completions | Private upstream |
| STT endpoint | Turns browser audio into text | Private upstream |
| TTS endpoint | Turns reply text into audio bytes | Private upstream |

## Request flows

### Typed chat

1. The browser sends `{ "text": "..." }` to `POST /api/chat`.
2. The bridge prepends the server-owned system prompt and sends the request to the configured agent.
3. The bridge returns `{ "text": "..." }` to the browser.
4. The browser displays the text and asks `POST /api/synthesize` for speech.

### Hold-to-talk

1. The browser records microphone audio only while the button is held.
2. On release, it sends raw audio to `POST /api/transcribe`.
3. The browser submits the resulting text through the normal chat flow.
4. The reply follows the same visible-text and optional-speech path.

## Deliberate boundaries

- The browser never receives upstream API keys.
- The bridge accepts only user text for chat; it does not forward browser-supplied system prompts, tools, or arbitrary message history.
- The starter does not persist transcripts, microphone recordings, or synthesized audio.
- The default listener is loopback-only. Reaching it from another device is an operator responsibility, not an implied feature.

See [API.md](API.md) for request and response contracts and [SECURITY.md](SECURITY.md) for the threat model.
