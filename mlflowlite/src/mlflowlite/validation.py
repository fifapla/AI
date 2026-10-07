"""Data validation: schema, null rates, ranges and label balance. Fails fast with a readable report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np
import pandas as pd


@dataclass
class ValidationReport:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate(df: pd.DataFrame, target: str, min_rows: int = 100, max_null_rate: float = 0.05, min_class_share: float = 0.05) -> ValidationReport:
    r = ValidationReport()
    if target not in df.columns:
        r.errors.append(f"missing target column '{target}'")
        return r
    if len(df) < min_rows:
        r.errors.append(f"only {len(df)} rows (minimum {min_rows})")
    feats = df.drop(columns=[target])
    non_numeric = [c for c in feats.columns if not pd.api.types.is_numeric_dtype(feats[c])]
    if non_numeric:
        r.errors.append(f"non-numeric feature columns: {non_numeric[:5]}")
    rates = df.isna().mean()
    for c, v in rates[rates > max_null_rate].items():
        r.errors.append(f"column '{c}' has {v:.1%} nulls (max {max_null_rate:.0%})")
    if df[target].isna().any():
        r.errors.append("target contains nulls")
    num = feats.select_dtypes(include=[np.number])
    if np.isinf(num.to_numpy(dtype=float)).any():
        r.errors.append("features contain infinite values")
    if (num.nunique() <= 1).any():
        r.warnings.append("constant feature columns: " + ", ".join(num.columns[num.nunique() <= 1][:5]))
    shares = df[target].value_counts(normalize=True)
    if len(shares) < 2:
        r.errors.append("target has a single class")
    elif shares.min() < min_class_share:
        r.warnings.append(f"imbalanced target: smallest class is {shares.min():.1%}")
    if df.duplicated().mean() > 0.2:
        r.warnings.append("more than 20% duplicate rows")
    return r
