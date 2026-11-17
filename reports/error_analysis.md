# Error Analysis and Production Classifier Decision (T3.2.4)

All numbers below come from `results/metrics.json` (keys in backticks). Gold set = 300 LLM-annotated events (`data/labels/gold_v1.csv`).

## Decision: keyword rules are the production classifier
TF-IDF + logistic regression lost to the frozen keyword baseline on macro-F1 (`clf.ml_macro_f1_all` 0.677 vs `clf.rules_macro_f1_all` 0.802; difference CI `clf.uplift_ci_all` -0.173 to -0.050). The user approved option 1 (2026-11-16): **keyword rules v1 classify the corpus** (`clf.production_method`), and the ML model is kept only for comparison (`ml_category`, `ml_confidence` columns; `models/classifier.joblib`). The ML/rules disagreement rate is used later as a label-noise sensitivity input.

Caveat: the rules and the gold labels were written by the same author (annotator A). The rules were frozen before any gold evaluation, but the shared author may favour the baseline.

## Confidence and Unclassified policy
- **No rule match -> `UNCLASSIFIED`** (method `unclassified`). These events are never forced into OTHER. On the gold set, "no match" was right only 3 of 23 times, so it means "unknown", not "other cause".
- **confidence** = gold-set precision of the event's match bucket: a single rule matched, or two or more matched and taxonomy priority broke the tie. Single-match precision is 0.913 (`clf.alt_single_match_precision_all`). Multi-match precision is lower; it is computed in `classify/final.py` and stored in the `confidence` column.

| Operating point | Precision on accepted (gold, all 300) | Coverage (gold) | Coverage (corpus) |
|---|---|---|---|
| **Accept any match (primary)** | 0.895, 95% CI 0.859-0.928 (`clf.prod_precision_accepted_all`) | 0.923 | 0.893 (`clf.corpus_coverage`) |
| Single match only (sensitivity) | 0.913 | 0.687 | ~0.70 |

On the random-200 subset, precision on accepted predictions is 0.894 (`clf.prod_precision_accepted_random`).

**Target (≥ 0.90 precision on accepted predictions): narrowly missed** at the primary operating point. 0.90 lies inside the confidence interval. Accepting only single matches would meet the target, but it would move about 20% of events (`clf.corpus_multi_match_share` 0.196) into Unclassified, a bigger distortion of the Pareto and SPC shares than 1-2 points of precision. The primary point is used downstream, and T4.1.1 compares rankings against the single-match view.

## Full corpus
`data/processed/events_classified.parquet` has one row per event (`clf.corpus_n_events` 12,687, asserted equal to the event table). The Unclassified share is 0.107 (`clf.corpus_unclassified_share`). Rules and ML agree on 0.875 of rule-accepted events (`clf.corpus_rules_ml_agreement`).

**Spot check** (informal): 30 random non-gold events (seed 7) were labeled by annotator A (LLM). 25 of the 26 rule-accepted predictions were correct (`clf.spot_check_accepted_accuracy` 0.962), and 4 of 30 were Unclassified. File: `data/labels/spot_check_30.csv`. Same annotator as the gold set, so this is not independent.

## Reviewed errors
Causes: **vocab** = vocabulary gap or false-positive keyword; **overlap** = two taxonomy categories plausibly apply; **label** = gold label debatable (possible label noise).

