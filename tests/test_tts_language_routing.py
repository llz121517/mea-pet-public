"""按回复段语言路由 TTS 与固定参考音频。"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class TestReferenceAudioConfig(unittest.TestCase):
    def test_normalizes_language_map_and_migrates_legacy_single_reference(self):
        from meapet.config.store import normalize_config

        config = normalize_config(
            {
                "tts": {
                    "gsv_ref_wav": " ./legacy-ja.wav ",
                    "gsv_ref_lang": "日语",
                    "reference_audios": {
                        "zh-CN": {"path": " ./refs/zh.wav ", "text": "你好"},
                        "en": " ./refs/en.wav ",
                    },
                }
            }
        )

        refs = config["tts"]["reference_audios"]
        self.assertEqual(refs["zh"], {"path": "./refs/zh.wav", "text": "你好"})
        self.assertEqual(refs["en"], {"path": "./refs/en.wav", "text": ""})
        self.assertEqual(
            refs["jp"],
            {"path": "./legacy-ja.wav", "text": ""},
        )


class TestGsvReferenceRouting(unittest.TestCase):
    def test_explicit_segment_language_selects_its_fixed_reference(self):
        from meapet.tts.engines.gsv import TtsGsvMixin

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            zh = root / "zh.wav"
            jp = root / "jp.wav"
            zh.write_bytes(b"RIFF" + b"\x00" * 64)
            jp.write_bytes(b"RIFF" + b"\x00" * 64)

            class Host(TtsGsvMixin):
                ref_dir = str(root / "automatic")
                voice_lang = "jp"
                gsv_ref_wav = ""
                gsv_ref_lang = "jp"
                reference_audios = {
                    "zh": {"path": str(zh), "text": "中文参考"},
                    "jp": {"path": str(jp), "text": "日本語の参照"},
                }

            host = Host()
            zh_result = host._get_ref_paths("neutral", voice_language="zh-CN")
            jp_result = host._get_ref_paths("neutral", voice_language="ja")

        self.assertEqual(zh_result, (str(zh), "中文参考", "中文"))
        self.assertEqual(jp_result, (str(jp), "日本語の参照", "日文"))


class TestTtsWorkerLanguage(unittest.TestCase):
    def test_worker_forwards_segment_language_without_mutating_global_language(self):
        from meapet.desktop.workers import TTSWorker

        captured = {}

        class TTS:
            voice_lang = "jp"

            async def speak_async(
                self,
                text,
                mood="neutral",
                style="",
                language="",
            ):
                captured.update(
                    text=text,
                    mood=mood,
                    style=style,
                    language=language,
                    global_language=self.voice_lang,
                )
                return ("/tmp/language.wav", "zh")

        worker = TTSWorker(
            TTS(),
            "你好",
            mood="happy",
            style="轻声",
            language="zh-CN",
        )
        result = asyncio.run(worker._run())

        self.assertEqual(result, "/tmp/language.wav|zh")
        self.assertEqual(captured["language"], "zh-CN")
        self.assertEqual(captured["global_language"], "jp")


class TestMeaTtsLanguageOverride(unittest.TestCase):
    def test_mimo_async_uses_per_call_language_instead_of_configured_default(self):
        from meapet.tts.service import MeaTTS

        with tempfile.TemporaryDirectory() as td:
            with mock.patch.dict(
                os.environ,
                {
                    "MIMO_API_KEY": "",
                    "XIAOMIMIMO_API_KEY": "",
                    "MEAPET_API_KEY": "",
                },
                clear=False,
            ):
                tts = MeaTTS(
                    {
                        "tts": {
                            "enabled": True,
                            "engine": "mimo",
                            "api_key": "test-key-not-real",
                            "voice_lang": "jp",
                            "translate_to_jp": True,
                            "output_dir": td,
                        }
                    }
                )

            with mock.patch.object(
                tts,
                "_speak_mimo_async",
                new_callable=mock.AsyncMock,
                return_value=(str(Path(td) / "zh.wav"), "zh"),
            ) as speak:
                result = asyncio.run(
                    tts.speak_async("你好", language="zh-CN")
                )

        self.assertEqual(result[1], "zh")
        self.assertEqual(speak.await_args.kwargs["lang_tag"], "zh")
        self.assertEqual(speak.await_args.kwargs["voice_language"], "zh")


if __name__ == "__main__":
    unittest.main()
