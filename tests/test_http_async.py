"""httpx 真异步 HTTP 层"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class TestHttpAsyncPost(unittest.TestCase):
    def test_post_json_uses_httpx_client(self):
        import httpx
        from meapet.async_runtime import run
        from meapet import http_async

        class FakeResp:
            status_code = 200
            text = '{"ok":true}'
            def json(self):
                return {"ok": True}

        class FakeClient:
            is_closed = False
            def __init__(self):
                self.calls = []
            async def post(self, url, **kwargs):
                self.calls.append((url, kwargs))
                return FakeResp()
            async def aclose(self):
                self.is_closed = True

        fake = FakeClient()

        async def _fake_get_client():
            return fake

        async def _scenario():
            with mock.patch.object(http_async, "get_client", _fake_get_client):
                resp = await http_async.post_json(
                    "https://example.com/v1/chat",
                    headers={"Authorization": "Bearer x"},
                    json={"a": 1},
                    timeout=5,
                )
            return resp.status_code, fake.calls

        code, calls = run(_scenario(), timeout=5)
        self.assertEqual(code, 200)
        self.assertEqual(len(calls), 1)
        self.assertIn("example.com", calls[0][0])

    def test_chat_async_backend_uses_http_async(self):
        from meapet.async_runtime import run
        from meapet.chat.engine import ChatEngine

        eng = ChatEngine(backend="deepseek", api_key="k", api_base="https://api.example.com", model="m")
        eng.available = True

        class Resp:
            status_code = 200
            text = "ok"
            def json(self):
                return {"choices": [{"message": {"content": "[happy]httpx喵"}}]}

        async def fake_post(url, headers=None, json_body=None, timeout=30):
            return Resp()

        with mock.patch.object(eng, "_post_json", side_effect=fake_post):
            reply, mood = run(eng.quick_chat_async("hi"), timeout=5)
        self.assertEqual(mood, "happy")
        self.assertEqual(reply, "httpx喵")

    def test_chat_backends_reserve_tokens_for_tts_metadata_line(self):
        import asyncio

        from meapet.chat.engine import ChatEngine

        captured = {}

        class DeepSeekResp:
            status_code = 200
            text = "ok"

            @staticmethod
            def json():
                return {"choices": [{"message": {"content": "两行加元数据"}}]}

        class OllamaResp:
            status_code = 200
            text = "ok"

            @staticmethod
            def json():
                return {"message": {"content": "两行加元数据"}}

        async def fake_post(_url, *, json_body=None, **_kwargs):
            if "options" in json_body:
                captured["ollama"] = json_body["options"]["num_predict"]
                return OllamaResp()
            captured["deepseek"] = json_body["max_tokens"]
            return DeepSeekResp()

        deepseek = ChatEngine(
            backend="deepseek",
            api_key="k",
            api_base="https://api.example.com",
            model="m",
        )
        ollama = ChatEngine.__new__(ChatEngine)
        ollama.host = "http://127.0.0.1:11434"
        ollama.model = "local-model"
        ollama.temperature = 0.7
        deepseek._post_json = fake_post
        ollama._post_json = fake_post

        asyncio.run(deepseek._chat_deepseek_async([]))
        asyncio.run(ollama._chat_ollama_async([]))

        self.assertGreaterEqual(captured["deepseek"], 320)
        self.assertGreaterEqual(captured["ollama"], 320)


if __name__ == "__main__":
    unittest.main()
