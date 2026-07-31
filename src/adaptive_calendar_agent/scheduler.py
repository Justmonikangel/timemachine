from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from adaptive_calendar_agent.config import PlanningConfig
from adaptive_calendar_agent.models import CalendarEvent, Energy, PlannedBlock, Task

WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def _combine(day: date, clock: str, tz: ZoneInfo) -> datetime:
    parsed = time.fromisoformat(clock)
    return datetime.combine(day, parsed, tzinfo=tz)


def _subtract_busy(
    start: datetime,
    end: datetime,
    busy: list[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    slots = [(start, end)]
    for busy_start, busy_end in sorted(busy):
        next_slots: list[tuple[datetime, datetime]] = []
        for slot_start, slot_end in slots:
            if busy_end <= slot_start or busy_start >= slot_end:
                next_slots.append((slot_start, slot_end))
                continue
            if busy_start > slot_start:
                next_slots.append((slot_start, busy_start))
            if busy_end < slot_end:
                next_slots.append((busy_end, slot_end))
        slots = next_slots
    return [(a, b) for a, b in slots if b > a]


def build_free_slots(
    window_start: datetime,
    window_end: datetime,
    events: list[CalendarEvent],
    planning: PlanningConfig,
    timezone: str,
) -> list[tuple[datetime, datetime]]:
    tz = ZoneInfo(timezone)
    busy_by_day: dict[date, list[tuple[datetime, datetime]]] = defaultdict(list)
    buffer = timedelta(minutes=planning.transition_buffer_minutes)

    for event in events:
        if event.deadline_marker:
            continue
        local_start = event.start.astimezone(tz)
        local_end = event.end.astimezone(tz)
        busy_by_day[local_start.date()].append((local_start - buffer, local_end + buffer))

    slots: list[tuple[datetime, datetime]] = []
    cursor = window_start.astimezone(tz).date()
    final_day = window_end.astimezone(tz).date()
    while cursor <= final_day:
        day_name = WEEKDAYS[cursor.weekday()]
        hours = planning.working_hours.get(day_name)
        if hours:
            day_start = max(_combine(cursor, hours[0], tz), window_start.astimezone(tz))
            day_end = min(_combine(cursor, hours[1], tz), window_end.astimezone(tz))
            if day_end > day_start:
                slots.extend(_subtract_busy(day_start, day_end, busy_by_day[cursor]))
        cursor += timedelta(days=1)
    return slots


def _energy_score(energy: Energy, start: datetime) -> int:
    hour = start.hour
    if energy == Energy.HIGH:
        return 5 if 8 <= hour < 13 else (2 if 13 <= hour < 17 else 0)
    if energy == Energy.MEDIUM:
        return 5 if 11 <= hour < 18 else 2
    return 5 if hour >= 16 else 3


def schedule_tasks(
    tasks: list[Task],
    events: list[CalendarEvent],
    window_start: datetime,
    window_end: datetime,
    planning: PlanningConfig,
    timezone: str,
) -> tuple[list[PlannedBlock], list[str]]:
    slots = build_free_slots(window_start, window_end, events, planning, timezone)
    tz = ZoneInfo(timezone)
    used_minutes_by_day: dict[date, int] = defaultdict(int)
    theoretical_minutes_by_day: dict[date, int] = defaultdict(int)
    high_blocks_by_day: dict[date, int] = defaultdict(int)

    for start, end in slots:
        theoretical_minutes_by_day[start.date()] += int((end - start).total_seconds() // 60)

    remaining_slots = list(slots)
    blocks: list[PlannedBlock] = []
    unscheduled: list[str] = []

    active_tasks = [task for task in tasks if task.status.value == "active"]
    active_tasks.sort(key=lambda task: (task.deadline, -task.priority, task.title.lower()))

    for task in active_tasks:
        minutes_left = task.duration_min
        max_block = planning.maximum_block_minutes[task.energy.value]

        while minutes_left > 0:
            candidates: list[tuple[int, int, datetime, datetime]] = []
            for index, (slot_start, slot_end) in enumerate(remaining_slots):
                local_start = slot_start.astimezone(tz)
                if local_start >= task.deadline.astimezone(tz):
                    continue
                slot_minutes = int((slot_end - slot_start).total_seconds() // 60)
                if slot_minutes < task.min_block_min:
                    continue
                day = local_start.date()
                daily_cap = int(theoretical_minutes_by_day[day] * planning.capacity_ratio)
                if used_minutes_by_day[day] >= daily_cap:
                    continue
                if (
                    task.energy == Energy.HIGH
                    and high_blocks_by_day[day] >= planning.max_high_energy_blocks_per_day
                ):
                    continue
                score = _energy_score(task.energy, local_start)
                score += task.priority
                score += max(0, 5 - (task.deadline.date() - local_start.date()).days)
                candidates.append((score, -index, slot_start, slot_end))

            if not candidates:
                break

            _, neg_index, slot_start, slot_end = max(candidates, key=lambda item: item[0])
            index = -neg_index
            day = slot_start.astimezone(tz).date()
            daily_cap = int(theoretical_minutes_by_day[day] * planning.capacity_ratio)
            available_today = daily_cap - used_minutes_by_day[day]
            slot_minutes = int((slot_end - slot_start).total_seconds() // 60)
            block_minutes = min(minutes_left, max_block, slot_minutes, available_today)
            if block_minutes < task.min_block_min:
                remaining_slots.pop(index)
                continue

            block_end = slot_start + timedelta(minutes=block_minutes)
            blocks.append(
                PlannedBlock(
                    task_id=task.id,
                    task_title=task.title,
                    start=slot_start,
                    end=block_end,
                    energy=task.energy,
                    project=task.project,
                )
            )
            used_minutes_by_day[day] += block_minutes
            if task.energy == Energy.HIGH:
                high_blocks_by_day[day] += 1
            minutes_left -= block_minutes

            if block_end < slot_end:
                remaining_slots[index] = (block_end, slot_end)
            else:
                remaining_slots.pop(index)

            if not task.splittable:
                break

        if minutes_left > 0:
            unscheduled.append(task.id)

    blocks.sort(key=lambda block: block.start)
    return blocks, unscheduled
