# Root-Cause Taxonomy v1 (T1.1.2)

Machine-readable source: `data/reference/taxonomy.yaml` (14 categories). This page explains design and tie-breaks.

## Design principles
- Categories describe the **stated reason for recall**, which is often a symptom (e.g., "failed dissolution") rather than a root cause established by investigation. Dashboard text says "stated reason category".
- **Single label** per event, chosen by a tie-break priority: specific hazards beat generic system failures; hazard to the patient/consumer beats paperwork.
- Grounded in data: categories were checked against the most frequent 45-character prefixes of event reason text (drug: impurity/degradation, sterility, CGMP, microbial, dissolution, subpotent, labeling, unapproved NDA/ANDA, particulates; food: Listeria, Salmonella, undeclared milk/egg/wheat/soy/peanut/sulfites, insanitary conditions).
- Drug categories map to the six systems of FDA Compliance Program 7356.002, *Drug Manufacturing Inspections* (issued 09/16/2022, p.11: Quality; Facilities and Equipment; Materials; Production; Packaging and Labeling; Laboratory Control) - https://www.fda.gov/media/75167/download. Food categories map to FSMA hazard types (biological, chemical, physical) plus allergen. Most category-to-system mappings are **the builder's judgement** and are marked "(judgement)" in the YAML.

## Categories
| ID | Name | Applies to | Drug system / food hazard |
|---|---|---|---|
| ALLERGEN | Undeclared allergen / sensitivity ingredient | both (mostly food) | Packaging & Labeling* / allergen |
| STERILITY | Lack of sterility assurance | drug | Production* |
| MICRO | Microbial contamination | both | Lab Control / Production* / biological |
| IMPURITY | Chemical contamination / impurity | both | Materials* / Lab Control / chemical |
| UNAPPROVED | Unapproved / adulterated status | both | Quality* / chemical* |
| FOREIGN | Foreign material / particulate | both | Production / F&E* / physical |
| MIXUP | Product mix-up / cross-contamination | both | Packaging & Labeling / Production* |
| POTENCY | Potency / assay failure | both | Lab Control |
| SPEC_FAIL | Dissolution / stability / other OOS | both (mostly drug) | Lab Control |
| PACKAGING | Container-closure / delivery-system defect | both | Packaging & Labeling |
| PROCESS_SANITATION | Inadequate processing, sanitation or storage | both (mostly food) | Production / F&E* / biological |
| LABELING | Labeling error (non-allergen) | both | Packaging & Labeling |
| CGMP | Non-specific CGMP deviation | both (mostly drug) | Quality |
| OTHER | Other / unclear | both | - |
\* judgement mapping.

## Tie-break priority (earlier wins)
ALLERGEN > STERILITY > MICRO > IMPURITY > UNAPPROVED > FOREIGN > MIXUP > POTENCY > SPEC_FAIL > PACKAGING > PROCESS_SANITATION > LABELING > CGMP > OTHER

### Worked conflict examples
1. "Undeclared milk: product labeled as vanilla contains chocolate (label mix-up)" -> **ALLERGEN** (beats MIXUP, LABELING: the consumer hazard is the allergen).
2. "CGMP deviations: presence of NDMA impurity detected above the acceptable daily intake" -> **IMPURITY** (beats CGMP: specific defect named).
3. "Lack of assurance of sterility; products marketed without an approved NDA" -> **STERILITY** (beats UNAPPROVED: patient hazard first).
4. "Dietary supplement found to contain undeclared sildenafil" -> **UNAPPROVED** (not ALLERGEN: "undeclared" a drug, not an allergen).
5. "Presence of foreign tablets: a bottle of drug A contained tablets of drug B" -> **MIXUP** (not FOREIGN: foreign material means physical matter).
6. "Failed dissolution and subpotent results at the 12-month stability station" -> **POTENCY** (beats SPEC_FAIL).
7. "Product prepared and held under insanitary conditions; Listeria found in environmental samples" -> **MICRO** (organism named, beats PROCESS_SANITATION).
8. "Labeling: incorrect expiration date; CGMP deviations" -> **LABELING** (beats CGMP).

## Rule for OTHER
Use only when no category's include rule matches after reading the full text (e.g., "recall initiated as a precautionary measure" with no hazard). Target < 5% of gold labels; if exceeded, revisit the taxonomy in T3.1.1.

## Uncertain points (UNVERIFIED / to revisit)
- Including sulfites and FD&C Yellow No. 5 in ALLERGEN is a design choice; they are not among the major food allergens defined by FALCPA. Their labeling requirement citation is UNVERIFIED.
- Whether sterile processing falls under CP 7356.002A's scope rather than 7356.002 for mapping purposes is UNVERIFIED (does not affect labeling).
- The "allergen" hazard type label for food: the FSMA PC rule lists food allergen controls as a preventive-control type; whether FDA classes allergens as a "chemical" hazard in hazard analysis is UNVERIFIED - kept separate here for clarity.
