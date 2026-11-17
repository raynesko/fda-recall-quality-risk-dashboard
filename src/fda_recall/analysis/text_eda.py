"""Exploratory analysis of reason_for_recall text (T3.1.1). Called from notebooks/03_text_eda.ipynb."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.feature_extraction.text import CountVectorizer  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
FIG = ROOT / "reports" / "figures"


def near_dup_key(text: str) -> str:
    """Hash of text with digits, punctuation and whitespace removed (catches lot/date-only variants)."""
    t = re.sub(r"[^a-z]+", "", str(text).lower())
    return hashlib.md5(t.encode()).hexdigest()


def summary(ev: pd.DataFrame) -> pd.DataFrame:
    out = []
    for pt, g in ev.groupby("product_type"):
        out.append({"product_type": pt, "events": len(g),
                    "distinct_texts": g.reason_norm.nunique(),
                    "distinct_share": g.reason_norm.nunique() / len(g),
                    "near_dup_keys": g.reason_norm.map(near_dup_key).nunique(),
                    "near_dup_rate": 1 - g.reason_norm.map(near_dup_key).nunique() / len(g),
                    "median_chars": g.reason_norm.str.len().median()})
    return pd.DataFrame(out)


def top_prefixes(ev: pd.DataFrame, n: int = 20, width: int = 20) -> pd.DataFrame:
    return ev.reason_norm.str[:width].value_counts().head(n).rename_axis("prefix").reset_index(name="events")


def top_ngrams(texts: pd.Series, ngram: tuple[int, int], k: int = 30) -> pd.Series:
    cv = CountVectorizer(ngram_range=ngram, stop_words="english", token_pattern=r"(?u)\b[a-z][a-z]+\b")
    X = cv.fit_transform(texts)
    counts = pd.Series(X.sum(axis=0).A1, index=cv.get_feature_names_out())
    return counts.sort_values(ascending=False).head(k)


def plot_lengths(ev: pd.DataFrame, path: Path = FIG / "text_eda_length.png") -> Path:
    fig, ax = plt.subplots(figsize=(8, 4))
    for pt, g in ev.groupby("product_type"):
        ax.hist(g.reason_norm.str.len().clip(upper=600), bins=60, alpha=0.6, label=pt)
    ax.set(xlabel="reason_for_recall length (characters, clipped at 600)", ylabel="events",
           title="Food reasons are longer and more free-form than drug reasons")
    ax.legend()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def plot_ngrams(ev: pd.DataFrame, pt: str, ngram: tuple[int, int], label: str) -> Path:
    s = top_ngrams(ev.loc[ev.product_type == pt, "reason_norm"], ngram)
    fig, ax = plt.subplots(figsize=(7, 8))
    s[::-1].plot.barh(ax=ax, color="#4c72b0")
    ax.set(xlabel="events containing term (count of occurrences)", title=f"Top 30 {label} - {pt}")
    path = FIG / f"text_eda_{label}_{pt.lower()}.png"
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path
