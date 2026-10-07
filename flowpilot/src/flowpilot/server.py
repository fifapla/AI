"""Webhook receiver: POST /events (optionally HMAC-signed), GET /approvals, POST /approvals/<id>/approve|reject."""
import hashlib
import hmac
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from .engine import Engine


def make_handler(engine: Engine, secret: str = ""):
    class H(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            b = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

        def _body(self):
            n = min(int(self.headers.get("Content-Length", "0")), 100_000)
            return self.rfile.read(n)

        def do_GET(self):
            if self.path == "/health":
                return self._send(200, {"status": "ok"})
            if self.path == "/approvals":
                return self._send(200, engine.store.pending_approvals())
            if self.path == "/dlq":
                return self._send(200, engine.store.dlq())
            self._send(404, {"error": "not found"})

        def do_POST(self):
            raw = self._body()
            if secret:
                sig = self.headers.get("X-Signature", "")
                good = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
                if not hmac.compare_digest(sig, good):
                    return self._send(401, {"error": "bad signature"})
            if self.path == "/events":
                try:
                    ev = json.loads(raw)
                    assert isinstance(ev, dict)
                except (json.JSONDecodeError, AssertionError):
                    return self._send(400, {"error": "event must be a JSON object"})
                return self._send(200, engine.handle(ev))
            parts = self.path.strip("/").split("/")
            if len(parts) == 3 and parts[0] == "approvals" and parts[1].isdigit() and parts[2] in ("approve", "reject"):
                return self._send(200, engine.decide(int(parts[1]), parts[2] == "approve"))
            self._send(404, {"error": "not found"})

        def log_message(self, *a):
            pass
    return H


def serve(engine: Engine, port: int = 8090, secret: str = ""):
    print(f"flowpilot listening on http://127.0.0.1:{port}")
    HTTPServer(("127.0.0.1", port), make_handler(engine, secret)).serve_forever()
