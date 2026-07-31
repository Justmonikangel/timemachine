from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo

import typer
import uvicorn

from adaptive_calendar_agent.api import app as api_app
from adaptive_calendar_agent.config import load_settings
from adaptive_calendar_agent.google_calendar import GoogleCalendarAdapter
from adaptive_calendar_agent.models import Energy, Task
from adaptive_calendar_agent.service import CalendarAgentService
from adaptive_calendar_agent.store import Store
from adaptive_calendar_agent.voice import transcribe

app = typer.Typer(no_args_is_help=True)


def service() -> CalendarAgentService:
    settings = load_settings()
    store = Store(settings.db_path)
    calendar = GoogleCalendarAdapter(settings)
    return CalendarAgentService(settings, store, calendar)


@app.command()
def auth() -> None:
    agent = service()
    agent.calendar.authenticate()
    typer.echo("Google Calendar authorization succeeded.")


@app.command()
def calendars() -> None:
    agent = service()
    items = agent.calendar.list_calendars()
    for item in items:
        typer.echo(f"{item.get('summary')}\t{item.get('id')}")


@app.command("add-task")
def add_task(
    title: Annotated[str, typer.Option()],
    duration: Annotated[int, typer.Option(help="Total estimated minutes.")],
    deadline: Annotated[str, typer.Option(help="ISO-like local datetime.")],
    energy: Annotated[Energy, typer.Option()] = Energy.MEDIUM,
    priority: Annotated[int, typer.Option(min=1, max=5)] = 3,
    project: Annotated[str, typer.Option()] = "general",
    min_block: Annotated[int, typer.Option()] = 25,
) -> None:
    agent = service()
    tz = ZoneInfo(agent.settings.timezone)
    parsed = datetime.fromisoformat(deadline).replace(tzinfo=tz)
    task = Task(
        title=title,
        duration_min=duration,
        deadline=parsed,
        energy=energy,
        priority=priority,
        project=project,
        min_block_min=min_block,
    )
    agent.store.upsert_task(task)
    typer.echo(task.model_dump_json(indent=2))


@app.command()
def tasks() -> None:
    agent = service()
    typer.echo(json.dumps([t.model_dump(mode="json") for t in agent.store.list_tasks()], indent=2))


@app.command()
def preview(text: str) -> None:
    plan = service().preview_command(text)
    typer.echo(plan.model_dump_json(indent=2))


@app.command()
def replan(days: Annotated[int | None, typer.Option()] = None) -> None:
    plan = service().preview_replan(days)
    typer.echo(plan.model_dump_json(indent=2))


@app.command()
def apply(plan_id: str) -> None:
    result = service().apply_plan(plan_id)
    typer.echo(json.dumps(result, indent=2))


@app.command("voice-preview")
def voice_preview(path: Path) -> None:
    agent = service()
    text = transcribe(path, agent.settings.voice)
    typer.echo(f"Transcript: {text}")
    typer.echo(agent.preview_command(text).model_dump_json(indent=2))


@app.command()
def serve(
    host: Annotated[str, typer.Option()] = "127.0.0.1",
    port: Annotated[int, typer.Option()] = 8000,
) -> None:
    uvicorn.run(api_app, host=host, port=port)


if __name__ == "__main__":
    app()
