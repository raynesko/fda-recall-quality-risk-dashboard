# 7. Definition of Done

## Ticket
- [ ] Every acceptance criterion verified by running something and ticked (`scripts/tickets.py check`).
- [ ] Deliverable exists at the stated path and is committed (`<ID>: summary`).
- [ ] Code has type hints and a toy-data test with a hand-computed expected value (where code exists); `pytest -q` and `ruff check .` pass.
- [ ] Any number produced is recorded via `record_metric` with target/achieved label; no hard-coded numbers in docs.
- [ ] Unknowns/assumptions marked `UNVERIFIED` or logged; Agent log has date, decisions, hours spent.
- [ ] Status set to `done` through the CLI (which enforces dependencies and checked criteria).

## Sub-epic
- [ ] All P0 tickets done; P1 done or explicitly cut with a note in the milestone plan.
- [ ] Exit criterion in `docs/02-epic-breakdown.md` demonstrably true (demo run or output shown).
- [ ] Outputs regenerate from raw data with one command sequence (no manual steps).
- [ ] Limitations discovered are appended to the methodology doc draft.

## Project
- [ ] Clean-environment run: install -> `run_pipeline.py` -> reports regenerate; `pytest -q` green.
- [ ] Targets M1-M9 each marked **met / missed** with the achieved value; misses explained, not hidden.
- [ ] Dashboard (4 pages) reconciles to Python; PDF + screenshots exported; usability test logged.
- [ ] README complete per outline; methodology and limitations document finished; no secrets or raw data committed.
- [ ] Resume bullets/pitch/slides/Q&A contain only numbers printed by `resume_numbers.py`; no placeholders left.
- [ ] A non-technical reviewer can state the project's question, main finding and one limitation after 5 minutes.
