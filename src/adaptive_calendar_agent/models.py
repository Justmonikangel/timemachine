from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class Energy(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    duration_min: int = Field(gt=0)
    deadline: datetime
    priority: int = Field(default=3, ge=1, le=5)
    energy: Energy = Energy.MEDIUM
    project: str = "general"
    splittable: bool = True
    min_block_min: int = Field(default=25, gt=0)
    status: TaskStatus = TaskStatus.ACTIVE
    rollover_count: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_block(self) -> Task:
        self.min_block_min = min(self.min_block_min, self.duration_min)
        return self


class CalendarEvent(BaseModel):
    id: str
    calendar_id: str
    calendar_name: str
    title: str
    start: datetime
    end: datetime
    protected: bool = False
    deadline_marker: bool = False
    managed: bool = False
    recurring_event_id: str | None = None


class CommandType(StrEnum):
    SKIP_EVENT = "skip_event"
    REPLAN = "replan"
    ADD_TASK = "add_task"
    UNKNOWN = "unknown"


class ParsedCommand(BaseModel):
    command_type: CommandType
    raw_text: str
    target: str | None = None
    horizon_days: int | None = None
    confidence: float = Field(default=1.0, ge=0, le=1)
    requires_confirmation: bool = True
    notes: list[str] = Field(default_factory=list)


class PlannedBlock(BaseModel):
    task_id: str
    task_title: str
    start: datetime
    end: datetime
    energy: Energy
    project: str


class MutationKind(StrEnum):
    CREATE_FOCUS_BLOCK = "create_focus_block"
    SKIP_EVENT_REQUEST = "skip_event_request"


class PlannedMutation(BaseModel):
    kind: MutationKind
    payload: dict
    risk: str = "low"


class Plan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime
    command: ParsedCommand | None = None
    blocks: list[PlannedBlock] = Field(default_factory=list)
    mutations: list[PlannedMutation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    unscheduled_task_ids: list[str] = Field(default_factory=list)
    applied: bool = False
