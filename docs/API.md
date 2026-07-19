# API reference

All routes are served by the FastAPI bridge. By default it listens on `127.0.0.1:8787`.

If `VOICE_COMPANION_TOKEN` is set, every route except `/health` requires:

```http
Authorization: Bearer <token>
```

## `GET /health`

Returns process health only. It does not probe upstream services.

```json
{"status":"ok"}
```

## `GET /api/config`

Returns browser-safe display configuration. It never returns endpoint URLs, tokens, or API keys.

```json
{"app_name":"Voice Companion","greeting":"Hello","voice_name":"default"}
```

## `POST /api/chat`

```json
{"text":"Hello"}
```

`text` must be non-empty and no longer than 12,000 characters.

```json
{"text":"Hello. How can I help?"}
```

The configured agent must implement an OpenAI-compatible non-streaming chat-completions endpoint. The bridge sends a model name, one server-owned system message, one user message, and `stream: false`.

## `POST /api/transcribe`

Send raw browser audio. The bridge forwards the supplied content type to the STT service.

```http
Content-Type: audio/webm

<binary audio>
```

The maximum body size is 12 MiB. The configured STT service must return:

```json
{"text":"transcribed words"}
```

## `POST /api/synthesize`

```json
{"text":"Hello"}
```

The bridge adds the configured `voice` and `speed` when calling the TTS service:

```json
{"text":"Hello","voice":"default","speed":1.0}
```

The TTS service may return `audio/wav`, `audio/mpeg`, `audio/ogg`, or another browser-playable audio content type.

## Error contract

Input validation returns normal HTTP validation errors. Upstream connection, protocol, and response failures are deliberately returned as:

```json
{"detail":"The configured upstream service did not complete the request."}
```

This avoids leaking upstream URLs, stack traces, credentials, or provider response bodies to the browser.
