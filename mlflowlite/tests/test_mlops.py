import json
import pathlib
import sys
import tempfile
import threading
import unittest
import urllib.request
from http.server import HTTPServer

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from mlflowlite.drift import drift_report, psi  # noqa: E402
from mlflowlite.pipeline import load_data, train  # noqa: E402
from mlflowlite.registry import PromotionBlocked, Registry  # noqa: E402
from mlflowlite.serve import ModelServer, make_handler  # noqa: E402
from mlflowlite.tracking import Tracker, data_fingerprint  # noqa: E402
from mlflowlite.validation import validate  # noqa: E402

DF = load_data()


class Validation(unittest.TestCase):
    def test_clean_data_passes(self):
        self.assertTrue(validate(DF, "target").ok)

    def test_catches_problems(self):
        bad = DF.copy()
        bad.iloc[:60, 0] = np.nan
        self.assertTrue(any("nulls" in e for e in validate(bad, "target").errors))
        self.assertFalse(validate(DF.drop(columns=["target"]), "target").ok)
        self.assertFalse(validate(DF.head(20), "target").ok)
        one = DF.copy(); one["target"] = 1
        self.assertFalse(validate(one, "target").ok)


class Drift(unittest.TestCase):
    def test_no_drift_vs_shift(self):
        rng = np.random.default_rng(0)
        a = rng.normal(size=5000)
        self.assertLess(psi(a, rng.normal(size=5000)), 0.05)
        self.assertGreater(psi(a, rng.normal(loc=1.0, size=5000)), 0.25)

    def test_report_flags_shifted_columns(self):
        X = DF.drop(columns=["target"])
        same = drift_report(X, X.sample(frac=0.5, random_state=3))
        self.assertEqual(same["alerts"], [])
        shifted = X.copy(); shifted.iloc[:, :5] += 3 * X.iloc[:, :5].std()
        rep = drift_report(X, shifted)
        self.assertGreaterEqual(len(rep["alerts"]), 5)


class Lifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = pathlib.Path(self.tmp.name)
        self.tr, self.reg, self.work = Tracker(t / "runs"), Registry(t / "reg"), t / "art"

    def tearDown(self):
        self.tmp.cleanup()

    def test_train_track_register(self):
        v, m = train(DF, "logreg", {"C": 1.0}, self.tr, self.reg, self.work)
        self.assertEqual(v, 1)
        self.assertGreater(m["roc_auc"], 0.95)
        run = self.tr.runs()[0]
        self.assertEqual(run["data_fingerprint"], data_fingerprint(DF))
        self.assertEqual(self.reg.get("classifier", 1)["run_id"], run["run_id"])

    def test_training_is_reproducible(self):
        _, m1 = train(DF, "logreg", {"C": 1.0}, self.tr, self.reg, self.work)
        _, m2 = train(DF, "logreg", {"C": 1.0}, self.tr, self.reg, self.work)
        self.assertEqual(m1, m2)

    def test_refuses_bad_data(self):
        with self.assertRaises(ValueError):
            train(DF.head(30), "logreg", {}, self.tr, self.reg, self.work)

    def test_promotion_gate_and_rollback(self):
        train(DF, "logreg", {"C": 1.0}, self.tr, self.reg, self.work)
        self.reg.promote("classifier", 1)
        train(DF, "logreg", {"C": 0.00001}, self.tr, self.reg, self.work)  # heavily regularised -> worse
        with self.assertRaises(PromotionBlocked):
            self.reg.promote("classifier", 2, metric="f1", min_gain=0.0)
        self.assertEqual(self.reg.production("classifier")["version"], 1)
        train(DF, "gboost", {"n_estimators": 50}, self.tr, self.reg, self.work)
        self.reg.promote("classifier", 3, metric="f1", min_gain=-1.0)  # explicit override of the gain requirement
        self.assertEqual(self.reg.production("classifier")["version"], 3)
        self.assertEqual(self.reg.rollback("classifier"), 1)
        self.assertEqual(self.reg.production("classifier")["version"], 1)

    def test_server_serves_production_and_hot_reloads(self):
        train(DF, "logreg", {"C": 1.0}, self.tr, self.reg, self.work)
        srv = ModelServer(self.reg, "classifier")
        httpd = HTTPServer(("127.0.0.1", 0), make_handler(srv))
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{httpd.server_port}"
        row = {k: float(v) for k, v in DF.drop(columns=["target"]).iloc[0].items()}

        def post(body):
            r = urllib.request.Request(base + "/predict", data=json.dumps(body).encode(), method="POST")
            return json.loads(urllib.request.urlopen(r, timeout=5).read())
        try:
            with self.assertRaises(urllib.error.HTTPError) as cm:  # no production model yet
                post({"features": row})
            self.assertEqual(cm.exception.code, 503)
            self.reg.promote("classifier", 1)
            self.assertEqual(post({"features": row})["model_version"], 1)
            with self.assertRaises(urllib.error.HTTPError) as cm:
                post({"features": {"x": 1}})
            self.assertEqual(cm.exception.code, 400)
            self.assertEqual(json.loads(urllib.request.urlopen(base + "/metrics", timeout=5).read())["requests"], 3)
        finally:
            httpd.shutdown()


if __name__ == "__main__":
    unittest.main()
