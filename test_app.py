import asyncio
import unittest
from unittest.mock import patch

import httpx

import app


class FakeResponse:
    def __init__(self, data, content=b"", content_type="application/json"):
        self._data = data
        self.content = content
        self.headers = {"content-type": content_type}

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


class FakeClient:
    payload = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, **kwargs):
        FakeClient.payload = {"url": url, **kwargs}
        return FakeResponse({"choices": [{"message": {"content": "A concise reply."}}]})


class VoiceCompanionTests(unittest.IsolatedAsyncioTestCase):
    def settings(self, **overrides):
        return app.Settings(access_token="test-token", **overrides)

    async def client(self, settings=None):
        return httpx.AsyncClient(transport=httpx.ASGITransport(app=app.create_app(settings or self.settings())), base_url="http://test")

    async def test_ui_requires_configured_bearer_token(self):
        async with await self.client() as client:
            denied = await client.get("/")
            allowed = await client.get("/", headers={"Authorization": "Bearer test-token"})
        self.assertEqual(denied.status_code, 401)
        self.assertEqual(allowed.status_code, 200)
        self.assertIn("Voice Companion", allowed.text)
        self.assertIn("SELF-HOSTED VOICE COMPANION", allowed.text)

    async def test_config_exposes_no_secret(self):
        settings = self.settings(agent_api_key="never-send-me", greeting="Welcome")
        async with await self.client(settings) as client:
            response = await client.get("/api/config", headers={"Authorization": "Bearer test-token"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"app_name": "Voice Companion", "greeting": "Welcome", "voice_name": "default"})
        self.assertNotIn("never-send-me", response.text)

    async def test_chat_uses_server_owned_system_prompt(self):
        settings = self.settings(agent_system_prompt="Server-owned policy")
        with patch.object(app.httpx, "AsyncClient", FakeClient):
            reply = await app._chat(settings, "Hello")
        self.assertEqual(reply, "A concise reply.")
        messages = FakeClient.payload["json"]["messages"]
        self.assertEqual(messages, [{"role": "system", "content": "Server-owned policy"}, {"role": "user", "content": "Hello"}])
        self.assertEqual(FakeClient.payload["headers"], {})

    def test_non_loopback_requires_token(self):
        with patch.dict("os.environ", {"VOICE_COMPANION_TOKEN": ""}, clear=False):
            with self.assertRaises(SystemExit):
                app.validate_bind_host("0.0.0.0")

    async def test_audio_size_is_bounded(self):
        settings = self.settings()
        async with await self.client(settings) as client:
            response = await client.post("/api/transcribe", content=b"x" * (app.MAX_AUDIO_BYTES + 1), headers={"Authorization": "Bearer test-token", "Content-Type": "audio/webm"})
        self.assertEqual(response.status_code, 413)


if __name__ == "__main__":
    unittest.main()
