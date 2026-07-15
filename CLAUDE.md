# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests
python -m pytest -q

# Run specific test files
python -m pytest tests/test_ui_refactor.py tests/test_live2d_startup.py -q

# Lint (ruff: only E9/F63/F7/F82)
python -m ruff check meapet wizard scripts tests

# Syntax check
python -m compileall -q meapet wizard

# Launch desktop pet
python pet.py  # or: python -m meapet

# Launch config wizard
python setup_wizard.py
```

Ruff excludes: `GPT-Sovits`, `live2d`, `models`, `vits_core`, `vits_models`. Python 3.10–3.12 (.python-version = 3.12). VITS optional-deps requires `numpy<2`, `setuptools==69.5.1`.

## Architecture

**Entry points:** `pet.py` / `meapet/__main__.py` → `meapet.desktop.app:main`. Config wizard at `wizard/app.py`.

**Main window** (`meapet/desktop/app.py`): 8-mixin MRO over `QWidget`. Resolution order: `PetAudioMixin → PetWatcherMixin → PetChatFlowMixin → PetControlBridgeMixin → PetInteractionMixin → PetWindowChromeMixin → PetRenderHostMixin → PetConfigBridgeMixin → QWidget`.

**Dual reply backends** (one at a time, no automatic failover):
1. **Direct** (`meapet/direct/`): 4 protocols — `ollama_chat`, `openai_chat`, `openai_responses`, `anthropic_messages`. MeaPet manages prompts, context, memory.
2. **Agent** (`meapet/agent/`): Hermes (OpenAI Chat + SSE) or OpenClaw (Gateway WebSocket v4). Agent manages its own model, memory, tools.

**Conversation protocol** (`meapet/conversation/`): Multi-segment reply format with `<MEAPET_SEGMENT>`, `<DISPLAY>`, `<META>` tags. Parser produces stream events (`SegmentStarted`, `SegmentTextDelta`, `SegmentCompleted`) for incremental bubble display. Falls back from meapet format → legacy → plain → ollama-lax as needed.

**Threading model:**
- Pet runs on Qt main thread (blocked only by event loop).
- Async runtime (`meapet/async_runtime.py`): singleton daemon thread running an asyncio loop. `submit(coro)` dispatches to it.
- `ChatWorker` / `TTSWorker` (`meapet/desktop/workers.py`): `async_runtime.submit(coro)` → Future → polled by `QTimer` (~100ms).
- Net I/O uses async `httpx` on the daemon loop. Blocking work (local TTS subprocess) → `asyncio.to_thread`.
- `ScreenWatcher` runs in its own `QThread`.
- **Never** block the GUI thread with network I/O or TTS.

**Window lifecycle:**
- Flags: `Qt.Tool | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint` (no `SubWindow` — invisible on Windows).
- `WA_QuitOnClose = False`; exit only through tray menu.
- `app.setQuitOnLastWindowClosed(False)` + offscreen keepalive `QWidget` prevent early exit.
- `socket` must be imported **before** any PyQt path (QtNetwork hook conflict) — enforced in `app.py` and `chat/engine.py`.

**Config** (`meapet/config/store.py`): Single `config.json`. Env var > config.json priority. `$ENV_VAR` / `${ENV_VAR}` placeholders. `resolve_secret()` handles all credential resolution. Key env vars: `DEEPSEEK_API_KEY`, `MIMO_API_KEY`, `MEAPET_API_KEY`, `HERMES_API_SERVER_KEY`, `MEAPET_CONTROL_TOKEN`, `GSV_PYTHON`, `MEAPET_FORCE_PNG`, `MEAPET_DEBUG`.

**Companion MCP** (`meapet/control/`): Optional Streamable HTTP server exposing 4 tools — `meapet.say`, `meapet.express`, `meapet.get_state`, `meapet.capture_screen`. Security: Bearer Token, IP/Host/Origin validation, rate limiting, optional mTLS. Defaults to 127.0.0.1 only.

**Memory & affection** (`meapet/memory/db.py`): SQLite with jieba token-level embeddings (SCHEMA_VERSION=5). Affection 0–100, start=5, per-turn +1/2/3 by length, daily cap=15. Tiers define relationship phrases. RLock-protected.

**TTS** (`meapet/tts/`): `MeaTTS` inherits `TtsMimoMixin`, `TtsGsvMixin`, `TtsVitsMixin`. Language policy handles routing, translation fallback. GPT-SoVITS supports per-language reference audio.

**Vision** (`meapet/vision/`): Three modes — `disabled`, `inherit` (shared with main model), `relay` (independent vision model generates summary). Screenshots require per-execution user confirmation.

**Chat flow** (`meapet/desktop/chat_flow.py`): Coordinates conversation state, timeline, memory extraction, TTS sequencing, bubble display. Serializes memory operations with `_memory_op_lock`.

**UI design system**: Dark theme (`#0E1020` canvas). Semantic color palette, LXGW WenKai font, 44px touch minimum, rounded corners 8/12/18px. Defined in `meapet/ui_theme.py`, design constraints in `design-system/MASTER.md`. Read those before editing pet UI. Status text lives in `meapet/desktop/status_language.py` (functions, not raw strings).

**Testing:** 26 test files in `tests/`. `pytest.ini_options` with `addopts = "-ra"`. After UI changes, run `tests/test_ui_refactor.py` + `tests/test_live2d_startup.py`. If changing menu text, update assertions in `test_ui_refactor.py`.

## Key behaviors (not obvious from code)

- **Chat history**: max 16 messages; keeps system prompt + last 14 on overflow.
- **Memory extraction**: immediate on keywords "记住 / 记下 / 别忘了 / 提醒我"; else every 3 turns.
- **Bubble duration**: `bubble_duration_ms` keys `default/reply/watch/interaction/thinking`. When `tts.sync_with_audio=true`, waits for TTS audio before showing bubble.
- **Screen watcher**: random interval from `watcher.interval.min_ms/max_ms`. Off by default. Cloud vision requires `watcher.allow_cloud=true` + per-run confirmation with timeout → cancel.
- **Config application**: save cancels inflight generation and rebuilds backend. Late replies/TTS/screenshots from old session are discarded.
- **Ollama protocol**: uses `/api/chat` NDJSON streaming. Other protocols use SSE.
- **`meapet/config/store.py`** has `print` debug statements throughout — these flush to stderr on every config operation. Don't add more.
