"""Structured, bounded relay output from a dedicated vision model."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class VisionObservation:
    summary: str
    application: str = ""
    activity: str = "unknown"
    notable_text: tuple[str, ...] = ()
    sensitive: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "summary": self.summary,
            "application": self.application,
            "activity": self.activity,
            "notable_text": list(self.notable_text),
            "sensitive": self.sensitive,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )


def _bounded_text(value: object, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit].strip()


def parse_vision_observation(raw: object) -> VisionObservation | None:
    text = str(raw or "").strip()
    if not text:
        return None
    fenced = re.fullmatch(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.I)
    if fenced:
        text = fenced.group(1).strip()
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        summary = _bounded_text(text, 800)
        return VisionObservation(summary=summary) if summary else None
    if not isinstance(payload, dict):
        return None
    summary = _bounded_text(payload.get("summary"), 800)
    if not summary:
        return None
    raw_notable = payload.get("notable_text")
    notable = []
    if isinstance(raw_notable, list):
        for value in raw_notable[:10]:
            item = _bounded_text(value, 120)
            if item and item not in notable:
                notable.append(item)
    return VisionObservation(
        summary=summary,
        application=_bounded_text(payload.get("application"), 120),
        activity=_bounded_text(payload.get("activity"), 64) or "unknown",
        notable_text=tuple(notable),
        sensitive=bool(payload.get("sensitive", False)),
    )


__all__ = ["VisionObservation", "parse_vision_observation"]