### 10 highest-confidence errors (single rule matched, wrong)
| event | gold | rule | cause | note |
|---|---|---|---|---|
| 67258 | MIXUP | LABELING | overlap | decaf lids/labels put on caffeinated packs: a mix-up expressed through labeling |
| 96609 | MICRO | PROCESS_SANITATION | overlap | *C. botulinum*: the rule treats botulinum as a process-control signal |
| 85181 | SPEC_FAIL | CGMP | vocab | "CGMP Deviations:" heading wins; "discoloration" is not in the SPEC_FAIL vocabulary |
| 79458 | PROCESS_SANITATION | ALLERGEN | vocab | "allergen cross contact" matches ALLERGEN, but the taxonomy sends cross-contact risk to PROCESS_SANITATION |
| 95102 | STERILITY | MICRO | overlap | "microbial contamination of sterile products" |
| 85126 | ALLERGEN | LABELING | vocab | "does not include the word milk": allergen without the word "undeclared" |
| 90090 | FOREIGN | ALLERGEN | vocab | "fish bones" triggers the fish-allergen keyword |
| 87496 | MICRO | CGMP | vocab | *B. cepacia* is not in the MICRO vocabulary |
| 72234 | MIXUP | CGMP | vocab | wrong API used; the mix-up is not stated in mix-up words |
| 69407 | ALLERGEN | PROCESS_SANITATION | vocab | "undeclared coconut" is not in the allergen list; HACCP matched instead |

### 10 lowest-confidence errors (multiple rules matched, tie-break wrong)
| event | gold | rule (matches) | cause | note |
|---|---|---|---|---|
| 62792 | LABELING | MIXUP (MIXUP, LABELING) | overlap | FDA heading "Label Mix-Up" covers a typo, not a mix-up |
| 61948 | LABELING | MIXUP (MIXUP, LABELING) | overlap | same heading pattern |
| 99355 | PROCESS_SANITATION | IMPURITY (IMPURITY, PROCESS_SANITATION) | overlap | botulinum *toxin* from ambient storage |
| 69344 | CGMP | LABELING (LABELING, CGMP) | label | GMP failure plus misbranding: two stated causes |
| 62754 | LABELING | ALLERGEN (ALLERGEN, LABELING) | overlap | false "gluten free" claim, but wheat is declared |
| 95826 | MICRO | SPEC_FAIL (SPEC_FAIL, CGMP) | overlap | OOS for micro: the guide says MICRO, but SPEC_FAIL has priority in the rules |
| 89945 | CGMP | SPEC_FAIL (SPEC_FAIL, CGMP) | vocab | "stability study program" discontinued; "stability" ≠ stability failure |
| 91616 | SPEC_FAIL | IMPURITY (IMPURITY, SPEC_FAIL) | label | FDA heading says impurities; the content is conductivity OOS |
| 88387 | PROCESS_SANITATION | SPEC_FAIL (SPEC_FAIL, PROCESS_SANITATION) | overlap | missed pasteurization specification |
| 66018 | MIXUP | ALLERGEN (ALLERGEN, MIXUP, PACKAGING) | label | walnut dough cross-contamination; ALLERGEN is defensible |

### Unclassified on gold (23 events)
Mostly vocabulary gaps: plastic or larvae without a "foreign" keyword (6 FOREIGN), certified colours without "allergen" (LABELING), "L. mono" abbreviation, histamine/scombrotoxin, "supterpotent" typo. 3 are true OTHER (choking hazard, consumer complaints, GI distress).

### Found in the full-corpus spot check
- Event 74470: `crack` in the PACKAGING rule matches "graham **crack**er" (6 corpus events labeled PACKAGING contain "cracker").

## Fixes and what was deliberately not changed
- **Rules v1 stay frozen.** Editing rules after seeing gold errors would make the gold metrics optimistic. Candidate v2 changes are listed below. They may only be adopted with a fresh holdout labeled before the change, and are not used in this project's results.
  - Word boundaries for `crack`/`seal`/`leak`; drop bare "fish" when followed by "bone".
  - Add `l\. ?mono`, `cepacia`, `histamine|scombro`, `plastic`, `larva`, `coconut`, certified colour names.
  - Route "allergen cross[- ]contact" to PROCESS_SANITATION; route "OOS ... micro" to MICRO before SPEC_FAIL.
- **Guide clarification** (logged in `docs/domain/taxonomy-change-log.md`): FDA's heading prefix ("Label Mix-Up:", "CGMP Deviations:", "Failed Impurities/Degradation Specifications:") is not decisive; label the specific failure described after it. This matches how the gold set was labeled, and no labels changed.
