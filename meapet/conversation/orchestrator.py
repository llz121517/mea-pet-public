"""活动对话代次与迟到事件隔离。"""

from __future__ import annotations

import threading
from dataclasses import dataclass

from meapet.conversation.timeline import ConversationKey


@dataclass(frozen=True)
class TurnContext:
    """一次回复在创建时绑定的不可变关联信息。"""

    conversation_key: ConversationKey
    turn_id: str
    generation_id: int

    def __post_init__(self) -> None:
        turn_id = str(self.turn_id or "").strip()
        if not turn_id:
            raise ValueError("turn_id is required")
        if len(turn_id) > 256 or any(char in turn_id for char in "\r\n\x00"):
            raise ValueError("turn_id is not a safe request identifier")
        generation_id = int(self.generation_id)
        if generation_id <= 0:
            raise ValueError("generation_id must be positive")
        object.__setattr__(self, "turn_id", turn_id)
        object.__setattr__(self, "generation_id", generation_id)


class ConversationOrchestrator:
    """只接受当前 ConversationKey、代次和 turn 的事件。"""

    def __init__(self, conversation_key: ConversationKey) -> None:
        if not isinstance(conversation_key, ConversationKey):
            raise TypeError("conversation_key must be a ConversationKey")
        self._lock = threading.RLock()
        self._conversation_key = conversation_key
        self._generation_id = 1
        self._active_turn_id = ""

    @property
    def conversation_key(self) -> ConversationKey:
        with self._lock:
            return self._conversation_key

    @property
    def generation_id(self) -> int:
        with self._lock:
            return self._generation_id

    def activate(self, conversation_key: ConversationKey) -> int:
        """切换会话时递增代次；相同 key 的重复激活保持当前请求。"""
        if not isinstance(conversation_key, ConversationKey):
            raise TypeError("conversation_key must be a ConversationKey")
        with self._lock:
            if conversation_key != self._conversation_key:
                self._conversation_key = conversation_key
                self._generation_id += 1
                self._active_turn_id = ""
            return self._generation_id

    def begin_turn(self, turn_id: str) -> TurnContext:
        with self._lock:
            context = TurnContext(
                self._conversation_key,
                turn_id,
                self._generation_id,
            )
            self._active_turn_id = context.turn_id
            return context

    def accepts(self, context: TurnContext | None) -> bool:
        if not isinstance(context, TurnContext):
            return False
        with self._lock:
            return (
                context.conversation_key == self._conversation_key
                and context.generation_id == self._generation_id
                and context.turn_id == self._active_turn_id
            )

    def complete(self, context: TurnContext | None) -> bool:
        with self._lock:
            if not self.accepts(context):
                return False
            self._active_turn_id = ""
            return True

    def invalidate(self) -> int:
        """取消当前代次，使所有已发出的异步回调立即失效。"""
        with self._lock:
            self._generation_id += 1
            self._active_turn_id = ""
            return self._generation_id
