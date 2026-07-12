"""MeaPet 的跨窗口语义化 UI 设计令牌。"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping


_PALETTE = {
    "canvas": "#0E1020",
    "surface": "#17192D",
    "surface_elevated": "#20233D",
    "surface_input": "#111326",
    "primary": "#FF91B4",
    "primary_hover": "#FFA8C4",
    "on_primary": "#26131B",
    "secondary": "#FFB36B",
    "accent": "#A69BFF",
    "text_primary": "#F8F8FC",
    "text_secondary": "#CACCE0",
    "text_muted": "#9FA3BC",
    "border": "#3B3E5B",
    "border_strong": "#555A7B",
    "focus": "#C0B9FF",
    "success": "#70DDB0",
    "warning": "#F4CC75",
    "danger": "#FF8892",
    "on_danger": "#2A1014",
}

PALETTE: Mapping[str, str] = MappingProxyType(_PALETTE)

FONT_FAMILY = (
    '"Segoe UI", "Microsoft YaHei UI", "Microsoft YaHei", '
    '"PingFang SC", "Noto Sans CJK SC", sans-serif'
)
MONO_FONT_FAMILY = '"Cascadia Mono", "JetBrains Mono", Consolas, monospace'

MIN_TARGET_SIZE = 44

SPACE_1 = 4
SPACE_2 = 8
SPACE_3 = 12
SPACE_4 = 16
SPACE_5 = 20
SPACE_6 = 24
SPACE_8 = 32

RADIUS_SMALL = 8
RADIUS_MEDIUM = 12
RADIUS_LARGE = 18


def rgba(color: str, alpha: int) -> str:
    """把 ``#RRGGBB`` 转成 Qt 样式表可用的 ``rgba`` 字符串。"""
    value = color.removeprefix("#")
    if len(value) != 6:
        raise ValueError(f"颜色必须使用 #RRGGBB 格式: {color!r}")
    if not 0 <= alpha <= 255:
        raise ValueError(f"alpha 必须在 0..255 之间: {alpha}")
    red, green, blue = (int(value[index : index + 2], 16) for index in (0, 2, 4))
    return f"rgba({red}, {green}, {blue}, {alpha})"


def contrast_ratio(foreground: str, background: str) -> float:
    """返回两个 ``#RRGGBB`` 颜色的 WCAG 2.x 对比度。"""
    foreground_luminance = _relative_luminance(foreground)
    background_luminance = _relative_luminance(background)
    lighter = max(foreground_luminance, background_luminance)
    darker = min(foreground_luminance, background_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def _relative_luminance(color: str) -> float:
    value = color.removeprefix("#")
    if len(value) != 6:
        raise ValueError(f"颜色必须使用 #RRGGBB 格式: {color!r}")
    channels = [int(value[index : index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
