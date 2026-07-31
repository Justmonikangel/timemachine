from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from adaptive_calendar_agent.config import load_settings
from adaptive_calendar_agent.google_calendar import GoogleCalendarAdapter
from adaptive_calendar_agent.service import CalendarAgentService
from adaptive_calendar_agent.store import Store
from adaptive_calendar_agent.voice import transcribe


class CommandBody(BaseModel):
    text: str


class ReplanBody(BaseModel):
    horizon_days: int | None = None


def build_service() -> CalendarAgentService:
    settings = load_settings()
    store = Store(settings.db_path)
    calendar = GoogleCalendarAdapter(settings)
    return CalendarAgentService(settings, store, calendar)


app = FastAPI(title="Adaptive Calendar Agent", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}


@app.post("/commands/preview")
def preview_command(body: CommandBody) -> dict:
    try:
        return build_service().preview_command(body.text).model_dump(mode="json")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/plans/replan")
def preview_replan(body: ReplanBody) -> dict:
    try:
        return build_service().preview_replan(body.horizon_days).model_dump(mode="json")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/plans/{plan_id}/apply")
def apply_plan(plan_id: str) -> dict:
    try:
        return build_service().apply_plan(plan_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/voice/preview")
async def voice_preview(audio: Annotated[UploadFile, File()]) -> dict:
    service = build_service()
    suffix = Path(audio.filename or "voice.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(await audio.read())
        path = Path(handle.name)
    try:
        text = transcribe(path, service.settings.voice)
        plan = service.preview_command(text)
        return {"transcript": text, "plan": plan.model_dump(mode="json")}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        path.unlink(missing_ok=True)
