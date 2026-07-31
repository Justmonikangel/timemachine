from __future__ import annotations

import re

from adaptive_calendar_agent.models import CommandType, ParsedCommand

_CHINESE_SKIP = re.compile(
    r"这周(?:先)?(?:不去|不上|暂停|跳过)\s*(?P<target>.+?)(?:的?课)?(?:了)?[。.!]?$",
    re.IGNORECASE,
)
_ENGLISH_SKIP = re.compile(
    r"(?:skip|pause)\s+(?P<target>.+?)\s+(?:this week|for this week)[.!]?$",
    re.IGNORECASE,
)
_REPLAN_DAYS = re.compile(
    r"(?:未来|接下来|next)\s*(?P<days>\d+)\s*(?:天|days?)",
    re.IGNORECASE,
)


def parse_command(text: str) -> ParsedCommand:
    normalized = " ".join(text.strip().split())
    if not normalized:
        return ParsedCommand(
            command_type=CommandType.UNKNOWN,
            raw_text=text,
            confidence=0,
            notes=["Empty command."],
        )

    for pattern in (_CHINESE_SKIP, _ENGLISH_SKIP):
        match = pattern.search(normalized)
        if match:
            target = match.group("target").strip(" ,，。")
            return ParsedCommand(
                command_type=CommandType.SKIP_EVENT,
                raw_text=text,
                target=target,
                confidence=0.92,
                requires_confirmation=True,
                notes=["A skip request never deletes a protected calendar event."],
            )

    lowered = normalized.lower()
    if "重新排" in normalized or "replan" in lowered or "重新安排" in normalized:
        match = _REPLAN_DAYS.search(normalized)
        days = int(match.group("days")) if match else None
        return ParsedCommand(
            command_type=CommandType.REPLAN,
            raw_text=text,
            horizon_days=days,
            confidence=0.98,
            requires_confirmation=True,
        )

    return ParsedCommand(
        command_type=CommandType.UNKNOWN,
        raw_text=text,
        confidence=0.2,
        notes=["Unsupported command. The parser intentionally does not guess."],
    )
