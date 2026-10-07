"""Model registry with versions, stages (none -> staging -> production -> archived) and a promotion gate."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

STAGES = ("none", "staging", "production", "archived")


class PromotionBlocked(Exception):
    pass


class Registry:
    def __init__(self, root: str | Path = "registry"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index = self.root / "index.json"
        if not self.index.exists():
            self._save({})

    def _load(self) -> Dict[str, List[Dict[str, Any]]]:
        return json.loads(self.index.read_text(encoding="utf-8"))

    def _save(self, d) -> None:
        self.index.write_text(json.dumps(d, indent=2), encoding="utf-8")

    def register(self, name: str, model_file: str | Path, metrics: Dict[str, float], run_id: str, features: List[str]) -> int:
        d = self._load()
        versions = d.setdefault(name, [])
        v = len(versions) + 1
        dest = self.root / name / f"v{v}"
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(model_file, dest / "model.joblib")
        versions.append({"version": v, "stage": "none", "metrics": metrics, "run_id": run_id, "features": features, "path": str(dest / "model.joblib")})
        self._save(d)
        return v

    def get(self, name: str, version: int) -> Dict[str, Any]:
        for r in self._load().get(name, []):
            if r["version"] == version:
                return r
        raise KeyError(f"{name} v{version} not found")

    def production(self, name: str) -> Optional[Dict[str, Any]]:
        return next((r for r in self._load().get(name, []) if r["stage"] == "production"), None)

    def promote(self, name: str, version: int, metric: str = "f1", min_gain: float = 0.0, max_regression: Dict[str, float] | None = None) -> str:
        """Gate: the candidate must beat production on `metric` by `min_gain` and not regress other metrics beyond tolerance."""
        d = self._load()
        cand = next((r for r in d.get(name, []) if r["version"] == version), None)
        if cand is None:
            raise KeyError(f"{name} v{version} not found")
        prod = next((r for r in d[name] if r["stage"] == "production"), None)
        if prod:
            gain = cand["metrics"][metric] - prod["metrics"][metric]
            if gain < min_gain:
                raise PromotionBlocked(f"{metric} gain {gain:+.4f} is below the required {min_gain:+.4f}")
            for m, tol in (max_regression or {}).items():
                drop = prod["metrics"].get(m, 0) - cand["metrics"].get(m, 0)
                if drop > tol:
                    raise PromotionBlocked(f"{m} regressed by {drop:.4f} (tolerance {tol})")
            prod["stage"] = "archived"
        cand["stage"] = "production"
        self._save(d)
        return f"{name} v{version} is now production"

    def rollback(self, name: str) -> int:
        d = self._load()
        vs = d.get(name, [])
        cur = next((r for r in vs if r["stage"] == "production"), None)
        prev = [r for r in vs if r["stage"] == "archived"]
        if not cur or not prev:
            raise PromotionBlocked("nothing to roll back to")
        target = max(prev, key=lambda r: r["version"])
        cur["stage"], target["stage"] = "archived", "production"
        self._save(d)
        return target["version"]
