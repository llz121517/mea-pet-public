"""把统一 Agent 事件转换为不依赖 Qt 的气泡、TTS 与播放动作。"""

from __future__ import annotations

from dataclasses import dataclass, replace

from meapet.agent.base import (
    FormatRepairRequired,
    ToolStatus,
    TurnCancelled,
    TurnCompleted,
    TurnFailed,
)
from meapet.conversation.output_protocol import (
    SegmentCompleted,
    SegmentStarted,
    SegmentTextDelta,
)
from meapet.conversation.types import ReplySegment


@dataclass(frozen=True)
class BeginBubble:
    index: int


@dataclass(frozen=True)
class UpdateBubble:
    index: int
    text: str


@dataclass(frozen=True)
class FinalizeBubble:
    segment: ReplySegment
    duration_ms: int
    wav_path: str = ""


@dataclass(frozen=True)
class SubmitTTS:
    segment: ReplySegment


@dataclass(frozen=True)
class PlayAudio:
    index: int
    wav_path: str
    duration_ms: int


@dataclass(frozen=True)
class ShowStatus:
    state: str
    safe_text: str


@dataclass(frozen=True)
class RequestFormatRepair:
    result: object


@dataclass(frozen=True)
class FinishTurn:
    turn_id: str


@dataclass(frozen=True)
class FailTurn:
    turn_id: str
    category: str
    safe_message: str


@dataclass(frozen=True)
class CancelTurn:
    turn_id: str


class AgentTurnPresentation:
    """维护单轮呈现顺序；调用方只需执行返回的不可变动作。"""

    def __init__(
        self,
        *,
        tts_enabled: bool,
        reply_min_duration_ms: int = 3000,
        supported_moods: tuple[str, ...] = (),
    ) -> None:
        self.tts_enabled = bool(tts_enabled)
        self.reply_min_duration_ms = max(0, int(reply_min_duration_ms))
        self.supported_moods = frozenset(
            str(mood or "").strip().lower()
            for mood in supported_moods
            if str(mood or "").strip()
        )
        self._texts: dict[int, str] = {}
        self._begun: set[int] = set()
        self._segments: dict[int, ReplySegment] = {}
        self._tts_results: dict[int, tuple[str, int]] = {}
        self._next_present_index = 0
        self._playing_index: int | None = None
        self._turn_id = ""
        self._expected_segments: int | None = None
        self._finished = False

    def consume(self, event: object) -> tuple[object, ...]:
        if self._finished:
            return ()
        if isinstance(event, ToolStatus):
            return (ShowStatus(event.state, event.safe_text),)
        if isinstance(event, SegmentStarted):
            self._begun.add(event.index)
            self._texts.setdefault(event.index, "")
            if self.tts_enabled:
                return ()
            return (BeginBubble(event.index),)
        if isinstance(event, SegmentTextDelta):
            current = self._texts.get(event.index, "") + event.delta
            self._texts[event.index] = current
            if self.tts_enabled:
                return ()
            actions = []
            if event.index not in self._begun:
                self._begun.add(event.index)
                actions.append(BeginBubble(event.index))
            actions.append(UpdateBubble(event.index, current))
            return tuple(actions)
        if isinstance(event, SegmentCompleted):
            segment = event.segment
            if self.supported_moods and segment.mood not in self.supported_moods:
                segment = replace(segment, mood="neutral")
            self._segments[segment.index] = segment
            self._texts[segment.index] = segment.display_text
            if not self.tts_enabled:
                return (
                    FinalizeBubble(
                        segment,
                        duration_ms=self.reply_min_duration_ms,
                        wav_path="",
                    ),
                )
            missing = set(segment.missing_required_fields)
            if missing.intersection({"voice_text", "voice_language"}):
                self._tts_results[segment.index] = ("", 0)
                return self._drain_ready()
            return (SubmitTTS(segment),)
        if isinstance(event, FormatRepairRequired):
            return (RequestFormatRepair(event.result),)
        if isinstance(event, TurnCompleted):
            self._turn_id = event.turn_id
            self._expected_segments = len(event.result.segments)
            if not self.tts_enabled:
                return self._finish_if_ready(force=True)
            return self._finish_if_ready()
        if isinstance(event, TurnFailed):
            self._finished = True
            return (
                FailTurn(
                    turn_id=event.turn_id,
                    category=event.category,
                    safe_message=event.safe_message,
                ),
            )
        if isinstance(event, TurnCancelled):
            self._finished = True
            return (CancelTurn(event.turn_id),)
        return ()

    def tts_ready(
        self,
        index: int,
        wav_path: str,
        *,
        audio_duration_ms: int,
    ) -> tuple[object, ...]:
        if self._finished or index not in self._segments:
            return ()
        self._tts_results[index] = (
            str(wav_path or ""),
            max(0, int(audio_duration_ms)),
        )
        return self._drain_ready()

    def audio_finished(self, index: int) -> tuple[object, ...]:
        if self._finished or self._playing_index != index:
            return ()
        self._playing_index = None
        self._next_present_index = index + 1
        return self._drain_ready()

    def _drain_ready(self) -> tuple[object, ...]:
        actions = []
        while (
            self._playing_index is None
            and self._next_present_index in self._tts_results
            and self._next_present_index in self._segments
        ):
            index = self._next_present_index
            wav_path, audio_duration_ms = self._tts_results.pop(index)
            segment = self._segments[index]
            duration_ms = self.reply_min_duration_ms
            if wav_path and audio_duration_ms > 0:
                duration_ms = max(duration_ms, audio_duration_ms + 500)
            actions.append(
                FinalizeBubble(
                    segment,
                    duration_ms=duration_ms,
                    wav_path=wav_path,
                )
            )
            if wav_path:
                self._playing_index = index
                actions.append(PlayAudio(index, wav_path, audio_duration_ms))
                break
            self._next_present_index += 1
        actions.extend(self._finish_if_ready())
        return tuple(actions)

    def _finish_if_ready(self, *, force: bool = False) -> tuple[object, ...]:
        if self._finished or not self._turn_id:
            return ()
        if not force:
            if self._expected_segments is None or self._playing_index is not None:
                return ()
            if self._next_present_index < self._expected_segments:
                return ()
        self._finished = True
        return (FinishTurn(self._turn_id),)
