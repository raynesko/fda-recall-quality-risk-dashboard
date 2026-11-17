# Labeling Guide - gold set v1 (T3.1.2)

## How to label
```
.venv\Scripts\activate
python -m fda_recall.labeling.label        # resumable; q to quit, progress saved after every answer
```
- Read the **whole** reason text. Pick the category whose *include* rule fits (`docs/domain/root-cause-taxonomy.md`). If more than one fits, the tie-break order decides; record the runner-up as `secondary_label`.
- Label **blind**: do not look at any classifier output, keyword rule hits, or the `source` column before finishing. The tool hides them.
- Do not change the taxonomy mid-labeling. If a case is genuinely ambiguous, decide, add it to the edge-case table below, and keep going. Re-check earlier labels of the same pattern at the end.
- Time is logged automatically to `data/labels/labeling_time.log`.

Tie-break: ALLERGEN > STERILITY > MICRO > IMPURITY > UNAPPROVED > FOREIGN > MIXUP > POTENCY > SPEC_FAIL > PACKAGING > PROCESS_SANITATION > LABELING > CGMP > OTHER

## Sampling design
`python -m fda_recall.labeling.sample --seed 42` -> 300 events (event_id hash `991249120590f5eb3fc13c6eb68a40cc493de8cb5920fe5e804296ec9ac669c3`):
- 200 random, stratified by product type x report-year bucket (2012-15, 2016-19, 2020-22, 2023-26), proportional allocation -> 74 drug / 126 food.
- 100 targeted, drawn with broad search patterns (one per category) to give rare categories enough examples -> 63 drug / 37 food.
- **Not prevalence-representative.** Never use the gold set to estimate category shares. Classifier metrics are reported on all 300 and on the random-200 subset (targeted draws were found with keywords, which could favour the keyword baseline).

## Decided edge cases (>= 20)
| # | Pattern | Label | Why |
|---|---|---|---|
| 1 | "Undeclared milk" caused by wrong label applied | ALLERGEN (secondary MIXUP) | Consumer hazard is the allergen |
| 2 | "Undeclared sildenafil/tadalafil" in a supplement | UNAPPROVED | "Undeclared" a drug, not an allergen |
| 3 | "Undeclared sulfites" / "FD&C Yellow No. 5" | ALLERGEN | Design choice (see taxonomy caveat) |
| 4 | "May contain undeclared allergen" because shared line, no allergen confirmed | ALLERGEN | Text states undeclared allergen risk |
| 5 | Allergen cross-contact risk stated as a sanitation failure without "undeclared" | PROCESS_SANITATION | No undeclared declaration stated |
| 6 | "Lack of assurance of sterility" + "marketed without approved NDA" | STERILITY (secondary UNAPPROVED) | Patient hazard first |
| 7 | "Microbial contamination of non-sterile products" | MICRO | Non-sterile |
| 8 | Sterile injectable with bacteria found | STERILITY | Sterile product failure |
| 9 | "Prepared/packed/held under insanitary conditions" with no organism named | PROCESS_SANITATION | No specific contaminant |
| 10 | Insanitary conditions + Listeria found in environment | MICRO | Organism named |
| 11 | "Potential C. botulinum" due to under-processing / missing HACCP/acidification | PROCESS_SANITATION | Process failure; organism not detected |
| 12 | "CGMP deviations: presence of NDMA / nitrosamine" | IMPURITY | Specific impurity |
| 13 | "CGMP deviations" alone or with only procedural detail | CGMP | Nothing more specific |
| 14 | "Failed impurities/degradation specifications" | IMPURITY | Degradant = impurity |
| 15 | "Subpotent" / "Superpotent" / "failed assay" (even if found on stability) | POTENCY | Assay beats stability |
| 16 | "Failed dissolution" / "failed stability" (assay not mentioned) | SPEC_FAIL | |
| 17 | "Failed tablet/capsule specifications" (weight, hardness, appearance) | SPEC_FAIL | Physical attribute OOS |
| 18 | "Presence of particulate matter" / glass / metal / plastic | FOREIGN | Physical matter |
| 19 | "Presence of foreign tablets/capsules" (another product) | MIXUP | Wrong product, not debris |
| 20 | "Labeling: label mix-up" (wrong label on product) | MIXUP | Decision in taxonomy v1.1 |
| 21 | "Labeling: incorrect or missing lot and/or exp date" | LABELING | |
| 22 | "Defective container" / "defective delivery system" / leaking / seal failure | PACKAGING | |
| 23 | Temperature excursion during storage/shipping | PROCESS_SANITATION | Storage control |
| 24 | Elevated lead / arsenic / aflatoxin / pesticide | IMPURITY | Chemical contaminant |
| 25 | "Recall initiated as a precautionary measure" with no hazard named | OTHER | Too vague |
| 26 | Preamble "the firm was notified by its supplier that..." | label the hazard after the preamble | Preamble is not the reason |
| 27 | Supplier ingredient recalled for Salmonella, product not tested | MICRO | Organism named as hazard |
| 28 | "Marketed without an approved NDA/ANDA" only | UNAPPROVED | Regulatory status |

| 29 | Undeclared NON-allergen ingredient (colors other than Yellow 5, preservatives, flaxseed, malic acid) with no mix-up | LABELING | Not in ALLERGEN scope |
| 30 | FDA heading "Label Mix-up" but text describes a label TEXT error (typo, mismatched statement) rather than a wrong label on product | LABELING | Content beats FDA heading |
| 31 | Insects, larvae, hair, bones, animal droppings FOUND in product | FOREIGN | Physical matter found; "insanitary conditions/filth" without a finding stays PROCESS_SANITATION |
| 32 | Histamine / scombrotoxin | IMPURITY | Chemical hazard named |
| 33 | Leak/breakage/crimp failure that causes "lack of assurance of sterility" | STERILITY (secondary PACKAGING) | Tie-break; this is why PACKAGING is rare |
| 34 | Excess nutrient (e.g., selenium, vitamin overage) | POTENCY | Content out of target |
| 35 | Spoilage signs (bubbling, sour taste) | MICRO | Implies microbial growth |
| 36 | Endotoxin / pyrogen failure in sterile product | STERILITY | Sterile product failure |
| 37 | Tablet imprinted with wrong ID | LABELING | Marking error, product correct |
| 38 | "Gluten free" claim but wheat is in the ingredient list | LABELING (secondary ALLERGEN) | Allergen declared; claim is wrong |
| 39 | Wrong API/ingredient used, product carry-over, same-line cross-contamination with another product | MIXUP | Wrong product content |
| 40 | Product under import alert released; non-permitted dietary ingredient | UNAPPROVED | Regulatory status |

Add new rows here as you meet them (number, pattern, label, why).

## Rare categories (< 10 gold labels)
PACKAGING (3) and OTHER (3). PACKAGING is rare because leak/breakage cases that threaten sterility are labeled STERILITY by tie-break (edge case 33); its per-class metrics are reported but flagged as unreliable.

## Annotation provenance (decision 2026-11-16, builder's choice)
Gold labels were produced by an LLM annotator (annotator A: Claude Opus 5.5, `notes` column) following this guide, **not hand-labeled by the builder**. Agreement is measured against an independent second LLM annotation (annotator B, a separate session given only the taxonomy and this guide, blind to A's labels) on 60 events (T3.1.3). Limitations: (1) annotator A also wrote the keyword baseline rules, which may bias the baseline comparison in either direction; (2) two LLM annotators may share systematic errors that agreement cannot detect; (3) a human spot check of a sample is recommended before publishing results.

Labeling time: single agent session on 2026-11-16 (not comparable to human labeling time).
