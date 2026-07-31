from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from adaptive_calendar_agent.config import Settings
from adaptive_calendar_agent.models import CalendarEvent, PlannedBlock

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarAdapter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._service = None

    def authenticate(self) -> None:
        credentials: Credentials | None = None
        token_path = self.settings.token_path
        credentials_path = self.settings.credentials_path
        token_path.parent.mkdir(parents=True, exist_ok=True)

        if token_path.exists():
            credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        if not credentials or not credentials.valid:
            if not credentials_path.exists():
                raise FileNotFoundError(
                    f"Google OAuth credentials not found: {credentials_path}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            credentials = flow.run_local_server(port=0)
            token_path.write_text(credentials.to_json(), encoding="utf-8")
        self._service = build("calendar", "v3", credentials=credentials)

    @property
    def service(self):
        if self._service is None:
            self.authenticate()
        return self._service

    def list_calendars(self) -> list[dict]:
        items: list[dict] = []
        token = None
        while True:
            result = self.service.calendarList().list(pageToken=token).execute()
            items.extend(result.get("items", []))
            token = result.get("nextPageToken")
            if not token:
                break
        return items

    def calendar_id_by_name(self, name: str) -> str | None:
        for calendar in self.list_calendars():
            if calendar.get("summary") == name:
                return calendar["id"]
        return None

    def ensure_focus_calendar(self) -> str:
        existing = self.calendar_id_by_name(self.settings.focus_calendar_name)
        if existing:
            return existing
        created = self.service.calendars().insert(
            body={"summary": self.settings.focus_calendar_name, "timeZone": self.settings.timezone}
        ).execute()
        return created["id"]

    def list_events(self, start: datetime, end: datetime) -> list[CalendarEvent]:
        tz = ZoneInfo(self.settings.timezone)
        calendars = self.list_calendars()
        result_events: list[CalendarEvent] = []
        for calendar in calendars:
            calendar_id = calendar["id"]
            name = calendar.get("summary", calendar_id)
            token = None
            while True:
                response = (
                    self.service.events()
                    .list(
                        calendarId=calendar_id,
                        timeMin=start.isoformat(),
                        timeMax=end.isoformat(),
                        singleEvents=True,
                        orderBy="startTime",
                        pageToken=token,
                    )
                    .execute()
                )
                for event in response.get("items", []):
                    start_raw = event.get("start", {})
                    end_raw = event.get("end", {})
                    if "dateTime" not in start_raw:
                        continue
                    event_start = datetime.fromisoformat(start_raw["dateTime"]).astimezone(tz)
                    event_end = datetime.fromisoformat(end_raw["dateTime"]).astimezone(tz)
                    private = event.get("extendedProperties", {}).get("private", {})
                    result_events.append(
                        CalendarEvent(
                            id=event["id"],
                            calendar_id=calendar_id,
                            calendar_name=name,
                            title=event.get("summary", "Untitled event"),
                            start=event_start,
                            end=event_end,
                            protected=name in self.settings.protected_calendar_names,
                            deadline_marker=name in self.settings.deadline_calendar_names,
                            managed=private.get("aca_managed") == "true",
                            recurring_event_id=event.get("recurringEventId"),
                        )
                    )
                token = response.get("nextPageToken")
                if not token:
                    break
        return result_events

    def delete_managed_focus_blocks(self, start: datetime, end: datetime) -> int:
        focus_id = self.ensure_focus_calendar()
        response = (
            self.service.events()
            .list(
                calendarId=focus_id,
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        deleted = 0
        for event in response.get("items", []):
            private = event.get("extendedProperties", {}).get("private", {})
            if private.get("aca_managed") != "true":
                continue
            self.service.events().delete(calendarId=focus_id, eventId=event["id"]).execute()
            deleted += 1
        return deleted

    def create_focus_block(self, block: PlannedBlock, plan_id: str) -> str:
        focus_id = self.ensure_focus_calendar()
        body = {
            "summary": f"Focus: {block.task_title}",
            "start": {"dateTime": block.start.isoformat(), "timeZone": self.settings.timezone},
            "end": {"dateTime": block.end.isoformat(), "timeZone": self.settings.timezone},
            "description": (
                f"Managed by Adaptive Calendar Agent. Project: {block.project}. "
                f"Energy: {block.energy.value}."
            ),
            "extendedProperties": {
                "private": {
                    "aca_managed": "true",
                    "aca_plan_id": plan_id,
                    "aca_task_id": block.task_id,
                }
            },
            "transparency": "opaque",
        }
        created = self.service.events().insert(calendarId=focus_id, body=body).execute()
        return created["id"]
