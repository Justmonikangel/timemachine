from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from adaptive_calendar_agent.config import PlanningConfig
from adaptive_calendar_agent.models import CalendarEvent, Energy, Task
from adaptive_calendar_agent.scheduler import schedule_tasks


def policy() -> PlanningConfig:
    return PlanningConfig(
        capacity_ratio=0.70,
        horizon_days=2,
        max_high_energy_blocks_per_day=2,
        transition_buffer_minutes=0,
        post_class_buffer_minutes=30,
        default_task_block_minutes=60,
        maximum_block_minutes={"high": 90, "medium": 75, "low": 60},
        working_hours={
            "monday": ("09:00", "17:00"),
            "tuesday": ("09:00", "17:00"),
            "wednesday": ("09:00", "17:00"),
            "thursday": ("09:00", "17:00"),
            "friday": ("09:00", "17:00"),
            "saturday": ("10:00", "16:00"),
            "sunday": ("10:00", "16:00"),
        },
    )


def test_scheduler_avoids_busy_event_and_splits_task() -> None:
    tz = ZoneInfo("Australia/Melbourne")
    start = datetime(2026, 8, 3, 9, 0, tzinfo=tz)
    end = start + timedelta(days=1)
    busy = CalendarEvent(
        id="class",
        calendar_id="classes",
        calendar_name="Monash class",
        title="Workshop",
        start=datetime(2026, 8, 3, 10, 0, tzinfo=tz),
        end=datetime(2026, 8, 3, 12, 0, tzinfo=tz),
        protected=True,
    )
    task = Task(
        title="CS61A recursion",
        duration_min=150,
        deadline=end,
        energy=Energy.HIGH,
        priority=4,
        min_block_min=30,
    )
    blocks, unscheduled = schedule_tasks(
        [task], [busy], start, end, policy(), "Australia/Melbourne"
    )
    assert not unscheduled
    assert sum(int((b.end - b.start).total_seconds() // 60) for b in blocks) == 150
    assert all(not (b.start < busy.end and b.end > busy.start) for b in blocks)
    assert len(blocks) == 2


def test_capacity_limit_is_respected() -> None:
    tz = ZoneInfo("Australia/Melbourne")
    start = datetime(2026, 8, 3, 9, 0, tzinfo=tz)
    end = datetime(2026, 8, 3, 17, 0, tzinfo=tz)
    task = Task(
        title="Huge task",
        duration_min=600,
        deadline=end,
        energy=Energy.MEDIUM,
        priority=5,
    )
    blocks, unscheduled = schedule_tasks(
        [task], [], start, end, policy(), "Australia/Melbourne"
    )
    scheduled = sum(int((b.end - b.start).total_seconds() // 60) for b in blocks)
    assert scheduled <= int(8 * 60 * 0.70)
    assert task.id in unscheduled
