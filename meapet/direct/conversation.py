"""把直连模型的 Canonical 流转换为 MeaPet 统一分段事件。"""

from __future__ import annotations

from typing import AsyncIterator

from meapet.agent.base import (
    AgentTurnRequest,
    FormatRepairRequired,
    TurnCancelled,
    TurnCompleted,
    TurnFailed,
)
from meapet.agent.prompts import (
    MAX_REPAIR_INPUT_CHARS,
    OUTPUT_INSTRUCTION,
    REPAIR_INSTRUCTION,
    frontend_context_json,
)
from meapet.conversation.output_protocol import (
    MeaPetOutputStreamParser,
    ProtocolCompleted,
    SegmentCompleted,
)
from meapet.direct.client import DirectProtocolError
from meapet.direct.types import (
    CanonicalChatRequest,
    ReasoningDelta,
    StreamDone,
    TextDelta,
)


class DirectConversationAdapter:
    """协调 MeaPet 本地角色/历史与供应商无关的流式协议客户端。"""

    def __init__(self, engine, protocol_client) -> None:
        self.engine = engine
        self.protocol_client = protocol_client
        self._cancelled_turns: set[str] = set()

    def _canonical_request(
        self,
        messages,
        *,
        max_tokens: int | None = None,
    ) -> CanonicalChatRequest:
        return CanonicalChatRequest(
            model=self.engine.model,
            messages=tuple(messages),
            temperature=self.engine.temperature,
            max_tokens=max_tokens or self.engine.max_tokens,
            stream=True,
        )

    async def cancel(self, turn_id: str) -> None:
        self._cancelled_turns.add(str(turn_id or "").strip())

    async def close(self) -> None:
        await self.protocol_client.close()

    async def _repair_result(
        self,
        *,
        request: AgentTurnRequest,
        malformed_output: str,
    ):
        repair_request = self._canonical_request(
            (
                {"role": "system", "content": REPAIR_INSTRUCTION},
                {
                    "role": "user",
                    "content": malformed_output[:MAX_REPAIR_INPUT_CHARS],
                },
            )
        )
        parser = MeaPetOutputStreamParser()
        try:
            async for event in self.protocol_client.stream(repair_request):
                if request.turn_id in self._cancelled_turns:
                    return None
                if isinstance(event, TextDelta):
                    parser.feed(event.delta)
                elif isinstance(event, StreamDone):
                    break
        except DirectProtocolError:
            return None
        result = parser.close(tts_enabled=request.tts_enabled)
        if result.requires_repair(tts_enabled=request.tts_enabled):
            return None
        return result

    async def stream_turn(self, request: AgentTurnRequest) -> AsyncIterator[object]:
        if request.turn_id in self._cancelled_turns:
            self._cancelled_turns.discard(request.turn_id)
            yield TurnCancelled(request.turn_id)
            return
        if not self.engine.available:
            yield TurnFailed(
                request.turn_id,
                "backend_unavailable",
                "模型服务尚未就绪，请检查配置和运行状态。",
                True,
            )
            return

        prepared = False
        try:
            messages = self.engine._prepare_direct_turn(request.user_text)
            prepared = True
            system = str(messages[0].get("content") or "")
            messages[0] = {
                "role": "system",
                "content": (
                    f"{system}\n\n{OUTPUT_INSTRUCTION}\n"
                    f"前端只读摘要：{frontend_context_json(request)}"
                ),
            }
            canonical = self._canonical_request(messages)
            parser = MeaPetOutputStreamParser()
            raw_chunks: list[str] = []
            completed_indices: set[int] = set()
            protocol_completed_emitted = False
            stream_done = False

            async for event in self.protocol_client.stream(canonical):
                if request.turn_id in self._cancelled_turns:
                    self._cancelled_turns.discard(request.turn_id)
                    self.engine._rollback_direct_turn(request.user_text)
                    yield TurnCancelled(request.turn_id)
                    return
                if isinstance(event, TextDelta):
                    raw_chunks.append(event.delta)
                    for parsed_event in parser.feed(event.delta):
                        if isinstance(parsed_event, SegmentCompleted):
                            if parsed_event.segment.missing_required_fields:
                                continue
                            completed_indices.add(parsed_event.segment.index)
                        elif isinstance(parsed_event, ProtocolCompleted):
                            protocol_completed_emitted = True
                        yield parsed_event
                elif isinstance(event, ReasoningDelta):
                    # reasoning 仅存在于协议内部，禁止进入气泡、TTS 和时间线正文。
                    continue
                elif isinstance(event, StreamDone):
                    stream_done = True
                    break
            if not stream_done:
                raise DirectProtocolError("protocol", "模型流未正常结束。")

            result = parser.close(tts_enabled=request.tts_enabled)
            if result.requires_repair(tts_enabled=request.tts_enabled):
                yield FormatRepairRequired(result)
                repaired = await self._repair_result(
                    request=request,
                    malformed_output="".join(raw_chunks),
                )
                if request.turn_id in self._cancelled_turns:
                    self._cancelled_turns.discard(request.turn_id)
                    self.engine._rollback_direct_turn(request.user_text)
                    yield TurnCancelled(request.turn_id)
                    return
                if repaired is not None:
                    result = repaired

            if not any(segment.display_text.strip() for segment in result.segments):
                self.engine._rollback_direct_turn(request.user_text)
                yield TurnFailed(
                    request.turn_id,
                    "protocol",
                    "模型没有返回可展示的回复。",
                )
                return

            for segment in result.segments:
                if segment.index not in completed_indices:
                    yield SegmentCompleted(segment)
                    completed_indices.add(segment.index)
            if result.done and not protocol_completed_emitted:
                yield ProtocolCompleted()
            self.engine._commit_direct_turn(result)
            yield TurnCompleted(request.turn_id, result)
        except DirectProtocolError as exc:
            if prepared:
                self.engine._rollback_direct_turn(request.user_text)
            yield TurnFailed(
                request.turn_id,
                exc.category,
                exc.safe_message,
                exc.retryable,
            )
        except (ValueError, TypeError):
            if prepared:
                self.engine._rollback_direct_turn(request.user_text)
            yield TurnFailed(
                request.turn_id,
                "configuration",
                "模型配置不完整，请检查协议、地址和模型。",
            )
