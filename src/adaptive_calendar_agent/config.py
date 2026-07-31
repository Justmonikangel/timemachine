from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class VoiceConfig:
    model: str = "small"
    device: str = "cpu"
    compute_type: str = "int8"


@dataclass(frozen=True)
class PlanningConfig:
    capacity_ratio: float
    horizon_days: int
    max_high_energy_blocks_per_day: int
    transition_buffer_minutes: int
    post_class_buffer_minutes: int
    default_task_block_minutes: int
    maximum_block_minutes: dict[str, int]
    working_hours: dict[str, tuple[str, str]]


@dataclass(frozen=True)
class SafetyConfig:
    preview_required: bool
    allow_skip_non_protected_events: bool
    only_modify_managed_focus_blocks: bool


@dataclass(frozen=True)
class Settings:
    timezone: str
    focus_calendar_name: str
    protected_calendar_names: tuple[str, ...]
    deadline_calendar_names: tuple[str, ...]
    planning: PlanningConfig
    safety: SafetyConfig
    voice: VoiceConfig
    db_path: Path
    credentials_path: Path
    token_path: Path


def _tuple_hours(raw: dict) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for day, values in raw.items():
        if not isinstance(values, list) or len(values) != 2:
            raise ValueError(f"working_hours.{day} must contain [start, end]")
        result[day.lower()] = (str(values[0]), str(values[1]))
    return result


def load_settings(path: str | Path | None = None) -> Settings:
    config_path = Path(path or os.getenv("ACA_POLICY_PATH", "policy.yaml"))
    if not config_path.exists():
        raise FileNotFoundError(
            f"Policy file not found: {config_path}. Copy config/policy.example.yaml to policy.yaml."
        )

    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    planning = data["planning"]
    safety = data["safety"]
    voice = data.get("voice", {})

    capacity = float(planning["capacity_ratio"])
    if not 0 < capacity <= 1:
        raise ValueError("capacity_ratio must be in (0, 1]")

    return Settings(
        timezone=str(data["timezone"]),
        focus_calendar_name=str(data["focus_calendar_name"]),
        protected_calendar_names=tuple(data.get("protected_calendar_names", [])),
        deadline_calendar_names=tuple(data.get("deadline_calendar_names", [])),
        planning=PlanningConfig(
            capacity_ratio=capacity,
            horizon_days=int(planning["horizon_days"]),
            max_high_energy_blocks_per_day=int(planning["max_high_energy_blocks_per_day"]),
            transition_buffer_minutes=int(planning["transition_buffer_minutes"]),
            post_class_buffer_minutes=int(planning["post_class_buffer_minutes"]),
            default_task_block_minutes=int(planning["default_task_block_minutes"]),
            maximum_block_minutes={
                str(k): int(v) for k, v in planning["maximum_block_minutes"].items()
            },
            working_hours=_tuple_hours(planning["working_hours"]),
        ),
        safety=SafetyConfig(
            preview_required=bool(safety["preview_required"]),
            allow_skip_non_protected_events=bool(
                safety.get("allow_skip_non_protected_events", False)
            ),
            only_modify_managed_focus_blocks=bool(
                safety.get("only_modify_managed_focus_blocks", True)
            ),
        ),
        voice=VoiceConfig(
            model=str(voice.get("model", "small")),
            device=str(voice.get("device", "cpu")),
            compute_type=str(voice.get("compute_type", "int8")),
        ),
        db_path=Path(os.getenv("ACA_DB_PATH", "adaptive_calendar_agent.db")),
        credentials_path=Path(
            os.getenv("ACA_CREDENTIALS_PATH", ".secrets/credentials.json")
        ),
        token_path=Path(os.getenv("ACA_TOKEN_PATH", ".secrets/token.json")),
    )
