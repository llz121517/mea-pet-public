"""直连模型的 Canonical 请求与线协议适配。"""

from .client import DirectProtocolClient, DirectProtocolConfig, DirectProtocolError
from .types import (
    CanonicalChatRequest,
    ReasoningDelta,
    StreamDone,
    TextDelta,
    UsageEvent,
)

__all__ = [
    "CanonicalChatRequest",
    "DirectProtocolClient",
    "DirectProtocolConfig",
    "DirectProtocolError",
    "ReasoningDelta",
    "StreamDone",
    "TextDelta",
    "UsageEvent",
]
