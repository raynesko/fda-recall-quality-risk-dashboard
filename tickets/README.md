# Tickets - how humans and agents use this backlog

**Hierarchy:** `EPIC-1` -> sub-epics `SE1..SE7` -> stories `S<se>.<n>` (defined in `docs/02-epic-breakdown.md` and quoted in each ticket) -> executable tickets `T<se>.<story>.<n>` (Task | Spike | Story). One file per ticket in `tickets/SE*/`.

**Source of truth:** the ticket files. `INDEX.md` and `tickets.csv` are generated (`python scripts/tickets.py index`). `tickets.csv` imports into Jira, Linear, Notion or GitHub Projects (columns: ID, Title, Type, Epic, Sub-epic, Story, Priority, Estimate, Size, Week, Status, Depends on, Deliverable, Description, Acceptance criteria).

## Frontmatter
`id, title, type, epic, sub_epic, story, priority (P0|P1|P2), estimate_hours, size (S<=2h, M<=4h, L>4h), week, status (todo|in_progress|done|blocked), depends_on, deliverable`

## Agent protocol
1. `python scripts/tickets.py next` -> returns the first unblocked core ticket (ordered by week, then priority). P2 stretch tickets are never auto-selected.
2. Read the ticket + the docs it names. Confirm all `depends_on` are `done`.
3. `python scripts/tickets.py set <ID> in_progress`.
4. Do exactly what the acceptance criteria require. Each criterion must be checked by running something (test, script, query) - not by inspection.
5. Tick each verified criterion: `python scripts/tickets.py check <ID> <n>`. `set done` refuses while any criterion is unchecked or a dependency is unfinished.
6. Record numbers via `record_metric`, never by typing them into docs.
7. Append to `## Agent log` (date, what was decided, time spent, surprises). Spikes: stop at the time box.
8. Commit with message `<ID>: <summary>`.

## Priority meaning
- **P0** critical path or required for the resume story. **P1** strengthens rigor; cut first if time runs short (order: T4.2.3, T6.1.6, T5.1.3, T3.1.3). **P2** stretch, only after P0/P1 are done.

## Size/estimate
Hours are focused-work estimates for a solo student engineer (target ~8-10 h/week). Core total and per-week loads are in `docs/04-milestone-plan.md`.
