"""Train + evaluate + track + register. Uses scikit-learn's bundled breast-cancer dataset so it runs offline."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

import joblib
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .registry import Registry
from .tracking import Tracker, data_fingerprint
from .validation import validate

MODELS = {
    "logreg": lambda p: make_pipeline(StandardScaler(), LogisticRegression(max_iter=500, C=p.get("C", 1.0), random_state=0)),
    "gboost": lambda p: make_pipeline(StandardScaler(), GradientBoostingClassifier(n_estimators=p.get("n_estimators", 100), max_depth=p.get("max_depth", 3), random_state=0)),
}


def load_data() -> pd.DataFrame:
    d = load_breast_cancer(as_frame=True)
    df = d.frame.copy()
    df.columns = [c.replace(" ", "_") for c in df.columns]
    return df  # column 'target' (1 = benign)


def evaluate(model, X, y) -> Dict[str, float]:
    pred, proba = model.predict(X), model.predict_proba(X)[:, 1]
    return {"accuracy": accuracy_score(y, pred), "precision": precision_score(y, pred), "recall": recall_score(y, pred),
            "f1": f1_score(y, pred), "roc_auc": roc_auc_score(y, proba)}


def train(df: pd.DataFrame, model_name: str, params: Dict[str, Any], tracker: Tracker, registry: Registry, workdir: str | Path,
          name: str = "classifier", seed: int = 42) -> Tuple[int, Dict[str, float]]:
    rep = validate(df, "target")
    if not rep.ok:
        raise ValueError("data validation failed: " + "; ".join(rep.errors))
    X, y = df.drop(columns=["target"]), df["target"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, stratify=y, random_state=seed)
    model = MODELS[model_name](params).fit(Xtr, ytr)
    metrics = {k: round(float(v), 4) for k, v in evaluate(model, Xte, yte).items()}
    Path(workdir).mkdir(parents=True, exist_ok=True)
    f = Path(workdir) / f"{model_name}.joblib"
    joblib.dump(model, f)
    run_id = tracker.log_run(name, {"model": model_name, **params, "seed": seed}, metrics, data_fingerprint(df), str(f))
    version = registry.register(name, f, metrics, run_id, list(X.columns))
    return version, metrics
