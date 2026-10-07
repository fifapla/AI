"""Model server: GET /health, GET /metrics, POST /predict {"features": {...}} - always serves the PRODUCTION version."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import joblib
import pandas as pd

from .registry import Registry


class ModelServer:
    def __init__(self, registry: Registry, name: str):
        self.registry, self.name = registry, name
        self.lock = threading.Lock()
        self.stats = {"requests": 0, "errors": 0, "latency_ms_sum": 0.0}
        self._ver, self._model, self._features = None, None, []

    def _ensure(self):
        prod = self.registry.production(self.name)
        if prod is None:
            raise LookupError("no production model")
        if prod["version"] != self._ver:  # hot-reload after promote/rollback
            self._model, self._features, self._ver = joblib.load(prod["path"]), prod["features"], prod["version"]

    def predict(self, features: dict) -> dict:
        with self.lock:
            self._ensure()
            missing = [f for f in self._features if f not in features]
            if missing:
                raise ValueError(f"missing features: {missing[:3]}")
            X = pd.DataFrame([[float(features[f]) for f in self._features]], columns=self._features)
            p = float(self._model.predict_proba(X)[0, 1])
            return {"prediction": int(p >= 0.5), "probability": round(p, 4), "model_version": self._ver}


def make_handler(srv: ModelServer):
    class H(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            b = json.dumps(obj).encode()
            self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b)))
            self.end_headers(); self.wfile.write(b)

        def do_GET(self):
            if self.path == "/health":
                ok = srv.registry.production(srv.name) is not None
                return self._send(200 if ok else 503, {"status": "ok" if ok else "no production model"})
            if self.path == "/metrics":
                s = srv.stats
                return self._send(200, {**s, "avg_latency_ms": round(s["latency_ms_sum"] / s["requests"], 3) if s["requests"] else 0})
            self._send(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/predict":
                return self._send(404, {"error": "not found"})
            t0 = time.perf_counter()
            srv.stats["requests"] += 1
            try:
                body = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length", "0")), 100_000)))
                out = srv.predict(body["features"])
                srv.stats["latency_ms_sum"] += (time.perf_counter() - t0) * 1000
                self._send(200, out)
            except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
                srv.stats["errors"] += 1
                self._send(400, {"error": str(e)})
            except LookupError as e:
                srv.stats["errors"] += 1
                self._send(503, {"error": str(e)})

        def log_message(self, *a):
            pass
    return H


def serve(srv: ModelServer, port: int = 8000):
    print(f"serving '{srv.name}' on http://127.0.0.1:{port}")
    HTTPServer(("127.0.0.1", port), make_handler(srv)).serve_forever()
