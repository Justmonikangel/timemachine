# Adaptive Calendar Agent

An open-source, local-first calendar agent for people who need **structured flexibility**.

It treats fixed classes, appointments, and deadlines as protected constraints, then schedules flexible tasks around them using explicit rules for capacity, energy, buffers, and unfinished work.

## What V0.1 does

- Connects to Google Calendar through local OAuth.
- Protects configured calendars such as `Monash class` and assessment calendars.
- Accepts Chinese or English text commands.
- Optionally transcribes an uploaded audio file with `faster-whisper`.
- Builds a preview plan before any calendar mutation.
- Creates only agent-managed focus blocks.
- Refuses to modify protected calendars.
- Stores tasks, plans, and audit records in SQLite.
- Uses an ADHD-oriented scheduling policy:
  - schedule at most 70% of theoretical free time;
  - no more than two high-energy blocks per day;
  - add transition buffers;
  - split large tasks into smaller blocks;
  - stop endlessly rolling over repeatedly missed work.

## Non-goals for V0.1

- No always-listening wake word.
- No direct Moodle scraping.
- No silent deletion of third-party calendar events.
- No LLM is required for supported commands.
- No claim that the scheduler can infer medical needs.

## Safety model

The agent follows a two-stage write flow:

1. `preview` creates a plan and shows intended changes.
2. `apply PLAN_ID` writes the reviewed plan.

By default, only events carrying the private Google Calendar property `aca_managed=true` may be deleted or rescheduled automatically.

## Quick start

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

For local voice transcription:

```bash
pip install -e '.[voice,dev]'
```

### 2. Configure

```bash
cp config/policy.example.yaml policy.yaml
cp .env.example .env
```

Edit `policy.yaml` so the protected calendar names match your Google Calendar names.

### 3. Configure Google OAuth

Create a Google Cloud project, enable the Google Calendar API, create a Desktop OAuth client, and save the downloaded file as:

```text
.secrets/credentials.json
```

Then run:

```bash
aca auth
```

The first authorization creates `.secrets/token.json` locally. Neither file should be committed.

### 4. Inspect calendars

```bash
aca calendars
```

### 5. Add flexible tasks

```bash
aca add-task \
  --title 'CS61A recursion exercises' \
  --duration 120 \
  --deadline '2026-08-09 18:00' \
  --energy high \
  --priority 4 \
  --project cs61a
```

### 6. Preview and apply a schedule

```bash
aca replan --days 14
aca apply PLAN_ID
```

### 7. Preview a natural-language command

```bash
aca preview '这周先不上 gym 的课了'
aca preview 'replan the next two weeks'
```

V0.1 recognises a small deterministic command set. Unsupported commands return `unknown` rather than guessing.

### 8. Voice file

```bash
aca voice-preview recording.m4a
```

### 9. API

```bash
aca serve
```

Then open `http://127.0.0.1:8000/docs`.

## Calendar roles

Configure three roles in `policy.yaml`:

- `protected`: classes, official assessments, medical appointments, shared meetings.
- `deadline`: deadline markers; these constrain scheduling but should not consume the whole day.
- `focus`: the calendar where agent-managed work blocks are created.

## Supported V0.1 command examples

```text
这周先不上 gym 的课了
这周暂停 gym
skip gym this week
replan the next 14 days
重新安排未来两周
```

A skip command is only executable when the matching event is on a non-protected calendar. The initial implementation records the request and triggers replanning; it does not silently delete protected or shared events.

## Project structure

```text
src/adaptive_calendar_agent/
  api.py              FastAPI endpoints
  cli.py              Typer CLI
  config.py           YAML and environment configuration
  google_calendar.py  Google Calendar adapter and safety checks
  models.py           Typed domain models
  parser.py           Deterministic bilingual command parser
  scheduler.py        Rule-based scheduling engine
  service.py          Preview/apply orchestration
  store.py            SQLite persistence and audit log
  voice.py            Optional faster-whisper adapter
```

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

MIT. See [LICENSE](LICENSE).
