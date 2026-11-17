# Taxonomy Change Log

## v1 -> v1.1 (T3.1.1, 2026-11-16) - evidence from notebooks/03_text_eda.ipynb
Taxonomy categories unchanged (14). Example phrases and one decision rule added:

| Change | Evidence (event counts from EDA) |
|---|---|
| SPEC_FAIL example "failed tablet/capsule specifications" | 83 drug events start with "failed tablet/capsul" |
| IMPURITY example "chemical contamination" | 61 drug events start with "chemical contaminati" |
| LABELING example "labeling: not elsewhere classified" | 65 drug events start with "labeling: not elsewh" |
| **Decision:** FDA's "Labeling: Label Mix-up" -> **MIXUP**, not LABELING (wrong label on product = mix-up hazard; MIXUP precedes LABELING in tie-break) | 88 drug events start with "labeling: label mix-" |
| **Labeling rule (no taxonomy change):** food texts often begin with a preamble ("the firm was notified by their supplier/customer that ...") - classify by the hazard stated after the preamble | 135 + 47 food events start with this preamble |

Other observations (no change): drug text is formulaic (FDA-style "Category: detail" prefixes; 26% near-duplicate rate after stripping digits/punctuation), food text is free-form (18% near-duplicate rate). Literal taxonomy example phrases hit 73% of drug events but only 13% of food events, so the keyword baseline (T3.2.1) needs pattern rules (e.g., `listeria|salmonella`, `undeclared (milk|egg|...)`), not exact phrases.

## 2026-11-16 - T3.2.4 error analysis (no taxonomy version change)
- **Guide clarification:** FDA heading prefixes ("Label Mix-Up:", "CGMP Deviations:", "Failed Impurities/Degradation Specifications:") are not decisive; label the specific failure described after them. Consistent with how gold_v1 was labeled; no labels changed.
- **Production policy:** events with no keyword-rule match are `UNCLASSIFIED` (a dim_category row, not a taxonomy category); rules never assign OTHER.
- Keyword rules v1 stay frozen. Candidate v2 rule fixes are listed in `reports/error_analysis.md` and are not used for any reported result.
