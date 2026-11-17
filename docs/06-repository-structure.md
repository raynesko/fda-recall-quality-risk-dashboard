# 6. Repository & Documentation Structure

```
fda-recall-quality-risk-dashboard/
├── CLAUDE.md                  agent instructions + hard rules
├── README.md                  (created in T7.1.1)
├── requirements.txt           floor versions now; pinned in T7.1.3
├── .gitignore
├── .claude/commands/          slash commands (next-ticket)
├── tickets/                   backlog: SE1..SE7 folders, INDEX.md, tickets.csv, README.md
├── scripts/                   tickets.py (backlog CLI); run_pipeline.py, resume_numbers.py (T7.1.3)
├── src/fda_recall/            ingest.py clean.py model.py metrics.py
│   ├── classify/              rules.py model.py embed.py(stretch)
│   ├── analysis/              pareto.py series.py spc.py trend.py
│   ├── risk/                  score.py backtest.py sensitivity.py
│   └── labeling/              sample.py
├── tests/                     test_<module>.py (mirrors src)
├── notebooks/                 NN_topic.ipynb (narrative only)
├── data/
│   ├── raw/                   immutable downloads + manifest.json
│   ├── interim/               scratch (ignored)
│   ├── processed/             parquet outputs, star/ for BI
│   ├── reference/             taxonomy.yaml, keyword_rules.yaml, qa_action_library.csv
│   └── labels/                gold_v1.csv, gold_v1_relabel.csv
├── models/                    classifier.joblib (ignored)
├── reports/                   figures/, tables/, *.md (generated)
├── results/metrics.json       single source of published numbers
├── dashboard/                 fda_recall_dashboard.pbix
└── docs/
    ├── 01-project-charter.md ... 09-risks-and-open-questions.md   (planning set)
    ├── domain/                primer, taxonomy, glossary, DMAIC framing, metric dictionary, labeling guide
    ├── data/                  openfda-source-notes.md, data-dictionary.md
    ├── methodology/           time-series.md, risk-score.md, methodology-and-limitations.md
    ├── dashboard/             bi-tool-decision, reconciliation, usability-log, pdf, screens/
    └── portfolio/             resume-bullets, pitch, slides outline, interview Q&A (T7.2.1)
```

## README outline (T7.1.1)
1. **Title + one-line value statement + dashboard screenshot**
2. **Problem** - why QA teams care; what the data is; what question is answered
3. **Method** - pipeline diagram; taxonomy; classifier and baseline; Pareto; SPC; risk score; DMAIC mapping
4. **Results** - 3 headline numbers (from metrics.json), classifier table, Pareto chart, control-chart example, backtest outcome (including misses), dashboard pages
5. **How to run** - venv, install, `scripts/run_pipeline.py`, open the .pbix / view PDF
6. **Assumptions** - data scope, date definition, severity weights, taxonomy
7. **Limitations** - no denominator, FDA-classification bias, LLM-produced labels, small-n backtest, USDA-FSIS excluded, not for decisions
8. **Repo map, data sources and citations, license, disclaimer**

## Naming conventions
- Tickets `T<se>.<story>.<n>`; stories `S<se>.<n>`; sub-epics `SE1..SE7`; epic `EPIC-1`.
- Python `snake_case`; modules mirror tests (`spc.py` <-> `test_spc.py`).
- Data `<entity>_<grain>.parquet` (e.g., `recalls_event.parquet`); figures `<topic>_<scope>.png`; metric keys `<area>.<name>` (e.g., `clf.macro_f1`).
- Commits `T2.1.2: short summary`.

## Requirements file plan
- `requirements.txt` (core, floor versions now -> exact pins at T7.1.3 via `pip freeze` in a clean venv).
- Optional `requirements-extras.txt` for stretch libraries (sentence-transformers) so the core install stays light.
- No GPU requirement; no paid services; Power BI Desktop / Tableau Public are separate installs documented in README.
