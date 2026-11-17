"""Generate the Power BI project (PBIP: TMDL semantic model + PBIR report) from code.

    python -m fda_recall.pbip     -> dashboard/FDA_Recall_Dashboard.pbip (+ .SemanticModel/, .Report/)

Why generated: the dashboard is reproducible and reviewable as text, and every visual reads precomputed
Python outputs (data/processed/dashboard/*.parquet, data/processed/star/*.parquet) so it reconciles exactly.
Open the .pbip in Power BI Desktop, click Refresh, then run docs/dashboard/test-checklist.md.
Formats: PBIR schemas (developer.microsoft.com/json-schemas/fabric) validated by scripts/validate_pbir.py;
TMDL parsed by scripts/validate_tmdl.ps1 (Microsoft TOM TmdlSerializer shipped with Power BI Desktop).
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd

from .actions import DISCLAIMER
from .dashboard import FOOTER, TOOLTIP

ROOT = Path(__file__).resolve().parents[2]
DASH = ROOT / "dashboard"
NAME = "FDA_Recall_Dashboard"
SM = DASH / f"{NAME}.SemanticModel"
RP = DASH / f"{NAME}.Report"
DATA = ROOT / "data" / "processed"
SCH = "https://developer.microsoft.com/json-schemas/fabric"
VC = f"{SCH}/item/report/definition/visualContainer/2.6.0/schema.json"
T = "\t"

# ----------------------------------------------------------------------------------------- model --
TABLES = {  # table -> parquet path relative to data/processed
    "fact_recall_event": "star/fact_recall_event.parquet",
    "fact_recall_product": "star/fact_recall_product.parquet",
    "dim_date": "star/dim_date.parquet",
    "dim_firm": "star/dim_firm.parquet",
    "dim_category": "star/dim_category.parquet",
    "dim_product_type": "dashboard/dim_product_type.parquet",
    "dash_kpi": "dashboard/dash_kpi.parquet",
    "dash_pareto": "dashboard/dash_pareto.parquet",
    "dash_spc": "dashboard/dash_spc.parquet",
    "dash_watchlist": "dashboard/dash_watchlist.parquet",
    "dash_watch_components": "dashboard/dash_watch_components.parquet",
    "dash_actions": "dashboard/dash_actions.parquet",
    "dash_notes": "dashboard/dash_notes.parquet",
}
RELATIONSHIPS = [  # many-side column -> one-side column
    ("fact_recall_event.firm_key", "dim_firm.firm_key"),
    ("fact_recall_event.category_id", "dim_category.category_id"),
    ("fact_recall_event.report_date_key", "dim_date.date_key"),
    ("fact_recall_event.product_type", "dim_product_type.product_type"),
    ("fact_recall_product.event_id", "fact_recall_event.event_id"),
    ("dash_pareto.category", "dim_category.category_id"),
    ("dash_watchlist.category", "dim_category.category_id"),
    ("dash_watchlist.product_type", "dim_product_type.product_type"),
    ("dash_watch_components.category", "dim_category.category_id"),
    ("dash_watch_components.product_type", "dim_product_type.product_type"),
    ("dash_actions.category", "dim_category.category_id"),
]
SPC_DEFAULT_SERIES, SPC_DEFAULT_CHART = "Drugs - IMPURITY", "Share of month (p-chart)"
TOP6 = ["Drugs - IMPURITY", "Drugs - SPEC_FAIL", "Drugs - STERILITY", "Food - ALLERGEN", "Food - MICRO", "Food - FOREIGN"]
_SPC_CTX = (f'VAR s = IF(HASONEVALUE(dash_spc[series]), VALUES(dash_spc[series]), "{SPC_DEFAULT_SERIES}")\n'
            f'VAR c = IF(HASONEVALUE(dash_spc[chart_label]), VALUES(dash_spc[chart_label]), "{SPC_DEFAULT_CHART}")\n')
_PAR_CTX = ('VAR w = IF(HASONEVALUE(dash_pareto[weight]), VALUES(dash_pareto[weight]), "count")\n'
            'VAR p = IF(HASONEVALUE(dash_pareto[period_key]), VALUES(dash_pareto[period_key]), "full")\n')
MEASURES = {  # table -> [(name, dax, formatString)]
    "fact_recall_event": [
        ("Total Events", "COUNTROWS(fact_recall_event)", "#,0"),
        ("As Of Month", "EOMONTH(CALCULATE(MAX(fact_recall_event[report_month]), REMOVEFILTERS(fact_recall_event)), -1)", "yyyy-mm"),
        ("Events T12", "VAR e = [As Of Month]\nRETURN CALCULATE(COUNTROWS(fact_recall_event), fact_recall_event[report_month] > EDATE(e, -12), fact_recall_event[report_month] <= e)", "#,0"),
        ("Events P12", "VAR e = [As Of Month]\nRETURN CALCULATE(COUNTROWS(fact_recall_event), fact_recall_event[report_month] > EDATE(e, -24), fact_recall_event[report_month] <= EDATE(e, -12))", "#,0"),
        ("Change vs Prior 12m", "DIVIDE([Events T12] - [Events P12], [Events P12])", "+0.0%;-0.0%;0.0%"),
        ("Class I Share T12", "DIVIDE(CALCULATE([Events T12], fact_recall_event[classification] = \"Class I\"), [Events T12])", "0.0%"),
        ("Events Complete Months", "CALCULATE(COUNTROWS(fact_recall_event), fact_recall_event[report_month] >= DATE(2012, 7, 1), fact_recall_event[report_month] <= [As Of Month])", "#,0"),
    ],
    "dash_watchlist": [
        ("Flagged Categories", "CALCULATE(COUNTROWS(dash_watchlist), dash_watchlist[flag] = TRUE())", "0"),
        ("Score", "SUM(dash_watchlist[score])", "0.000"),
    ],
    "dash_kpi": [
        ("Data As Of", "\"Data as of \" & FIRSTNONBLANK(dash_kpi[data_as_of], 1) & \" (report date). \" & FIRSTNONBLANK(dash_kpi[footer], 1)", ""),
    ],
    "dash_pareto": [
        ("Pareto Value", _PAR_CTX + "RETURN CALCULATE(SUM(dash_pareto[value]), dash_pareto[weight] = w, dash_pareto[period_key] = p)", "#,0"),
        ("Pareto Cum Pct", _PAR_CTX + "RETURN CALCULATE(MAX(dash_pareto[cum_pct]), dash_pareto[weight] = w, dash_pareto[period_key] = p) / 100", "0.0%"),
        ("Pareto Sort Key", _PAR_CTX + "RETURN 100 - CALCULATE(MIN(dash_pareto[sort_order]), dash_pareto[weight] = w, dash_pareto[period_key] = p)", "0"),
        ("Pareto Drugs", "CALCULATE([Pareto Value], dash_pareto[product_type] = \"Drugs\")", "#,0"),
        ("Pareto Drugs Cum Pct", "CALCULATE([Pareto Cum Pct], dash_pareto[product_type] = \"Drugs\")", "0.0%"),
        ("Pareto Drugs Sort", "CALCULATE([Pareto Sort Key], dash_pareto[product_type] = \"Drugs\")", "0"),
        ("Pareto Food", "CALCULATE([Pareto Value], dash_pareto[product_type] = \"Food\")", "#,0"),
        ("Pareto Food Cum Pct", "CALCULATE([Pareto Cum Pct], dash_pareto[product_type] = \"Food\")", "0.0%"),
        ("Pareto Food Sort", "CALCULATE([Pareto Sort Key], dash_pareto[product_type] = \"Food\")", "0"),
    ],
    "dash_spc": [
        ("SPC Value", _SPC_CTX + "RETURN CALCULATE(SUM(dash_spc[value]), dash_spc[series] = s, dash_spc[chart_label] = c)", "0.000"),
        ("SPC CL", _SPC_CTX + "RETURN CALCULATE(SUM(dash_spc[cl]), dash_spc[series] = s, dash_spc[chart_label] = c)", "0.000"),
        ("SPC UCL", _SPC_CTX + "RETURN CALCULATE(SUM(dash_spc[ucl]), dash_spc[series] = s, dash_spc[chart_label] = c)", "0.000"),
        ("SPC LCL", _SPC_CTX + "RETURN CALCULATE(SUM(dash_spc[lcl]), dash_spc[series] = s, dash_spc[chart_label] = c)", "0.000"),
        ("SPC Signal Point", _SPC_CTX + "RETURN CALCULATE(SUM(dash_spc[signal_value]), dash_spc[series] = s, dash_spc[chart_label] = c)", "0.000"),
        ("SPC Signals After Baseline", _SPC_CTX + "RETURN CALCULATE(COUNTROWS(dash_spc), dash_spc[series] = s, dash_spc[chart_label] = c, dash_spc[signal] = TRUE(), dash_spc[phase] = \"II\")", "0"),
        ("SPC Selected Series", _SPC_CTX + "RETURN s & \" | \" & c", ""),
        ("p-Chart Signals All Monitored", "CALCULATE(COUNTROWS(dash_spc), REMOVEFILTERS(dash_spc), dash_spc[chart] = \"p\", dash_spc[signal] = TRUE(), dash_spc[phase] = \"II\")", "0"),
        ("Top6 Share", "IF(SELECTEDVALUE(dash_spc[series]) IN {" + ", ".join(f'"{s}"' for s in TOP6) + "}, CALCULATE(SUM(dash_spc[value]), dash_spc[chart] = \"p\"))", "0.0%"),
        ("Top6 UCL", "IF(SELECTEDVALUE(dash_spc[series]) IN {" + ", ".join(f'"{s}"' for s in TOP6) + "}, CALCULATE(SUM(dash_spc[ucl]), dash_spc[chart] = \"p\"))", "0.0%"),
    ],
}

DTYPE = {"str": "string", "string": "string", "object": "string", "int64": "int64", "Int64": "int64",
         "int32": "int64", "float64": "double", "bool": "boolean", "datetime64[us]": "dateTime",
         "datetime64[ns]": "dateTime"}


def q(name: str) -> str:
    return name if name.replace("_", "").isalnum() else "'" + name.replace("'", "''") + "'"


def table_tmdl(table: str, rel_path: str) -> str:
    df = pd.read_parquet(DATA / rel_path)
    L = [f"table {table}", ""]
    for name, dax, fmt in MEASURES.get(table, []):
        lines = dax.split("\n")
        if len(lines) == 1:
            L.append(f"{T}measure {q(name)} = {dax}")
        else:
            L.append(f"{T}measure {q(name)} =")
            L += [f"{T}{T}{T}{ln}" for ln in lines]
        if fmt:
            L.append(f"{T}{T}formatString: {fmt}")
        L.append("")
    date_cols = []
    for col, dt in df.dtypes.astype(str).items():
        tt = DTYPE[dt]
        L += [f"{T}column {q(col)}", f"{T}{T}dataType: {tt}"]
        if tt == "dateTime":
            date_cols.append(col)
            L.append(f"{T}{T}formatString: yyyy-mm-dd")
        L += [f"{T}{T}summarizeBy: none", f"{T}{T}sourceColumn: {col}", ""]
    m_types = ", ".join(f'{{"{c}", type datetime}}' for c in date_cols)
    win = rel_path.replace("/", "\\\\")
    src = [ "let",
            f'    Source = Parquet.Document(File.Contents(DataFolder & "{win}")){"," if date_cols else ""}']
    if date_cols:
        src += [f"    Typed = Table.TransformColumnTypes(Source, {{{m_types}}})", "in", "    Typed"]
    else:
        src += ["in", "    Source"]
    L += [f"{T}partition {table} = m", f"{T}{T}mode: import", f"{T}{T}source ="]
    L += [f"{T}{T}{T}{T}{ln}" for ln in src]
    L.append("")
    return "\n".join(L).replace("\\\\", "\\")


def write_model() -> None:
    d = SM / "definition"
    (d / "tables").mkdir(parents=True, exist_ok=True)
    (SM / "definition.pbism").write_text(json.dumps({
        "$schema": f"{SCH}/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.2", "settings": {}}, indent=2), encoding="utf-8")
    (d / "database.tmdl").write_text("database\n\tcompatibilityLevel: 1600\n", encoding="utf-8")
    model = ["model Model", f"{T}culture: en-US", f"{T}defaultPowerBIDataSourceVersion: powerBI_V3",
             f"{T}sourceQueryCulture: en-US", f"{T}dataAccessOptions", f"{T}{T}legacyRedirects",
             f"{T}{T}returnErrorValuesAsNull", ""]
    model += [f"ref table {t}" for t in TABLES]
    model += ["", "ref expression DataFolder", ""]
    (d / "model.tmdl").write_text("\n".join(model), encoding="utf-8")
    folder = str(DATA) + "\\"
    (d / "expressions.tmdl").write_text(
        f'expression DataFolder = "{folder}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
        f"{T}annotation PBI_ResultType = Text\n", encoding="utf-8")
    rel = []
    for i, (a, b) in enumerate(RELATIONSHIPS, 1):
        rel += [f"relationship rel_{i:02d}_{a.replace('.', '_')}", f"{T}fromColumn: {a}", f"{T}toColumn: {b}", ""]
    (d / "relationships.tmdl").write_text("\n".join(rel), encoding="utf-8")
    for t, p in TABLES.items():
        (d / "tables" / f"{t}.tmdl").write_text(table_tmdl(t, p), encoding="utf-8")


# ---------------------------------------------------------------------------------------- report --
def lit(v) -> dict:
    if isinstance(v, bool):
        s = "true" if v else "false"
    elif isinstance(v, int):
        s = f"{v}L"
    elif isinstance(v, float):
        s = f"{v}D"
    else:
        s = "'" + str(v).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": s}}}


def col(entity: str, prop: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def meas(entity: str, prop: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


AGG = {0: "Sum", 1: "Avg", 3: "Min", 4: "Max"}


def proj(field: dict, display: str | None = None) -> dict:
    if "Aggregation" in field:
        inner = field["Aggregation"]["Expression"]["Column"]
        ent, prop = inner["Expression"]["SourceRef"]["Entity"], inner["Property"]
        fn = AGG[field["Aggregation"]["Function"]]
        p = {"field": field, "queryRef": f"{fn}({ent}.{prop})", "nativeQueryRef": f"{fn} of {prop}"}
    else:
        kind = "Column" if "Column" in field else "Measure"
        ent = field[kind]["Expression"]["SourceRef"]["Entity"]
        prop = field[kind]["Property"]
        p = {"field": field, "queryRef": f"{ent}.{prop}", "nativeQueryRef": prop}
    if display:
        p["displayName"] = display
    return p


def title(text: str, size: int = 12) -> dict:
    return {"title": [{"properties": {"show": lit(True), "text": lit(text), "fontSize": lit(float(size))}}]}


def container(name: str, x: int, y: int, w: int, h: int, z: int, visual: dict) -> dict:
    return {"$schema": VC, "name": name,
            "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z},
            "visual": visual}


def textbox(name, x, y, w, h, z, text, size=10, bold=False):
    run = {"value": text, "textStyle": {"fontSize": f"{size}pt"}}
    if bold:
        run["textStyle"]["fontWeight"] = "bold"
    return container(name, x, y, w, h, z, {"visualType": "textbox", "objects": {
        "general": [{"properties": {"paragraphs": [{"textRuns": [run]}]}}]}})


def card(name, x, y, w, h, z, m: dict, label: str):
    return container(name, x, y, w, h, z, {
        "visualType": "card",
        "query": {"queryState": {"Values": {"projections": [proj(m, label)]}}},
        "visualContainerObjects": title(label, 11)})


def slicer(name, x, y, w, h, z, field: dict, label: str, mode: str = "Dropdown", single: bool = False):
    objects = {"data": [{"properties": {"mode": lit(mode)}}]}
    if single:
        objects["selection"] = [{"properties": {"singleSelect": lit(True)}}]
    return container(name, x, y, w, h, z, {
        "visualType": "slicer", "query": {"queryState": {"Values": {"projections": [proj(field)]}}},
        "objects": objects, "visualContainerObjects": title(label, 10)})


def chart(name, x, y, w, h, z, vtype: str, roles: dict, ttl: str, sort: tuple | None = None, objects=None):
    q_ = {"queryState": {r: {"projections": ps} for r, ps in roles.items()}}
    if sort:
        q_["sortDefinition"] = {"sort": [{"field": sort[0], "direction": sort[1]}], "isDefaultSort": False}
    v = {"visualType": vtype, "query": q_, "visualContainerObjects": title(ttl), "drillFilterOtherVisuals": True}
    if objects:
        v["objects"] = objects
    return container(name, x, y, w, h, z, v)


def footer(name, z):
    return textbox(name, 20, 690, 1240, 26, z, FOOTER, 8)


def pages() -> dict[str, tuple[str, list[dict]]]:
    fe, pt = "fact_recall_event", "dim_product_type"
    p1 = [
        textbox("p1_title", 20, 10, 900, 40, 0, "FDA Recall & Quality Risk - Executive summary", 18, True),
        slicer("p1_sl_product", 20, 60, 220, 70, 1, col(pt, "product_type"), "Product type"),
        slicer("p1_sl_class", 250, 60, 220, 70, 2, col(fe, "classification"), "FDA class"),
        slicer("p1_sl_date", 480, 60, 400, 70, 3, col("dim_date", "date"), "Report date", mode="Between"),
        card("p1_card_t12", 20, 140, 300, 110, 4, meas(fe, "Events T12"), "Recall events, last 12 complete months"),
        card("p1_card_change", 330, 140, 300, 110, 5, meas(fe, "Change vs Prior 12m"), "Change vs prior 12 months"),
        card("p1_card_class1", 640, 140, 300, 110, 6, meas(fe, "Class I Share T12"), "Class I share, last 12 months"),
        card("p1_card_flags", 950, 140, 310, 110, 7, meas("dash_watchlist", "Flagged Categories"), "Flagged categories (risk watchlist)"),
        chart("p1_trend", 20, 260, 1240, 380, 8, "lineChart",
              {"Category": [proj(col("dim_date", "month_start"), "Report month")],
               "Y": [proj(meas(fe, "Events Complete Months"), "Recall events")],
               "Series": [proj(col(fe, "product_type"), "Product type")]},
              "Monthly recall events by product type (complete months; counts, not rates)"),
        container("p1_asof", 20, 645, 1240, 40, 9, {
            "visualType": "card", "query": {"queryState": {"Values": {"projections": [proj(meas("dash_kpi", "Data As Of"), "Data as of")]}}},
            "objects": {"labels": [{"properties": {"fontSize": lit(9.0)}}], "categoryLabels": [{"properties": {"show": lit(False)}}]}}),
    ]
    dc = "dim_category"
    p2 = [
        textbox("p2_title", 20, 10, 1240, 40, 0, "Pareto: which stated failure modes drive most recall events?", 18, True),
        slicer("p2_sl_weight", 20, 55, 300, 60, 1, col("dash_pareto", "weight"), "Weighting (count / severity / class1)", single=True),
        slicer("p2_sl_period", 330, 55, 400, 60, 2, col("dash_pareto", "period_key"), "Period (full / trailing 60 months)", single=True),
        textbox("p2_note", 740, 55, 520, 60, 3, "Bars = recall events per category, largest first; UNCLASSIFIED (no keyword rule matched) is always the last bar. Line = cumulative %. Click a bar to list its events below.", 9),
        chart("p2_pareto_drugs", 20, 120, 615, 330, 4, "lineClusteredColumnComboChart",
              {"Category": [proj(col(dc, "category_id"), "Category")],
               "Y": [proj(meas("dash_pareto", "Pareto Drugs"), "Events (drugs)")],
               "Y2": [proj(meas("dash_pareto", "Pareto Drugs Cum Pct"), "Cumulative %")],
               "Tooltips": [proj(meas("dash_pareto", "Pareto Drugs Sort"), "Sort key")]},
              "Drugs: a few categories account for most events",
              sort=(meas("dash_pareto", "Pareto Drugs Sort"), "Descending")),
        chart("p2_pareto_food", 645, 120, 615, 330, 5, "lineClusteredColumnComboChart",
              {"Category": [proj(col(dc, "category_id"), "Category")],
               "Y": [proj(meas("dash_pareto", "Pareto Food"), "Events (food)")],
               "Y2": [proj(meas("dash_pareto", "Pareto Food Cum Pct"), "Cumulative %")],
               "Tooltips": [proj(meas("dash_pareto", "Pareto Food Sort"), "Sort key")]},
              "Food: allergens and microbial contamination dominate",
              sort=(meas("dash_pareto", "Pareto Food Sort"), "Descending")),
        chart("p2_events", 20, 460, 1240, 225, 6, "tableEx",
              {"Values": [proj(col(fe, "event_id"), "Event"), proj(col(fe, "product_type"), "Type"),
                          proj(col(fe, "category_id"), "Category"), proj(col(fe, "classification"), "Class"),
                          proj(col("dim_firm", "firm_name"), "Recalling firm"),
                          proj(col(fe, "reason_for_recall"), "Reason for recall (FDA text)")]},
              "Event detail (click a Pareto bar to filter)"),
        footer("p2_footer", 7),
    ]
    sp = "dash_spc"
    p3 = [
        textbox("p3_title", 20, 10, 1240, 40, 0, "Control charts: is a category's recall activity unusual versus its 2015-2019 baseline?", 16, True),
        slicer("p3_sl_series", 20, 55, 300, 60, 1, col(sp, "series"), "Category series", single=True),
        slicer("p3_sl_chart", 330, 55, 280, 60, 2, col(sp, "chart_label"), "Chart type", single=True),
        card("p3_card_sel", 620, 55, 360, 60, 3, meas(sp, "SPC Selected Series"), "Showing"),
        card("p3_card_sig", 990, 55, 270, 60, 4, meas(sp, "SPC Signals After Baseline"), "Signalled months after baseline"),
        chart("p3_chart", 20, 125, 830, 330, 5, "lineChart",
              {"Category": [proj(col(sp, "month"), "Month")],
               "Y": [proj(meas(sp, "SPC Value"), "Value"), proj(meas(sp, "SPC CL"), "Centre line"),
                     proj(meas(sp, "SPC UCL"), "Upper control limit"), proj(meas(sp, "SPC LCL"), "Lower control limit"),
                     proj(meas(sp, "SPC Signal Point"), "Signal (special cause)")]},
              "Selected category: points outside the limits or long runs are signals",
              objects={"lineStyles": [{"properties": {"showMarker": lit(False)}},
                                      {"properties": {"showMarker": lit(True), "strokeWidth": lit(0)},
                                       "selector": {"metadata": "dash_spc.SPC Signal Point"}}]}),
        textbox("p3_explain", 860, 125, 400, 330, 6, "How to read this chart. " + TOOLTIP +
                " R1 = point beyond a control limit. R2 = 8 months in a row on the same side of the centre line. "
                "Limits are Laney-adjusted when months vary more than a simple count model expects.", 10),
        chart("p3_signals", 20, 460, 520, 225, 7, "tableEx",
              {"Values": [proj(col(sp, "month"), "Month"), proj(col(sp, "series"), "Series"),
                          proj(col(sp, "chart_label"), "Chart"), proj(col(sp, "signal_label"), "Rule")]},
              "Signal months (all series; filter with the slicers)"),
        chart("p3_top6", 550, 460, 710, 225, 8, "lineChart",
              {"Category": [proj(col(sp, "month"), "Month")],
               "Y": [proj(meas(sp, "Top6 Share"), "Share of month"), proj(meas(sp, "Top6 UCL"), "UCL")],
               "Rows": [proj(col(sp, "series"), "Series")]},
              "Top 6 categories (p-chart small multiples)"),
        footer("p3_footer", 9),
    ]
    wl = "dash_watchlist"
    p4 = [
        textbox("p4_title", 20, 10, 1240, 40, 0, "Risk watchlist: which failure modes deserve QA attention now? (triage, not prediction)", 16, True),
        slicer("p4_sl_product", 20, 55, 220, 60, 1, col(pt, "product_type"), "Product type"),
        textbox("p4_backtest", 250, 55, 1010, 60, 2, "Honest result: in a pre-registered backtest (10 yearly origins) this score did NOT beat naive baselines at predicting next-year increases (regression to the mean). Use it to triage attention; check 'Stability %' before acting.", 9),
        chart("p4_table", 20, 120, 820, 300, 3, "tableEx",
              {"Values": [proj(col(wl, "rank"), "Rank"), proj(col(wl, "product_type"), "Type"),
                          proj(col(dc, "category_id"), "Category"), proj(col(wl, "flag_label"), "Flag"),
                          proj(meas(wl, "Score"), "Score"), proj(col(wl, "stability_pct"), "Stability %"),
                          proj(col(wl, "why_flagged"), "Why flagged")]},
              "Ranked categories (latest complete month) - click a row for QA actions",
              sort=(meas(wl, "Score"), "Descending")),
        chart("p4_components", 850, 120, 410, 300, 4, "barChart",
              {"Category": [proj(col(dc, "category_id"), "Category")],
               "Y": [proj({"Aggregation": {"Expression": col("dash_watch_components", "weighted_contribution"), "Function": 0}}, "Contribution")],
               "Series": [proj(col("dash_watch_components", "component"), "Component")]},
              "What makes up each score (weighted components)"),
        chart("p4_actions", 20, 425, 820, 260, 5, "tableEx",
              {"Values": [proj(col("dash_actions", "category"), "Category"), proj(col("dash_actions", "phase"), "DMAIC phase"),
                          proj(col("dash_actions", "action"), "Recommended QA action"),
                          proj(col("dash_actions", "owner_function"), "Owner"), proj(col("dash_actions", "metric"), "Example metric"),
                          proj(col("dash_actions", "citation"), "Citation")]},
              "DMAIC QA actions for the selected category"),
        textbox("p4_limits", 850, 425, 410, 260, 6, "Limitations. Counts are FDA-recorded recall events with no production "
                "denominator, so they are not failure rates. FDA classification and enforcement priorities shape what is "
                "recorded. Categories come from keyword rules (~0.90 precision; Unclassified shown). USDA-FSIS meat/poultry "
                "recalls are excluded. " + DISCLAIMER, 9),
    ]
    return {"p1_exec": ("1 Executive summary", p1), "p2_pareto": ("2 Pareto", p2),
            "p3_spc": ("3 Control charts", p3), "p4_watchlist": ("4 Risk watchlist", p4)}


def write_report() -> None:
    d = RP / "definition"
    if d.exists():
        shutil.rmtree(d)
    (d / "pages").mkdir(parents=True)
    (RP / "definition.pbir").write_text(json.dumps({
        "$schema": f"{SCH}/item/report/definitionProperties/2.0.0/schema.json", "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}}, indent=2), encoding="utf-8")
    (d / "version.json").write_text(json.dumps({
        "$schema": f"{SCH}/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"}, indent=2),
        encoding="utf-8")
    (d / "report.json").write_text(json.dumps({
        "$schema": f"{SCH}/item/report/definition/report/3.0.0/schema.json",
        "themeCollection": {"baseTheme": {"name": "CY26SU10", "type": "SharedResources",
                                          "reportVersionAtImport": {"visual": "2.6.0", "report": "3.0.0", "page": "2.0.0"}}}},
        indent=2), encoding="utf-8")
    pg = pages()
    (d / "pages" / "pages.json").write_text(json.dumps({
        "$schema": f"{SCH}/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": list(pg), "activePageName": "p1_exec"}, indent=2), encoding="utf-8")
    for pname, (display, visuals) in pg.items():
        pdir = d / "pages" / pname
        (pdir / "visuals").mkdir(parents=True)
        (pdir / "page.json").write_text(json.dumps({
            "$schema": f"{SCH}/item/report/definition/page/2.0.0/schema.json", "name": pname,
            "displayName": display, "displayOption": "FitToPage", "height": 720, "width": 1280}, indent=2),
            encoding="utf-8")
        for v in visuals:
            vdir = pdir / "visuals" / v["name"]
            vdir.mkdir()
            (vdir / "visual.json").write_text(json.dumps(v, indent=2), encoding="utf-8")


def main() -> int:
    DASH.mkdir(exist_ok=True)
    write_model()
    write_report()
    (DASH / f"{NAME}.pbip").write_text(json.dumps({
        "$schema": f"{SCH}/pbip/pbipProperties/1.0.0/schema.json", "version": "1.0",
        "artifacts": [{"report": {"path": f"{NAME}.Report"}}], "settings": {"enableAutoRecovery": True}}, indent=2),
        encoding="utf-8")
    print("wrote", DASH / f"{NAME}.pbip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
