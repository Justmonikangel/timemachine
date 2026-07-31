# Architecture

## Trust boundary

Calendar source data is separated into three roles:

1. **Protected calendars** — read-only constraints.
2. **Deadline calendars** — temporal anchors; not treated as full busy blocks.
3. **Focus calendar** — the only calendar the agent may automatically rewrite.

## Command path

```text
Text or audio file
        ↓
Deterministic bilingual parser
        ↓
Typed command intent
        ↓
Preview plan persisted in SQLite
        ↓
Explicit apply
        ↓
Google Calendar adapter
        ↓
Agent-managed focus blocks only
```

## Why deterministic parsing first

V0.1 supports a narrow command grammar and returns `unknown` outside it. This prevents a language model from inventing calendar targets, dates, or destructive mutations. An optional LLM parser can be added behind the same typed interface after a golden-set evaluation is available.

## Scheduler

The initial scheduler is a transparent greedy scorer. It favours:

- deadlines approaching sooner;
- higher priority tasks;
- energy-compatible time windows;
- earlier completion;
- capacity and deep-work limits.

The algorithm is intentionally inspectable. More sophisticated optimisation can be introduced later without changing the calendar safety boundary.

## Data model

SQLite stores:

- flexible tasks;
- preview plans;
- application state;
- audit records.

OAuth secrets remain local and are excluded by `.gitignore`.
