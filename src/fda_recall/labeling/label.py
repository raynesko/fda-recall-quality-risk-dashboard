"""Interactive labeling tool for the gold set. Run it yourself in a terminal (labels must be human).

    python -m fda_recall.labeling.label                  # label data/labels/gold_v1.csv
    python -m fda_recall.labeling.label --file data/labels/gold_v1_relabel.csv   # T3.1.3 relabel

Shows one reason text at a time (no model output, no source flag). Saves after every answer, so you can
quit any time (q) and resume. Keys: category number, then optional secondary number; s = skip; q = quit.
Labeling minutes are appended to data/labels/labeling_time.log.
"""
from __future__ import annotations

import argparse
import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
TAX = ROOT / "data" / "reference" / "taxonomy.yaml"


def load_categories() -> list[dict]:
    return yaml.safe_load(TAX.read_text(encoding="utf-8"))["categories"]


def validate(df: pd.DataFrame, cats: list[dict]) -> list[str]:
    ids = {c["id"] for c in cats}
    errs = []
    lab = df[df.label != ""]
    bad = lab[~lab.label.isin(ids)]
    errs += [f"{r.event_id}: unknown label {r.label}" for r in bad.itertuples()]
    sec = lab[(lab.secondary_label != "") & ~lab.secondary_label.isin(ids)]
    errs += [f"{r.event_id}: unknown secondary {r.secondary_label}" for r in sec.itertuples()]
    if not df.event_id.is_unique:
        errs.append("duplicate event_id")
    return errs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=str(ROOT / "data" / "labels" / "gold_v1.csv"))
    a = ap.parse_args(argv)
    path = Path(a.file)
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    cats = load_categories()
    menu = "  ".join(f"{i}={c['id']}" for i, c in enumerate(cats, 1))
    todo = df.index[df.label == ""].tolist()
    print(f"{len(df) - len(todo)}/{len(df)} labeled. Guide: docs/domain/labeling-guide.md")
    t0 = time.time()
    done = 0
    for n, i in enumerate(todo, 1):
        print("\n" + "=" * 80)
        print(f"[{len(df) - len(todo) + n}/{len(df)}] {df.at[i, 'product_type']}  event {df.at[i, 'event_id']}")
        print(textwrap.fill(df.at[i, "reason_text"], 100))
        print("\n" + textwrap.fill(menu, 100))
        ans = input("label [secondary] (s=skip, q=quit): ").strip().lower().split()
        if not ans or ans[0] == "s":
            continue
        if ans[0] == "q":
            break
        try:
            nums = [int(x) for x in ans[:2]]
            assert all(1 <= x <= len(cats) for x in nums)
        except (ValueError, AssertionError):
            print("! invalid input, skipped")
            continue
        df.at[i, "label"] = cats[nums[0] - 1]["id"]
        df.at[i, "secondary_label"] = cats[nums[1] - 1]["id"] if len(nums) > 1 else ""
        df.at[i, "labeled_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        note = input("note (enter to skip): ").strip()
        if note:
            df.at[i, "notes"] = note
        df.to_csv(path, index=False, encoding="utf-8")
        done += 1
    minutes = (time.time() - t0) / 60
    with open(path.parent / "labeling_time.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}\t{path.name}\t{done} labels\t{minutes:.1f} min\n")
    errs = validate(df, cats)
    print(f"\nSaved. {int((df.label != '').sum())}/{len(df)} labeled; session {minutes:.1f} min. "
          f"Validation errors: {errs or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
