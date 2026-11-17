"""Single source of truth for every number that may appear in README/slides/resume.

    record_metric("clf.macro_f1", 0.81, source="classify/model.py", label="achieved")

label: "achieved" (produced by code) or "target" (a goal; never presented as a result).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "results" / "metrics.json"
LABELS = ("achieved", "target")


def _jsonable(v):
    try:
        import numpy as np
        if isinstance(v, np.generic):
            return v.item()
    except ImportError:  # pragma: no cover
        pass
    return v


def record_metric(key: str, value, source: str, label: str = "achieved", note: str = "",
                  path: Path = DEFAULT_PATH) -> None:
    if label not in LABELS:
        raise ValueError(f"label must be one of {LABELS}, got {label!r}")
    if not key or "." not in key:
        raise ValueError("key must look like '<area>.<name>'")
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    data[key] = {"value": _jsonable(value), "label": label, "source": source,
                 "recorded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 **({"note": note} if note else {})}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def load_metrics(path: Path = DEFAULT_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else {}
