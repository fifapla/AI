import argparse
import json
import sys

from .drift import drift_report
from .pipeline import load_data, train
from .registry import PromotionBlocked, Registry
from .serve import ModelServer, serve
from .tracking import Tracker


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="mlflowlite")
    ap.add_argument("--runs", default="mlruns"); ap.add_argument("--registry", default="registry"); ap.add_argument("--name", default="classifier")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("train"); t.add_argument("--model", choices=["logreg", "gboost"], default="logreg"); t.add_argument("--C", type=float, default=1.0)
    p = sub.add_parser("promote"); p.add_argument("version", type=int); p.add_argument("--min-gain", type=float, default=0.0)
    sub.add_parser("rollback")
    sub.add_parser("status")
    d = sub.add_parser("drift"); d.add_argument("--shift", type=float, default=0.0, help="demo: shift current data by this many std devs")
    s = sub.add_parser("serve"); s.add_argument("--port", type=int, default=8000)
    a = ap.parse_args(argv)
    reg = Registry(a.registry)
    if a.cmd == "train":
        v, m = train(load_data(), a.model, {"C": a.C} if a.model == "logreg" else {}, Tracker(a.runs), reg, "artifacts", a.name)
        print(json.dumps({"version": v, "metrics": m}, indent=2))
    elif a.cmd == "promote":
        try:
            print(reg.promote(a.name, a.version, min_gain=a.min_gain))
        except PromotionBlocked as e:
            print("BLOCKED:", e); return 1
    elif a.cmd == "rollback":
        print("rolled back to v", reg.rollback(a.name))
    elif a.cmd == "status":
        print(json.dumps(reg._load().get(a.name, []), indent=2))
    elif a.cmd == "drift":
        df = load_data().drop(columns=["target"]); cur = df.sample(frac=0.5, random_state=1) + a.shift * df.std()
        print(json.dumps(drift_report(df, cur), indent=2))
    else:
        serve(ModelServer(reg, a.name), a.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
