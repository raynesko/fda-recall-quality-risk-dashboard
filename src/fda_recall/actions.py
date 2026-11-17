"""DMAIC QA action library (T6.2.1).

    python -m fda_recall.actions   -> data/reference/qa_action_library.csv + docs/domain/qa-action-library.md

Actions are GENERIC HYPOTHESES derived from category-level patterns in FDA-recorded recall events. They are
not findings about any named firm and not regulatory advice. citation_verified = Y means the section
number and title were confirmed on 2026-11-17 at the source_url (Cornell LII mirror of the CFR; eCFR blocks
automated access); the action wording is our paraphrase, not regulatory text, except where noted.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV_OUT = ROOT / "data" / "reference" / "qa_action_library.csv"
MD_OUT = ROOT / "docs" / "domain" / "qa-action-library.md"
LII = "https://www.law.cornell.edu/cfr/text/21/"
DISCLAIMER = ("Generic, hypothesis-level QA actions inferred from category-level patterns in public openFDA "
              "recall (enforcement) data. Not findings about any named firm, not regulatory or legal advice, "
              "and not a substitute for a site's own risk assessment. Built from openFDA data - not for "
              "clinical or regulatory decisions.")

# section -> verified title (confirmed 2026-11-17 on the LII subpart pages)
CFR = {
    "211.22": "Responsibilities of quality control unit",
    "211.67": "Equipment cleaning and maintenance",
    "211.84": "Testing and approval or rejection of components, drug product containers, and closures",
    "211.94": "Drug product containers and closures",
    "211.100": "Written procedures; deviations",
    "211.110": "Sampling and testing of in-process materials and drug products",
    "211.113": "Control of microbiological contamination",
    "211.122": "Materials examination and usage criteria",
    "211.125": "Labeling issuance",
    "211.130": "Packaging and labeling operations",
    "211.160": "General requirements (Laboratory Controls)",
    "211.165": "Testing and release for distribution",
    "211.166": "Stability testing",
    "211.192": "Production record review",
    "211.198": "Complaint files",
    "117.3": "Definitions",
    "117.35": "Sanitary operations",
    "117.80": "Processes and controls",
    "117.130": "Hazard analysis",
    "117.135": "Preventive controls",
    "117.145": "Monitoring",
    "117.150": "Corrective actions and corrections",
    "117.160": "Validation",
    "117.165": "Verification of implementation and effectiveness",
    "117.430": "Conducting supplier verification activities for raw materials and other ingredients",
}
FALCPA = ("FALCPA of 2004 (FDA page; fetched in T1.1.1)", "Y",
          "https://www.fda.gov/food/food-allergensgluten-free-guidance-documents-"
          "regulatory-information/food-allergen-labeling-and-consumer-protection-act-2004-falcpa")


def cite(sec: str) -> tuple[str, str, str]:
    return f"21 CFR {sec} {CFR[sec]}", "Y", f"{LII}{sec}"


def unverified(text: str) -> tuple[str, str, str]:
    return text, "N", ""


D, M, A, IMP, C = "Define", "Measure", "Analyze", "Improve", "Control"

# (category, scope, phase, action, owner, metric, citation-tuple)
ROWS = [
    # ALLERGEN
    ("ALLERGEN", "food", D, "Scope undeclared-allergen risk to label/formula changes and shared-line changeovers; list major allergens per current FDA list (verify list at time of use)", "QA / Regulatory", "Products with allergen-containing ingredients on shared lines (count)", FALCPA),
    ("ALLERGEN", "food", M, "Track label-vs-formula verification at each label change and at line start-up", "QA", "% label changes with documented label-formula check", cite("117.135")),
    ("ALLERGEN", "food", A, "Pareto label-related deviations by cause (wrong label stock, formula change, supplier ingredient change)", "QA", "Top-3 causes share of allergen deviations", cite("117.130")),
    ("ALLERGEN", "food", IMP, "Strengthen food allergen controls: label reconciliation at changeover, segregated label storage, supplier allergen statements", "Operations / QA", "Label-reconciliation exceptions per 100 changeovers", cite("117.135")),
    ("ALLERGEN", "food", C, "Verify allergen controls are implemented and effective (record review, periodic label audits); document corrections vs corrective actions", "QA", "Overdue verification records (count)", cite("117.165")),
    # MICRO
    ("MICRO", "both", D, "Define pathogen/microbial hazards by product and process step (e.g., ready-to-eat exposure after kill step)", "Food Safety / QA", "Process steps with an identified microbial hazard", cite("117.130")),
    ("MICRO", "both", M, "Run environmental monitoring with zone-based sampling; trend positives", "Microbiology / QA", "Zone 1-2 positive rate per month (p-chart)", cite("117.165")),
    ("MICRO", "both", A, "Investigate positives to root cause (harborage, traffic flow, sanitation gaps)", "QA / Sanitation", "Median days from positive to root cause", cite("117.150")),
    ("MICRO", "both", IMP, "Revise sanitation controls and hygienic zoning; for drugs, written procedures to prevent objectionable microorganisms", "Sanitation / Production", "Repeat-positive sites after corrective action", cite("117.135")),
    ("MICRO", "drug", C, "Maintain written procedures to prevent objectionable microorganisms in non-sterile drug products; monitor on control charts with reaction plan", "QA", "Out-of-trend micro results reviewed within SLA (%)", cite("211.113")),
    # STERILITY
    ("STERILITY", "drug", D, "Define sterility-assurance boundaries: aseptic steps, sterilization processes, compounded sterile preparations in scope", "Sterility Assurance / QA", "Processes with current validation status (%)", cite("211.113")),
    ("STERILITY", "drug", M, "Trend aseptic-process monitoring (environmental and personnel monitoring, media-fill outcomes)", "Microbiology", "Excursions per 100 aseptic batches", cite("211.113")),
    ("STERILITY", "drug", A, "Investigate excursions and sterility failures; assess impact on all potentially affected batches", "QA", "Investigations closed on time (%)", cite("211.192")),
    ("STERILITY", "drug", IMP, "Improve aseptic technique training, intervention controls and cleaning of critical zones", "Production / Training", "Interventions per batch (trend)", cite("211.67")),
    ("STERILITY", "drug", C, "QC unit approves/rejects procedures and batches; release only after required testing", "QC unit", "Batches released with open sterility deviations (target 0)", cite("211.22")),
    # IMPURITY
    ("IMPURITY", "both", D, "Define chemical-hazard scope: process impurities, degradants, contaminants from components/equipment", "QA / Regulatory", "Products with a documented impurity risk assessment (%)", cite("211.84")),
    ("IMPURITY", "drug", M, "Test components and finished product against impurity specifications; trend results versus limits", "QC Lab", "Results >50% of limit (count per quarter)", cite("211.165")),
    ("IMPURITY", "both", A, "Root-cause impurity OOS/out-of-trend results (supplier change, process drift, contamination source)", "QC / QA", "OOS investigations with assigned root cause (%)", cite("211.192")),
    ("IMPURITY", "both", IMP, "Qualify and verify suppliers of at-risk raw materials; add incoming tests where justified", "Supplier Quality", "Supplier verification activities completed on schedule (%)", cite("117.430")),
    ("IMPURITY", "drug", C, "Stability program monitors degradants over shelf life", "QC Lab", "Stability pulls tested on time (%)", cite("211.166")),
    # FOREIGN
    ("FOREIGN", "both", D, "Define physical-hazard sources (glass, metal, plastic, particulate) per line", "QA / Engineering", "Lines with a physical-hazard map", cite("117.130")),
    ("FOREIGN", "both", M, "Measure detection-system challenges and particulate inspection results", "Production / QA", "Detector challenge failures per 1,000 checks", cite("117.135")),
    ("FOREIGN", "both", A, "Investigate complaints and finds to source (equipment wear, packaging supplier, glass breakage)", "QA", "Complaints with source identified (%)", cite("211.198")),
    ("FOREIGN", "both", IMP, "Preventive maintenance and equipment design changes on wear points; supplier corrective action requests", "Engineering / Supplier Quality", "Repeat finds from same source after correction", cite("211.67")),
    ("FOREIGN", "food", C, "Processes and controls include measures to protect against inclusion of metal or other extraneous material", "Operations / QA", "Physical-hazard deviations per month (c-chart)", cite("117.80")),
    # MIXUP
    ("MIXUP", "both", D, "Define mix-up risk points: label stock, changeovers, shared packaging lines, look-alike products", "QA / Packaging", "Changeovers per week on shared lines", cite("211.130")),
    ("MIXUP", "drug", M, "Reconcile labeling issued, used and returned; record discrepancies", "Packaging / QA", "Label reconciliation discrepancies per 100 batches", cite("211.125")),
    ("MIXUP", "drug", A, "Investigate reconciliation discrepancies and line-clearance failures", "QA", "Line-clearance failures with root cause (%)", cite("211.192")),
    ("MIXUP", "drug", IMP, "Strengthen line clearance and physical segregation of labeling; vision/barcode verification", "Packaging Engineering", "Line-clearance failures per month", cite("211.130")),
    ("MIXUP", "drug", C, "Labeling examined for identity and conformity before use; controlled storage", "QA", "Labeling lots used without documented examination (target 0)", cite("211.122")),
    # POTENCY
    ("POTENCY", "drug", D, "Define potency CTQs (assay limits) and the process steps that drive them (blending, fill weight, degradation)", "QA / Technical Services", "Products with defined potency CTQs (%)", cite("211.100")),
    ("POTENCY", "drug", M, "In-process sampling and testing of blend uniformity and fill weight", "QC / Production", "In-process results outside alert limits (%)", cite("211.110")),
    ("POTENCY", "drug", A, "Investigate super/sub-potent results across affected batches", "QA", "Investigations covering all potentially affected batches (%)", cite("211.192")),
    ("POTENCY", "drug", IMP, "Tighten process parameters and written procedures where drift is found", "Technical Services", "Process capability (Cpk) of assay", cite("211.100")),
    ("POTENCY", "drug", C, "Stability testing confirms potency through expiry", "QC Lab", "Stability assay results trending toward limit (count)", cite("211.166")),
    # SPEC_FAIL
    ("SPEC_FAIL", "drug", D, "Define OOS handling scope (dissolution, stability, other specifications)", "QC / QA", "Specifications with documented OOS procedure (%)", cite("211.160")),
    ("SPEC_FAIL", "drug", M, "Trend OOS and out-of-trend results by test and product", "QC Lab", "OOS rate per 100 tests (p-chart)", cite("211.165")),
    ("SPEC_FAIL", "drug", A, "Investigate OOS through laboratory and production phases; extend to other batches", "QA / QC", "OOS investigations closed on time (%)", cite("211.192")),
    ("SPEC_FAIL", "drug", IMP, "Address method or process root causes (formulation, equipment, method robustness)", "Technical Services / QC", "Repeat OOS for same root cause", cite("211.100")),
    ("SPEC_FAIL", "drug", C, "Stability program with predefined pulls and trending", "QC Lab", "Stability failures per year", cite("211.166")),
    # LABELING
    ("LABELING", "both", D, "Define labeling-content risks (wrong strength, missing statements, non-English labeling, nutrition/ingredient errors)", "Regulatory / QA", "Label versions under change control (%)", cite("211.125")),
    ("LABELING", "both", M, "Proof-read and verify labeling at approval and at issuance", "Regulatory / Packaging", "Labeling errors caught pre-release per 100 approvals", cite("211.122")),
    ("LABELING", "both", A, "Categorize labeling errors by origin (artwork, data entry, supplier print error)", "QA", "Share of labeling errors by origin", cite("211.192")),
    ("LABELING", "both", IMP, "Introduce artwork change control with independent second check", "Regulatory Affairs", "Artwork changes with second-person verification (%)", cite("211.125")),
    ("LABELING", "both", C, "Packaging and labeling operation controls; periodic label audits", "QA", "Audit findings per quarter", cite("211.130")),
    # PROCESS_SANITATION
    ("PROCESS_SANITATION", "food", D, "Define process-control hazards (thermal processing, acidification, temperature control, cross-contact)", "Food Safety", "Process controls with defined parameters and limits (%)", cite("117.135")),
    ("PROCESS_SANITATION", "food", M, "Monitor process-control parameters with records", "Production / QA", "Monitoring records completed (%)", cite("117.145")),
    ("PROCESS_SANITATION", "food", A, "When a parameter is out of limit, apply corrective action procedure; distinguish a correction (fix the instance) from a corrective action (prevent recurrence, evaluate affected food)", "QA", "Deviations with documented corrective action (%)", cite("117.150")),
    ("PROCESS_SANITATION", "food", IMP, "Validate process controls (e.g., thermal process lethality) and revise sanitation controls", "Food Safety / Process Authority", "Process controls with current validation (%)", cite("117.160")),
    ("PROCESS_SANITATION", "food", C, "Maintain sanitary operations; verify implementation and effectiveness", "Sanitation / QA", "Sanitation verification failures per month", cite("117.35")),
    # CGMP
    ("CGMP", "drug", D, "Scope systemic cGMP gaps behind non-specific recalls (procedures, records, QC unit oversight)", "QA", "Open deviations older than 30 days", cite("211.22")),
    ("CGMP", "drug", M, "Measure deviation and record-review performance", "QA", "Batch records with errors found at review (%)", cite("211.192")),
    ("CGMP", "drug", A, "Trend deviations by system (six-system model) to locate weakest system", "QA", "Deviation share by system", unverified("FDA Compliance Program 7356.002 six systems (verified in T1.1.2 taxonomy notes; not re-checked here)")),
    ("CGMP", "drug", IMP, "Run corrective and preventive actions (CAPA) with effectiveness checks on systemic causes", "QA", "CAPA effectiveness checks passed (%)", unverified("ICH Q10 Pharmaceutical Quality System (CAPA system) - UNVERIFIED")),
    ("CGMP", "drug", C, "Follow written procedures; record and justify deviations", "All functions / QA", "Unjustified deviations found in audits", cite("211.100")),
    # UNAPPROVED
    ("UNAPPROVED", "both", D, "Define exposure to unapproved/adulterated status (tainted supplements, undeclared drug ingredients, imported ingredients under import alert)", "Regulatory / Supplier Quality", "Ingredients from suppliers without verification (%)", unverified("FD&C Act adulteration/new-drug provisions - UNVERIFIED")),
    ("UNAPPROVED", "both", M, "Track supplier verification results and certificates of analysis versus identity testing", "Supplier Quality", "Identity-test discrepancies per 100 receipts", cite("211.84")),
    ("UNAPPROVED", "both", A, "Investigate source of unapproved ingredient or undeclared drug substance", "QA / Regulatory", "Cases with supplier root cause (%)", cite("117.150")),
    ("UNAPPROVED", "food", IMP, "Conduct risk-based supplier verification (audits, sampling and testing) for high-risk ingredients", "Supplier Quality", "High-risk suppliers verified in last 12 months (%)", cite("117.430")),
    ("UNAPPROVED", "both", C, "Regulatory review of product status before launch and on ingredient change", "Regulatory Affairs", "Launches without regulatory status check (target 0)", unverified("Internal change-control requirement (no single CFR section) - N/A")),
]


def main() -> int:
    cols = ["category", "product_scope", "phase", "action", "owner_function", "metric", "citation",
            "citation_verified", "source_url"]
    out = []
    for cat, scope, phase, action, owner, metric, c in ROWS:
        text, ver, url = c
        out.append(dict(zip(cols, [cat, scope, phase, action, owner, metric, text, ver, url])))
    for r in out:
        assert r["citation_verified"] in ("Y", "N")
        assert r["citation_verified"] == "N" or r["source_url"].startswith("https://"), r
    cats = {r["category"] for r in out}
    for c in cats:
        assert {r["phase"] for r in out if r["category"] == c} == {D, M, A, IMP, C}, c
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)

    L = ["# DMAIC QA Action Library (T6.2.1; generated by `python -m fda_recall.actions`)", "",
         f"> **Disclaimer:** {DISCLAIMER}", "",
         f"{len(cats)} categories x 5 DMAIC phases = {len(out)} actions. Data: `data/reference/qa_action_library.csv`.", "",
         "**Citations.** `citation_verified = Y` means the section number and title were confirmed on 2026-11-17 "
         "on the Cornell LII mirror of the CFR (eCFR blocks automated access). The action text is a paraphrase, "
         "not regulatory text. Read at text level on 2026-11-17: 117.3 (definition of *correction*), 117.135(c) "
         "(types of preventive controls incl. food allergen and sanitation controls), 117.80(c)(8) (\"adequate measures\" "
         "against metal or other extraneous material), 117.165(a)(3) (environmental monitoring as verification), "
         "211.113(a)-(b) (objectionable microorganisms; validation of aseptic and sterilization processes). "
         "Re-check on eCFR before quoting.", "",
         "**Terminology.**",
         "- *Correction* (21 CFR 117.3): fix the problem that occurred, without the actions of a corrective-action procedure.",
         "- *Corrective action* (21 CFR 117.150): a procedure that also prevents recurrence and evaluates and controls affected food.",
         "- *CAPA* (corrective and preventive action) is the drug-quality-system term used in ICH Q10 (UNVERIFIED here). "
         "This library uses \"CAPA\" only in the CGMP row.", ""]
    for c in sorted(cats):
        L += [f"## {c}", "", "| Phase | Action | Owner | Example metric | Citation |", "|---|---|---|---|---|"]
        for r in [r for r in out if r["category"] == c]:
            ref = f"[{r['citation']}]({r['source_url']})" if r["source_url"] else f"{r['citation']} (unverified)"
            L.append(f"| {r['phase']} | {r['action']} | {r['owner_function']} | {r['metric']} | {ref} |")
        L.append("")
    MD_OUT.write_text("\n".join(L), encoding="utf-8")
    print(len(out), "rows,", len(cats), "categories,", sum(r["citation_verified"] == "Y" for r in out), "verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
