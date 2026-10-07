"""Drift monitoring: Population Stability Index + two-sample KS test per feature."""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


def psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    edges = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    e = np.histogram(expected, edges)[0] / len(expected)
    a = np.histogram(actual, edges)[0] / len(actual)
    e, a = np.clip(e, 1e-4, None), np.clip(a, 1e-4, None)
    return float(np.sum((a - e) * np.log(a / e)))


def drift_report(reference: pd.DataFrame, current: pd.DataFrame, psi_warn: float = 0.1, psi_alert: float = 0.25, ks_alpha: float = 0.01) -> Dict:
    feats = {}
    for c in reference.columns:
        p = psi(reference[c].to_numpy(float), current[c].to_numpy(float))
        ks = ks_2samp(reference[c], current[c])
        level = "alert" if p >= psi_alert else "warn" if p >= psi_warn else "ok"
        feats[c] = {"psi": round(p, 4), "ks_p": round(float(ks.pvalue), 6), "level": level, "ks_significant": bool(ks.pvalue < ks_alpha)}
    alerts = [c for c, v in feats.items() if v["level"] == "alert"]
    return {"features": feats, "alerts": alerts, "retrain_recommended": len(alerts) >= max(1, len(feats) // 10)}
