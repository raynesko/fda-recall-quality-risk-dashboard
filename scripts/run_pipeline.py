"""Run the whole pipeline end to end, in dependency order (T7.1.3).

    python scripts/run_pipeline.py              # from existing raw files in data/raw/
    python scripts/run_pipeline.py --download   # first fetch today's openFDA bulk files (network)
    python scripts/run_pipeline.py --skip-pbip  # do not regenerate the Power BI project

Not re-run here (one-time, human/LLM-in-the-loop steps whose outputs are versioned inputs):
gold-set sampling (labeling/sample.py) and labeling itself (data/labels/*.csv), and the narrative EDA
notebook (notebooks/03_text_eda.ipynb).
"""
from __future__ import annotations

import argparse
import importlib
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))  # works with or without `pip install -e .`
ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")}
STEPS = [
    ("fda_recall.clean", "clean products, dedupe to events, data-quality report"),
    ("fda_recall.model", "star schema (uncategorized pass)"),
    ("fda_recall.labeling.agreement", "LLM inter-annotator kappa"),
    ("fda_recall.classify.evaluate_rules", "keyword baseline on gold set"),
    ("fda_recall.classify.model", "TF-IDF + LR vs baseline (grouped CV)"),
    ("fda_recall.classify.final", "classify full corpus with production rules"),
    ("fda_recall.model", "star schema with categories"),
    ("fda_recall.analysis.pareto", "Pareto"),
    ("fda_recall.analysis.series", "monthly series"),
    ("fda_recall.analysis.spc", "control charts + false-alarm simulation"),
    ("fda_recall.analysis.trend", "trend tests"),
    ("fda_recall.risk.score", "risk score"),
    ("fda_recall.risk.backtest", "pre-registered backtest"),
    ("fda_recall.risk.sensitivity", "sensitivity"),
    ("fda_recall.actions", "QA action library"),
    ("fda_recall.dashboard", "dashboard tables + reconciliation"),
    ("fda_recall.pbip", "Power BI project"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--download", action="store_true", help="fetch openFDA bulk files first (network)")
    ap.add_argument("--skip-pbip", action="store_true")
    a = ap.parse_args()
    steps = list(STEPS)
    if a.download:
        steps.insert(0, ("fda_recall.ingest", "download openFDA bulk files"))
    if a.skip_pbip:
        steps = [s for s in steps if s[0] != "fda_recall.pbip"]
    t_all = time.time()
    for i, (mod, desc) in enumerate(steps, 1):
        t0 = time.time()
        print(f"[{i:02d}/{len(steps)}] {mod}: {desc}", flush=True)
        importlib.import_module(mod)  # fail fast on import errors
        r = subprocess.run([sys.executable, "-m", mod], cwd=ROOT, env=ENV, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-3000:], r.stderr[-3000:], sep="\n")
            print(f"FAILED at {mod}")
            return r.returncode
        print(f"        ok ({time.time() - t0:.0f}s)")
    print(f"pipeline complete in {time.time() - t_all:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
