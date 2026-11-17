# CLAUDE.md - FDA Recall & Quality Risk Dashboard

Portfolio project for a student targeting NJ food/pharma **quality analyst, QA/QC, regulatory data analyst** roles (not software roles). Credibility with a QA hiring manager matters more than engineering polish.

**What it is:** a quality-risk intelligence pipeline + Power BI dashboard on openFDA drug and food **enforcement (recall)** data. NLP classifies `reason_for_recall` into root-cause categories; Pareto, control charts (SPC) and trend tests describe recall activity; a transparent risk score flags rising failure modes and is **backtested** against naive baselines; everything is framed in **DMAIC** with recommended QA actions.

## Start here
1. Read `docs/01-project-charter.md` (scope, non-goals, targets) and `docs/domain/metric-dictionary.md` once it exists.
2. Find work: `python scripts/tickets.py next` (stdlib only; run from repo root).
3. Open the ticket file it prints (`tickets/SE*/T*.md`). The ticket is the spec: description, testable acceptance criteria, dependencies, deliverable.
4. `python scripts/tickets.py set <ID> in_progress` -> do the work -> verify each criterion by actually running it -> `python scripts/tickets.py check <ID> <n>` per criterion -> `python scripts/tickets.py set <ID> done`.
5. Append decisions, blockers and time spent to the ticket's `## Agent log`.

Full protocol: `tickets/README.md`. Other tools: `/next-ticket` slash command (`.claude/commands/`). Definition of Done: `docs/07-definition-of-done.md`.

## Hard rules (non-negotiable)
- **Never fabricate numbers, record counts, dataset facts or regulatory citations.** Anything not verified from a live source or a script run is written `UNVERIFIED`. Prefer asking the user over guessing.
- **Targets are not results.** Every target in docs/tickets is a goal with a justification. A number may be called "achieved" only if it was produced by code and recorded via `fda_recall.metrics.record_metric` into `results/metrics.json`. README, slides and resume text may only use numbers from that file. If a target is missed, report it plainly; do not tune until it passes.
- **Raw data is immutable.** `data/raw/` is write-once, gitignored (manifest tracked). All transforms are code in `src/`, rerunnable from raw.
- **No proprietary/confidential data.** openFDA public data only (plus clearly documented synthetic data if ever added).
- **No leakage.** Backtests use only data available at the origin date. Classifier CV is grouped by recalling firm. Keyword baseline rules are written from taxonomy + EDA, never from gold labels.
- **Pre-register before you evaluate.** The risk-score definition and success criteria (T5.1.1) are committed before the backtest (T5.1.2) runs.
- **No causal or firm-level accusations.** Dashboard text describes category-level patterns in FDA-recorded recall events. Adverse-event data (if used) is context only, never evidence a recall caused harm.
- **Do not skip dependencies or time boxes.** Spikes stop at their time box; log what is unknown.
- Do not expand scope beyond the charter non-goals (no devices, no USDA-FSIS, no prediction of individual recalls, no deep-learning models) without a recorded user decision in `docs/09-risks-and-open-questions.md`.

## Domain cautions (get these right)
- A **recall event** (`event_id`) can contain many **product** rows (`recall_number`). Count at event level unless a ticket says otherwise; always state the grain.
- Counts are **events per month, not rates** - there is no production-volume denominator. Never call them "failure rates".
- Month = `report_date` by default (when FDA posted it); `recall_initiation_date` is the sensitivity alternative and has reporting lag.
- Classification (Class I/II/III) is assigned by FDA by health hazard; severity weights are ordinal and arbitrary - always show a sensitivity check.
- openFDA enforcement data excludes USDA-FSIS (meat/poultry/egg) recalls - do not describe it as "all US food recalls".
- Use QA terms precisely: correction vs corrective action vs CAPA; OOS; cGMP; HACCP/HARPC.

## Stack and layout
Python 3.12 on Windows (PowerShell/Git Bash). pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, pyarrow, duckdb, pytest. Power BI Desktop (free) for the dashboard unless T6.1.1 decides Tableau Public. Free/open-source only.
```
src/fda_recall/   package (ingest, clean, model, metrics, classify/, analysis/, risk/, labeling/)
tests/            pytest; no network in tests
data/             raw (immutable) | interim | processed | reference (taxonomy, rules, action library) | labels (gold set)
reports/          generated figures + tables + markdown reports (reproducible)
results/          metrics.json  <- single source of every published number
dashboard/        .pbix and exports
docs/             charter, plan, methodology, domain, dashboard docs
tickets/          the backlog (one file per ticket) + INDEX.md + tickets.csv
```
Layout details: `docs/06-repository-structure.md`.

## Commands
```
python -m venv .venv && .venv\Scripts\activate && pip install -e .   (installs requirements.txt + the fda_recall package)
pytest -q
python -m fda_recall.ingest --endpoint drug food     # after T2.1.2
python scripts/tickets.py list --week 3
python scripts/tickets.py index                        # regenerate INDEX.md + tickets.csv
python scripts/run_pipeline.py [--download]            # full pipeline, 17 steps, ~4 min; all outputs + metrics
python scripts/resume_numbers.py                       # every published number with its metrics key
python -m fda_recall.pbip                              # regenerate dashboard/FDA_Recall_Dashboard.pbip
python scripts/validate_pbir.py                        # PBIR JSON vs Microsoft schemas
powershell -File scripts\validate_tmdl.ps1             # TMDL parse via Power BI's TOM
```
Dashboard fixes go in `src/fda_recall/pbip.py` / `dashboard.py` (generated files are overwritten), then re-validate.
(Commands marked "after Txxx" do not exist until that ticket is done.)

## Conventions
- Python: type hints, small pure functions, seeded randomness (`seed=42` default, recorded), `ruff` formatting. Every analysis function has a toy-data unit test with a hand-computed answer.
- Files: `snake_case.py`; data `lowercase_snake.parquet`; figures `<topic>_<scope>.png`; notebooks numbered `NN_topic.ipynb` and must Restart-&-Run-All clean (logic lives in `src/`, notebooks only narrate).
- Commits: one ticket per commit/PR where possible; message `T2.1.2: <summary>`; end with the attribution line required by the session.
- Charts: label axes and units, title states the takeaway, no color-only encoding, state data-as-of date.
- Do not edit `tickets/INDEX.md` or `tickets.csv` by hand (generated). Do edit ticket frontmatter only through `scripts/tickets.py`.

## When blocked
Mark `blocked`, write the reason in the ticket's Agent log, and pick the next unblocked ticket. Questions for the user go to the bottom of `docs/09-risks-and-open-questions.md` with your default assumption.
