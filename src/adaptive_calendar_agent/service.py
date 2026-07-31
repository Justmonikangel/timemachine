from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from adaptive_calendar_agent.config import Settings
from adaptive_calendar_agent.google_calendar import GoogleCalendarAdapter
from adaptive_calendar_agent.models import (
    CommandType,
    MutationKind,
    Plan,
    PlannedMutation,
)
from adaptive_calendar_agent.parser import parse_command
from adaptive_calendar_agent.scheduler import schedule_tasks
from adaptive_calendar_agent.store import Store


class CalendarAgentService:
    def __init__(
        self,
        settings: Settings,
        store: Store,
        calendar: GoogleCalendarAdapter,
    ) -> None:
        self.settings = settings
        self.store = store
        self.calendar = calendar

    def preview_replan(self, horizon_days: int | None = None, command_text: str | None = None) -> Plan:
        tz = ZoneInfo(self.settings.timezone)
        start = datetime.now(tz).replace(second=0, microsecond=0)
        days = horizon_days or self.settings.planning.horizon_days
        end = start + timedelta(days=days)
        events = self.calendar.list_events(start, end)
        tasks = self.store.list_tasks()
        blocks, unscheduled = schedule_tasks(
            tasks,
            events,
            start,
            end,
            self.settings.planning,
            self.settings.timezone,
        )
        command = parse_command(command_text) if command_text else None
        plan = Plan(
            created_at=datetime.now(tz),
            command=command,
            blocks=blocks,
            mutations=[
                PlannedMutation(
                    kind=MutationKind.CREATE_FOCUS_BLOCK,
                    payload=block.model_dump(mode="json"),
                )
                for block in blocks
            ],
            unscheduled_task_ids=unscheduled,
        )
        if unscheduled:
            plan.warnings.append(
                "Some tasks could not be fully scheduled within the horizon and capacity limit."
            )
        self.store.save_plan(plan)
        return plan

    def preview_command(self, text: str) -> Plan:
        command = parse_command(text)
        tz = ZoneInfo(self.settings.timezone)
        if command.command_type == CommandType.REPLAN:
            return self.preview_replan(command.horizon_days, command_text=text)

        if command.command_type == CommandType.SKIP_EVENT:
            plan = Plan(created_at=datetime.now(tz), command=command)
            plan.mutations.append(
                PlannedMutation(
                    kind=MutationKind.SKIP_EVENT_REQUEST,
                    payload={"target": command.target, "scope": "this_week"},
                    risk="medium",
                )
            )
            plan.warnings.append(
                "V0.1 records skip requests but does not delete or alter non-agent calendar events. "
                "After confirming the event safely, trigger a replan."
            )
            self.store.save_plan(plan)
            return plan

        plan = Plan(created_at=datetime.now(tz), command=command)
        plan.warnings.extend(command.notes)
        self.store.save_plan(plan)
        return plan

    def apply_plan(self, plan_id: str) -> dict:
        plan = self.store.get_plan(plan_id)
        if plan is None:
            raise KeyError(f"Plan not found: {plan_id}")
        if plan.applied:
            raise ValueError("Plan has already been applied.")

        if any(m.kind == MutationKind.SKIP_EVENT_REQUEST for m in plan.mutations):
            raise ValueError(
                "Skip requests are not directly executable in V0.1. Confirm the matching event first."
            )

        if not plan.blocks:
            raise ValueError("The plan contains no focus blocks to apply.")

        start = min(block.start for block in plan.blocks)
        end = max(block.end for block in plan.blocks) + timedelta(minutes=1)
        deleted = self.calendar.delete_managed_focus_blocks(start, end)
        created_ids = [
            self.calendar.create_focus_block(block, plan.id) for block in plan.blocks
        ]
        self.store.mark_plan_applied(plan)
        payload = {
            "plan_id": plan.id,
            "deleted_managed_blocks": deleted,
            "created_event_ids": created_ids,
        }
        self.store.audit("apply_plan", payload)
        return payload
