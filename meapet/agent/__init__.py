"""外部 Agent 运行时适配器。"""

from .base import (
    AgentTurnRequest,
    FormatRepairRequired,
    ToolStatus,
    TurnCancelled,
    TurnCompleted,
    TurnFailed,
)
from .hermes import HermesAdapter, HermesCapabilities, HermesConfig
from .presentation import AgentTurnPresentation

__all__ = [
    "AgentTurnRequest",
    "AgentTurnPresentation",
    "FormatRepairRequired",
    "HermesAdapter",
    "HermesCapabilities",
    "HermesConfig",
    "ToolStatus",
    "TurnCancelled",
    "TurnCompleted",
    "TurnFailed",
]
