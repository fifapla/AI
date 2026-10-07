"""Minimal JSON API: POST /ask {"question": "..."} -> answer + citations. Binds to localhost only."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from .rag import RAG


def make_handler(rag: RAG):
    class H(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

        def do_GET(self):
            self._send(200, {"status": "ok"}) if self.path == "/health" else self._send(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/ask":
                return self._send(404, {"error": "not found"})
            try:
                n = int(self.headers.get("Content-Length", "0"))
                q = json.loads(self.rfile.read(min(n, 10_000)) or b"{}").get("question", "").strip()
            except (ValueError, json.JSONDecodeError):
                return self._send(400, {"error": "invalid JSON"})
            if not q:
                return self._send(400, {"error": "question is required"})
            r = rag.ask(q)
            self._send(200, {"answer": r.text, "grounded": r.grounded, "citations": r.citations})

        def log_message(self, *a):
            pass
    return H


def serve(rag: RAG, port: int = 8080):
    print(f"ragkit listening on http://127.0.0.1:{port}")
    HTTPServer((__import__("os").environ.get("BIND_HOST", "127.0.0.1"), port), make_handler(rag)).serve_forever()
