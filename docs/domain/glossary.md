# QA / Regulatory Glossary (T1.1.2)

Plain-language definitions as used in this project. Items whose exact regulatory wording I have not verified from a primary source are marked UNVERIFIED; do not quote them as regulation.

| Term | Definition (project usage) |
|---|---|
| Recall | A firm's removal or correction of a marketed product that FDA considers in violation of the laws it administers (21 CFR Part 7 Subpart C governs recall policy; exact 7.3 definition text UNVERIFIED). |
| Recall event / recall number | An event (`event_id`) is one recall action; it can cover many products, each with its own `recall_number`. This project counts events unless stated. |
| Class I / II / III | FDA's health-hazard classification: I = reasonable probability of serious adverse health consequences or death; II = temporary or medically reversible consequences, or remote probability of serious ones; III = not likely to cause adverse health consequences (fda.gov recalls background page). |
| Enforcement Report | FDA's weekly publication of monitored recalls and their classification; the source of openFDA enforcement data. |
| Voluntary vs FDA-requested vs mandated | Recalls may be firm-initiated, done at FDA's request, or ordered by FDA under statutory authority. |
| Market withdrawal | Removal of a product for a minor violation that would not be subject to FDA legal action (UNVERIFIED wording). |
| cGMP / CGMP | Current Good Manufacturing Practice - minimum requirements for methods, facilities and controls (drugs: 21 CFR 210/211; food: 21 CFR 117 Subpart B). |
| GxP | Umbrella term for "good practice" regulations (GMP, GLP, GCP, GDP). |
| Six-system inspection model | FDA CP 7356.002 groups drug CGMP into Quality; Facilities and Equipment; Materials; Production; Packaging and Labeling; Laboratory Control systems. |
| Quality unit | The group responsible for approving/rejecting materials, procedures and batches (21 CFR 211.22 - section text UNVERIFIED). |
| Deviation | A departure from an approved procedure, specification or instruction that must be documented and assessed. |
| OOS (out of specification) | A test result that falls outside established acceptance criteria; requires a documented investigation. |
| OOT (out of trend) | A result within specification but inconsistent with historical trend - an early-warning signal. |
| Specification | The tests, methods and acceptance criteria a material or product must meet. |
| Dissolution | Lab test measuring how fast the drug releases from a solid dose; failure can affect bioavailability. |
| Potency / assay | Measured amount of active ingredient relative to label claim (subpotent = low, superpotent = high). |
| Stability testing | Testing over time under defined storage conditions to support shelf life/expiry. |
| Sterility assurance | Confidence that a sterile product is free of viable microorganisms, based on validated processes, not just end-product testing. |
| Nitrosamines (e.g., NDMA) | Probable human carcinogen impurities found in some drugs since 2018; a major recall driver in the drug data. |
| Root cause | The underlying reason a failure occurred, found by investigation; recall text usually states a symptom, not the root cause. |
| Correction | Immediate action to fix the nonconforming product or situation (e.g., quarantine, rework). |
| Corrective action | Action to eliminate the cause of a detected nonconformity to prevent recurrence. |
| Preventive action | Action to eliminate the cause of a potential nonconformity before it occurs. |
| CAPA | Corrective and Preventive Action system: investigation, root-cause analysis, actions, and effectiveness checks. |
| Effectiveness check | Verification that a CAPA (or a recall) achieved its goal. |
| HACCP | Hazard Analysis and Critical Control Points - a preventive food-safety system with critical limits at control points (mandatory for some sectors, e.g., seafood and juice - UNVERIFIED scope). |
| HARPC | Hazard Analysis and Risk-based Preventive Controls - the FSMA approach in 21 CFR 117 Subpart C. |
| PCQI | Preventive Controls Qualified Individual - person who oversees the food safety plan under 21 CFR 117 (UNVERIFIED wording). |
| FSMA | FDA Food Safety Modernization Act (2011); shifted food safety to prevention, including preventive-controls rules. |
| Food safety plan | Written plan with hazard analysis, preventive controls, supply-chain program, recall plan, monitoring, corrective action and verification. |
| Preventive controls | Process, food allergen, sanitation and supply-chain controls applied to hazards needing control. |
| Environmental monitoring | Sampling of the processing environment (e.g., for Listeria) to verify sanitation controls. |
| Allergen cross-contact | Unintended transfer of an allergen into a food that should not contain it. |
| Major food allergens | Allergens defined by FALCPA as amended (sesame added by the FASTER Act). Current list and recent FDA interpretation changes - UNVERIFIED; check fda.gov before quoting. |
| DMAIC | Define, Measure, Analyze, Improve, Control - the Six Sigma improvement cycle used to frame this project. |
| CTQ | Critical to Quality - a measurable characteristic tied to a customer need. |
| SPC | Statistical Process Control - using control charts to separate common-cause from special-cause variation. |
| Control chart / CL / UCL / LCL | Time-ordered plot with a centre line and upper/lower control limits (typically +/- 3 sigma). |
| c-chart / p-chart | Control charts for counts of events per period (c) and for proportions (p). |
| Laney adjustment | Widens p/u-chart limits when data show more variation than the binomial/Poisson model (overdispersion). |
| Common vs special cause | Common cause = inherent noise of a stable process; special cause = an assignable shift that warrants investigation. |
| Western Electric / run rules | Signal rules beyond a single point outside limits, e.g., a run of consecutive points on one side of the centre line. |
| Pareto principle / analysis | Ranking causes by frequency to find the "vital few" that account for most occurrences. |
| NDC | National Drug Code - FDA's product identifier for drugs. |
| NDA / ANDA | New Drug Application / Abbreviated NDA (generics); "marketed without an approved NDA/ANDA" signals an unapproved drug. |
| FAERS / CAERS | FDA adverse-event reporting systems for drugs (FAERS) and foods/cosmetics/supplements (CAERS); spontaneous reports, no causality. |
| ICH Q9 / Q10 | ICH guidelines on Quality Risk Management (Q9) and Pharmaceutical Quality System (Q10). |
| USDA FSIS | USDA agency regulating meat, poultry and egg products; its recalls are outside openFDA. |
