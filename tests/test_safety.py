from pathlib import Path

from adaptive_calendar_agent.config import (
    PlanningConfig,
    SafetyConfig,
    Settings,
    VoiceConfig,
)


def test_protected_calendar_configuration() -> None:
    settings = Settings(
        timezone="Australia/Melbourne",
        focus_calendar_name="Focus Blocks",
        protected_calendar_names=("Monash class", "Assessments"),
        deadline_calendar_names=("Assessments",),
        planning=PlanningConfig(
            capacity_ratio=0.7,
            horizon_days=14,
            max_high_energy_blocks_per_day=2,
            transition_buffer_minutes=15,
            post_class_buffer_minutes=30,
            default_task_block_minutes=60,
            maximum_block_minutes={"high": 90, "medium": 75, "low": 60},
            working_hours={"monday": ("09:00", "17:00")},
        ),
        safety=SafetyConfig(
            preview_required=True,
            allow_skip_non_protected_events=False,
            only_modify_managed_focus_blocks=True,
        ),
        voice=VoiceConfig(),
        db_path=Path("test.db"),
        credentials_path=Path("credentials.json"),
        token_path=Path("token.json"),
    )
    assert "Monash class" in settings.protected_calendar_names
    assert settings.safety.only_modify_managed_focus_blocks is True
