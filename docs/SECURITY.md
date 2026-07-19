# Security and privacy

## Default posture

Voice Companion Starter is intentionally conservative:

- binds to `127.0.0.1` by default;
- refuses a non-loopback bind unless `VOICE_COMPANION_TOKEN` is configured;
- keeps agent and speech-service credentials server-side;
- serves no generated API documentation endpoints;
- sends `Cache-Control: no-store` for the private UI, configuration, and speech response;
- limits typed input to 12,000 characters and audio uploads to 12 MiB;
- returns generic upstream errors.

## Threat model

The browser is treated as an untrusted client. It can submit text and audio, but it cannot choose a system prompt, agent tools, upstream URL, model API key, STT key, or TTS key.

This is a starter, not a complete public-internet security product. If you expose it beyond localhost, provide all of the following yourself:

1. HTTPS termination.
2. Identity-aware authentication or a private VPN/reverse proxy.
3. Rate limiting and request-size controls at the edge.
4. Operational logging and alerting appropriate to your environment.
5. A secret-management process for `.env` values.

## Deployment rules

- Never commit `.env`.
- Do not put credentials in browser JavaScript, HTML, URLs, or container images.
- Do not expose the starter directly to the public internet with only the bearer token.
- Keep agent, STT, and TTS upstreams private or independently authenticated.
- Rotate a token immediately if it is copied into a terminal history, screenshot, issue, or repository.

## Reporting a vulnerability

Please do not open a public issue with exploit details or secrets. Use the repository owner’s private GitHub contact route instead. Include a minimal reproduction, impact, and affected version/commit where possible.
