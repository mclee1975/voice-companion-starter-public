# Project purpose and compatibility

## Goal

Voice Companion Starter exists to make a **private browser voice interface** practical for people who already operate an AI agent, speech-to-text (STT), and text-to-speech (TTS) services.

The project supplies the deliberately small layer between those components: a mobile-friendly browser UI, server-side STT → agent → TTS routing, spoken replies, a transcript, and a loopback-only default. It avoids the false choice between building a full hosted product and exposing private credentials or conversations through an unrelated control plane.

This is a starter project, not a hosted service, agent framework, model provider, identity provider, or remote-control system. Users retain control of their model, speech stack, authentication, and deployment design.

## Compatibility baseline

| Layer | Supported baseline |
|---|---|
| Application runtime | Python 3.11 or newer |
| Operating systems | Current Linux, macOS, or Windows environments capable of running Python 3.11+ |
| Container option | Docker and Docker Compose (optional) |
| Automated validation | GitHub Actions on Ubuntu 24.04 with Python 3.11 |
| Agent integration | Any OpenAI-compatible Chat Completions endpoint |
| Speech integration | Private HTTP STT/TTS services using the documented adapters |

## Hermes and other agent frameworks

Hermes is optional. This project has no privileged Hermes integration and no Hermes version dependency. If an existing Hermes deployment exposes an OpenAI-compatible chat-completions endpoint, configure it as the agent upstream just as you would any compatible agent framework or model server.

## Security intent

The browser never receives agent or speech-service credentials. The starter binds to loopback by default, keeps credentials server-side, does not persist transcripts or audio, and is not intended to be exposed publicly without proper HTTPS, identity-aware access control, rate limiting, and monitoring.
