from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from adaptive_calendar_agent.models import Plan, Task


class Store:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._init()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS plans (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    applied INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def upsert_task(self, task: Task) -> None:
        now = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO tasks(id, payload, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at
                """,
                (task.id, task.model_dump_json(), now),
            )

    def list_tasks(self) -> list[Task]:
        with self._connect() as connection:
            rows = connection.execute("SELECT payload FROM tasks ORDER BY updated_at").fetchall()
        return [Task.model_validate_json(row["payload"]) for row in rows]

    def save_plan(self, plan: Plan) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO plans(id, payload, applied, created_at) VALUES (?, ?, ?, ?)",
                (
                    plan.id,
                    plan.model_dump_json(),
                    int(plan.applied),
                    plan.created_at.isoformat(),
                ),
            )

    def get_plan(self, plan_id: str) -> Plan | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM plans WHERE id = ?", (plan_id,)
            ).fetchone()
        return Plan.model_validate_json(row["payload"]) if row else None

    def mark_plan_applied(self, plan: Plan) -> None:
        plan.applied = True
        self.save_plan(plan)

    def audit(self, action: str, payload: dict) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO audit_log(action, payload, created_at) VALUES (?, ?, ?)",
                (action, json.dumps(payload, default=str), datetime.now(UTC).isoformat()),
            )
