# Voice Companion Starter

A **private, self-hosted browser voice companion** you can run beside an existing AI agent, speech-to-text (STT), and text-to-speech (TTS) service.

It gives you a small mobile-friendly web page with:

- typed chat;
- hold-to-talk recording in the browser;
- server-side STT → agent → TTS routing;
- spoken replies and a visible transcript;
- a loopback-only security default.

This project deliberately does **not** include a hosted model, a voice model, a cloud account, personal data, a contact book, or any remote-control tools. You bring your own private components.

## What you need first

| Component | What it must provide |
|---|---|
| Python | Python 3.11 or newer |
| Agent | OpenAI-compatible `POST /v1/chat/completions` endpoint |
| STT service | Private HTTP endpoint that accepts raw browser audio and returns `{"text":"..."}` |
| TTS service | Private HTTP endpoint that accepts `{"text","voice","speed"}` and returns audio bytes |

> **Privacy rule:** Keep all three upstream services on your machine or private network. Never put an API key in browser JavaScript.

## Quick start (beginner-friendly)

### 1. Download the project

```bash
git clone https://github.com/mclee1975/voice-companion-starter-public.git
cd voice-companion-starter-public
```

### 2. Create a Python environment

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

### 3. Create your private configuration

```bash
cp .env.example .env
chmod 600 .env
```

Open `.env` in a text editor. Set **at minimum** these values to the endpoints you already operate:

```dotenv
AGENT_API_URL=http://YOUR-AGENT:PORT/v1/chat/completions
AGENT_MODEL=YOUR-MODEL-NAME
STT_API_URL=http://YOUR-STT:PORT/v1/transcribe
TTS_API_URL=http://YOUR-TTS:PORT/v1/synthesize
VOICE_NAME=YOUR-VOICE-NAME
```

If your agent requires a key, put it in `AGENT_API_KEY` in `.env`. Do **not** share or commit that file.

### 4. Start the companion

```bash
set -a; . ./.env; set +a
python app.py
```

Open <http://127.0.0.1:8787> in the same machine’s browser. Tap **Hold to talk**, approve microphone access, speak, then release.

## Docker option

If Docker is installed, after configuring `.env`:

```bash
docker compose up --build
```

The supplied Compose file publishes only `127.0.0.1:8787`, not the public internet.

## Security before remote access

The starter intentionally binds to `127.0.0.1`. If you want another device to reach it, put a **trusted authenticated reverse proxy** in front of it (for example, a private VPN proxy).

If you deliberately bind it beyond localhost, you must first set a long random token:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Put the result in `VOICE_COMPANION_TOKEN`. Requests must then include `Authorization: Bearer YOUR_TOKEN`. This is a minimum guard, not a replacement for private networking and HTTPS.

## Configure your STT and TTS adapters

The starter uses intentionally tiny HTTP contracts so you can adapt it to any speech stack:

### STT request/response

```http
POST /v1/transcribe
Content-Type: audio/webm

(binary browser audio)
```

```json
{"text":"What is the weather today?"}
```

### TTS request/response

```json
POST /v1/synthesize
{"text":"Hello", "voice":"default", "speed":1.0}
```

Return an audio response, such as `audio/wav`, `audio/mpeg`, or `audio/ogg`.

If your providers use another shape, adjust only `_transcribe()` or `_synthesize()` in `app.py`; agent credentials and speech-service credentials remain server-side either way.

## Development checks

```bash
python -m unittest -v
python -m compileall -q app.py
```

## Project boundaries

- The browser never receives `AGENT_API_KEY` or your speech-service credentials.
- Caller-provided system prompts and tools are never forwarded; the server owns the fixed system prompt.
- Requests are size-limited and upstream failures return generic errors.
- The server does not persist transcripts or audio files.
- This starter is not an authentication system or a public SaaS product. Keep it private unless you add proper HTTPS, identity-aware access control, rate limiting, and monitoring.

## Repository guide

| Path | Purpose |
|---|---|
| `app.py` | FastAPI bridge and server-side trust boundary |
| `static/` | Dependency-free browser UI |
| `.env.example` | Complete operator configuration reference |
| `compose.yaml` / `Dockerfile` | Loopback-first container option |
| `test_app.py` | Boundary and configuration regression tests |
| `docs/` | Architecture, API, and security references |

## Documentation

- [Project purpose and compatibility](PROJECT_PURPOSE.md)
- [Architecture and data flow](docs/ARCHITECTURE.md)
- [API reference](docs/API.md)
- [Security and privacy](docs/SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## Troubleshooting

| Symptom | First check |
|---|---|
| Browser cannot connect | Confirm the process is running and open `http://127.0.0.1:8787/health` on the host. |
| `502` response | Verify the configured agent, STT, or TTS endpoint is reachable from the bridge host and returns the documented response shape. |
| Microphone never starts | Use a secure browser context where required and grant microphone permission. |
| Non-local bind is refused | Set a long random `VOICE_COMPANION_TOKEN` before changing `VOICE_COMPANION_HOST`; use a trusted authenticated reverse proxy as well. |
| Audio does not play | Check that TTS returns a browser-playable audio content type and that the browser allows playback after user interaction. |

## Support and maintenance

Use GitHub Issues for reproducible bugs and feature requests. Keep reports free of credentials, private endpoints, recordings, and personal data. See [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## License

MIT. See [LICENSE](LICENSE).
