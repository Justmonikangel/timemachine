# Roadmap

## V0.1 — Safe automatic focus-block scheduling

- [x] Google Calendar OAuth adapter
- [x] protected/deadline/focus calendar roles
- [x] bilingual deterministic commands
- [x] task scheduler with capacity and energy rules
- [x] preview/apply workflow
- [x] optional faster-whisper file transcription
- [x] SQLite persistence
- [x] tests and CI

## V0.2 — Real voice commands and safer event skipping

- [ ] push-to-talk desktop/mobile client
- [ ] identify matching personal events by fuzzy title
- [ ] preview exact recurring-event scope
- [ ] reversible skip operation for one occurrence
- [ ] undo applied calendar plan
- [ ] deadline-to-task templates with mandatory review
- [ ] explicit low-energy mode

## V0.3 — Deadline automation

- [ ] read deadline calendar markers
- [ ] screenshot/PDF assessment extraction
- [ ] Gmail deadline-change detector
- [ ] source confidence and verification state
- [ ] backward planning templates
- [ ] duplicated/deleted deadline reconciliation

## V0.4 — LLM intent parser

- [ ] provider-neutral interface
- [ ] OpenAI adapter
- [ ] Anthropic adapter
- [ ] strict JSON schema
- [ ] golden-set intent tests
- [ ] adversarial date and recurrence tests
- [ ] deterministic fallback

## V0.5 — FluidCalendar integration

- [ ] import/export compatible task representation
- [ ] scheduler policy plugin or sidecar
- [ ] preserve FluidCalendar-owned data
- [ ] compare scheduler decisions in evaluation harness

## Release gate

No feature may silently modify a protected calendar. Destructive recurring-series operations require exact event identification and explicit user confirmation.
