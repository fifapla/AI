"""Experiment tracking on disk: one JSON per run with params, metrics, data fingerprint and the artifact path."""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


def data_fingerprint(df: pd.DataFrame) -> str:
    h = pd.util.hash_pandas_object(df, index=True).values.tobytes()
    return hashlib.sha256(h + ",".join(map(str, df.columns)).encode()).hexdigest()[:16]


class Tracker:
    def __init__(self, root: str | Path = "mlruns"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def log_run(self, experiment: str, params: Dict[str, Any], metrics: Dict[str, float], fingerprint: str, artifact: str = "") -> str:
        run_id = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        rec = {"run_id": run_id, "experiment": experiment, "params": params, "metrics": metrics, "data_fingerprint": fingerprint, "artifact": artifact, "ts": time.time()}
        (self.root / f"{run_id}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
        return run_id

    def runs(self, experiment: str | None = None) -> List[Dict[str, Any]]:
        out = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(self.root.glob("*.json"))]
        return [r for r in out if experiment in (None, r["experiment"])]

    def best(self, metric: str, experiment: str | None = None) -> Dict[str, Any] | None:
        rs = self.runs(experiment)
        return max(rs, key=lambda r: r["metrics"].get(metric, float("-inf"))) if rs else None
