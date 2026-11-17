# Interview Q&A Talking Points (T7.2.1)

All numbers trace to `results/metrics.json`; run `python scripts/resume_numbers.py`.

### 1. "Why control charts? Why not just count recalls per month?"
- Monthly counts move by chance. A control chart separates common-cause from special-cause variation, so you don't chase noise.
- I used p-charts on category *share* because there's no production denominator. Share also absorbs overall volume swings.
- Low monthly counts are overdispersed, so I used Laney limits.
- I simulated 1,000 stable Poisson series. At about 1 event per month, rule-1 false alarms ran at 0.008 per point vs the textbook 0.0027.
- Signal counts depend heavily on the baseline window (39–192), so I treat signals as prompts to investigate, not conclusions.

### 2. "Are these recall rates?"
- No. They are FDA-recorded recall events per month with no volume denominator.
- They also reflect FDA enforcement focus and reporting cadence. One firm's multi-product recall can move a month.
- That's stated on every dashboard page.

### 3. "How do you know the labels and the classifier are right?"
- The 300-event gold set was labeled by an LLM annotator. A second, independent LLM relabeled 60 blind, with kappa 0.98.
- Because both are LLMs sharing a guide, I treat that as an upper bound and recommend a human spot check.
- Cross-validation was grouped by firm to stop near-duplicate text leaking between folds.
- The keyword baseline was frozen before seeing gold labels.
- **Why the ML lost:** 300 labels over 14 classes is too few for the rare classes (packaging and "other" scored F1 0). FDA's recall text is formulaic, so rules work well.
- Caveat: the same annotator wrote the rules and the labels, so the rules' score may be optimistic.

### 4. "What would a QA manager do with this?"
- Start from the watchlist, check the stability %, then open the DMAIC actions for that category.
- Undeclared allergen → label-to-formula verification at changeover (21 CFR 117.135 food allergen controls).
- Microbial → environmental monitoring as verification (117.165(a)(3)).
- Sterility → aseptic process validation (211.113(b)).
- **Correction vs corrective action** (117.3 / 117.150): a correction fixes the instance; a corrective action prevents recurrence and evaluates affected product. CAPA is the drug quality-system term.
- These are hypotheses from category patterns, never findings about a firm.

### 5. "Did the risk score work? What would you change?"
- No. I pre-registered the success criteria and recorded the document's hash.
- Over 10 yearly origins: precision@3 was 0.235 vs 0.382 for random, and the score's correlation with next-year change was −0.31.
- Momentum alone had ρ −0.37, which is regression to the mean: categories that spike tend to fall back. My score weighted momentum most.
- I didn't re-tune it. I kept it as a transparent triage view and showed which flags are fragile.
- **Next steps:** a persistence-based outcome (does the category stay elevated?), a denominator such as establishment counts, and a human-labeled holdout.

**Also be ready for:**
- Class I/II/III definitions, and voluntary vs FDA-requested recalls (21 CFR Part 7 Subpart C).
- cGMP (Part 211) vs preventive controls (Part 117) vs HACCP.
- OOS investigations (211.192).
- Why rules or logistic regression rather than a transformer: small labeled set, auditability in a regulated setting.
