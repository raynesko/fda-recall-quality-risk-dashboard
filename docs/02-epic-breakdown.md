# 2. Epic Breakdown

**EPIC-1: FDA Recall & Quality Risk Intelligence Dashboard** - from openFDA recall data to a DMAIC-framed, backtested quality-risk dashboard a QA reviewer can use.

Build order follows the dependency chain; the baseline-and-validation work is embedded in SE3 (classifier baseline), SE4 (SPC validation) and SE5 (risk-score backtest) rather than isolated at the end, so every model is validated when built.

| Sub-epic | Name | Weeks | Core hours | Exit criterion |
|---|---|---|---|---|
| SE1 | Domain Research & Problem Framing | 1 | 6.0 | Primer, taxonomy v1, DMAIC mapping, metric dictionary exist and cite sources |
| SE2 | Data Acquisition & Modeling | 1-2 | 11.5 | Raw->clean->star schema rebuilds from source; data-quality report published |
| SE3 | Root-Cause Classification (NLP) | 3-4 | 14.0 | Gold set + kappa; ML vs baseline with CIs; full corpus classified with a confidence rule |
| SE4 | Pareto, Trend & Control-Chart Analysis | 4-5 | 8.0 | Pareto, validated SPC with signals, trend tests |
| SE5 | Risk Scoring & Backtest Validation | 5-6 | 8.5 | Pre-registered score, backtest vs 3 baselines, sensitivity analysis |
| SE6 | Dashboard & DMAIC Recommendations | 3, 6-7 | 11.5 | 4-page dashboard reconciled to Python; QA action library; usability test |
| SE7 | Documentation & Portfolio Packaging | 7-8 | 8.0 | README, methodology, reproducible run, resume assets from verified numbers |

Core total 67.5 h (+ 7 h P2 stretch). Ticket-level detail: `tickets/INDEX.md`.

## Stories (each ticket in `tickets/` quotes its story)

| Story | Statement | Tickets |
|---|---|---|
| S1.1 | As a quality analyst reviewer, I want recall root causes and the DMAIC framing grounded in FDA/GMP concepts, so that the analysis uses the language of QA and is defensible. | T1.1.1, T1.1.2, T1.1.3 |
| S2.1 | As an analyst, I want a reproducible ingestion and cleaning pipeline from openFDA, so that anyone can rebuild the dataset from source and trust the counts. | T2.1.1, T2.1.2, T2.1.3 |
| S2.2 | As a BI developer, I want an analytics-ready star schema with a data dictionary, so that dashboard measures are consistent and fast. | T2.2.1 |
| S2.3 (P2) | As a regulatory data analyst, I want adverse-event context next to recall findings, so that I can see reporting activity without implying causation. | T2.3.1, T2.3.2 |
| S3.1 | As an analyst, I want an LLM-annotated, agreement-checked gold set, so that classifier accuracy is measurable rather than asserted. | T3.1.1, T3.1.2, T3.1.3 |
| S3.2 | As an analyst, I want an NLP classifier that demonstrably beats a keyword baseline, so that every recall gets a root-cause category with known accuracy. | T3.2.1-T3.2.4 |
| S4.1 | As a QA manager, I want a Pareto view of root causes, so that I can focus on the vital few. | T4.1.1 |
| S4.2 | As a QA manager, I want control charts and trend tests by category, so that I can separate special-cause from common-cause variation. | T4.2.1-T4.2.3 |
| S5.1 | As a QA lead, I want a transparent, backtested risk score that flags rising failure modes, so that I can trust or challenge its flags. | T5.1.1-T5.1.3 |
| S6.1 | As a non-technical reviewer, I want a dashboard I can understand in five minutes. | T6.1.1-T6.1.6 |
| S6.2 | As a QA lead, I want flagged failure modes translated into DMAIC-framed QA actions. | T6.2.1 |
| S7.1 | As a hiring manager, I want a clear README and a repo that reproduces end-to-end. | T7.1.1-T7.1.3 |
| S7.2 | As the candidate, I want resume bullets, pitch, slides and interview points built only from verified results. | T7.2.1, T7.2.2 |

## Ticket catalogue
The 35 tickets (Tasks, Spikes, Stories) with description, acceptance criteria, dependencies, estimate, priority and deliverable live as individual files in `tickets/SE*/` and as `tickets/tickets.csv` (tracker import). Spike tickets with time boxes: T1.1.1 (2.5 h), T2.1.1 (1.5 h), T6.1.1 (1 h), T2.3.1 (1.5 h, stretch).
