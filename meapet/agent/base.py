"""Agent 适配器与前端编排器之间的稳定边界。"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass, field
from typing import Mapping, Tuple

from meapet.conversation.output_protocol import ParseResult
from meapet.conversation.timeline import ConversationKey


_IMAGE_MEDIA_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
_MAX_IMAGE_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class ImageAttachment:
    """仅允许内联、有界的截图，避免 SSRF 与无界载荷。"""

    media_type: str
    data: str
    file_name: str = "screenshot.jpg"

    def __post_init__(self) -> None:
        media_type = str(self.media_type or "").strip().lower()
        if media_type not in _IMAGE_MEDIA_TYPES:
            raise ValueError("image media_type is unsupported")
        data = str(self.data or "").strip()
        if not data:
            raise ValueError("image data is required")
        try:
            decoded = base64.b64decode(data, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("image data must be valid base64") from exc
        if not decoded or len(decoded) > _MAX_IMAGE_BYTES:
            raise ValueError("image data exceeds the allowed size")
        file_name = str(self.file_name or "screenshot.jpg").strip()
        if (
            not file_name
            or len(file_name) > 128
            or any(char in file_name for char in "/\\\r\n\x00")
        ):
            raise ValueError("image file_name is unsafe")
        object.__setattr__(self, "media_type", media_type)
        object.__setattr__(self, "data", data)
        object.__setattr__(self, "file_name", file_name)

    @property
    def decoded_size(self) -> int:
        padding = len(self.data) - len(self.data.rstrip("="))
        return (len(self.data) * 3 // 4) - padding

    def canonical_part(self) -> dict[str, str]:
        return {
            "type": "image",
            "media_type": self.media_type,
            "data": self.data,
        }


@dataclass(frozen=True)
class AgentTurnRequest:
    turn_id: str
    user_text: str
    history: Tuple[Mapping[str, object], ...] = ()
    frontend_context: Mapping[str, object] = field(default_factory=dict)
    tts_enabled: bool = False
    attachments: Tuple[ImageAttachment, ...] = ()
    conversation_key: ConversationKey | None = None
    generation_id: int = 0

    def __post_init__(self) -> None:
        turn_id = str(self.turn_id or "").strip()
        if not turn_id:
            raise ValueError("turn_id is required")
        if len(turn_id) > 256 or any(char in turn_id for char in "\r\n\x00"):
            raise ValueError("turn_id is not a safe request identifier")
        object.__setattr__(self, "turn_id", turn_id)
        object.__setattr__(self, "user_text", str(self.user_text or "").strip())
        object.__setattr__(self, "history", tuple(self.history or ()))
        object.__setattr__(self, "frontend_context", dict(self.frontend_context or {}))
        object.__setattr__(self, "tts_enabled", bool(self.tts_enabled))
        conversation_key = self.conversation_key
        if conversation_key is not None and not isinstance(
            conversation_key,
            ConversationKey,
        ):
            raise TypeError("conversation_key must be a ConversationKey")
        try:
            generation_id = int(self.generation_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("generation_id must be an integer") from exc
        if generation_id < 0:
            raise ValueError("generation_id cannot be negative")
        object.__setattr__(self, "generation_id", generation_id)
        attachments = tuple(self.attachments or ())
        if len(attachments) > 4 or any(
            not isinstance(item, ImageAttachment) for item in attachments
        ):
            raise ValueError("attachments must contain at most four images")
        object.__setattr__(self, "attachments", attachments)


@dataclass(frozen=True)
class ToolStatus:
    state: str
    safe_text: str


@dataclass(frozen=True)
class FormatRepairRequired:
    result: ParseResult


@dataclass(frozen=True)
class TurnCompleted:
    turn_id: str
    result: ParseResult


@dataclass(frozen=True)
class TurnFailed:
    turn_id: str
    category: str
    safe_message: str
    retryable: bool = False


@dataclass(frozen=True)
class TurnCancelled:
    turn_id: str
