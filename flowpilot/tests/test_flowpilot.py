import hashlib
import hmac
import json
import pathlib
import sys
import threading
import unittest
import urllib.request
from http.server import HTTPServer

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from flowpilot import Engine, Store, load_workflow  # noqa: E402
from flowpilot.server import make_handler  # noqa: E402

WF = load_workflow(ROOT / "workflows" / "support_triage.yaml")


def make(actions=None, llm=None):
    calls = []
    base = {n: (lambda p, n=n: calls.append((n, p["key"])) or "ok") for n in ("billing_queue", "tech_queue", "sales_queue", "security_queue", "triage_queue")}
    base.update(actions or {})
    return Engine(WF, Store(), base, llm, sleep=lambda s: None), calls


class Classify(unittest.TestCase):
    def test_rules_and_extraction(self):
        e, _ = make()
        self.assertEqual(e.classify("I was charged twice, need a refund")["label"], "billing")
        self.assertEqual(e.classify("الموقع لا يعمل عندي")["label"], "technical")
        f = e.extract("Order #123456 charged $49.90, mail me at a.b@x.com")
        self.assertEqual((f["order_id"], f["amount"], f["email"]), ("123456", "49.90", "a.b@x.com"))

    def test_llm_fallback_only_when_rules_fail_and_label_is_valid(self):
        e, _ = make(llm=lambda t: {"label": "sales", "confidence": 0.8})
        self.assertEqual(e.classify("thinking about buying for my company")["by"], "llm")
        e2, _ = make(llm=lambda t: {"label": "made_up", "confidence": 0.99})
        self.assertEqual(e2.classify("thinking about buying for my company")["label"], "unknown")


class Flow(unittest.TestCase):
    def test_routes_and_is_idempotent(self):
        e, calls = make()
        r1 = e.handle({"id": "e1", "text": "refund for my invoice please"})
        r2 = e.handle({"id": "e1", "text": "refund for my invoice please"})
        self.assertEqual((r1["status"], r2.get("duplicate")), ("done", True))
        self.assertEqual(calls, [("billing_queue", "e1")])  # action ran exactly once

    def test_unknown_goes_to_triage(self):
        e, calls = make()
        e.handle({"id": "e2", "text": "hello there"})
        self.assertEqual(calls[0][0], "triage_queue")

    def test_retry_then_success(self):
        state = {"n": 0}

        def flaky(p):
            state["n"] += 1
            if state["n"] < 3:
                raise ConnectionError("down")
            return "ok"
        e, _ = make({"tech_queue": flaky})
        self.assertEqual(e.handle({"id": "e3", "text": "app crash on start"})["status"], "done")
        self.assertEqual(state["n"], 3)

    def test_exhausted_retries_go_to_dlq(self):
        def broken(p):
            raise RuntimeError("boom")
        e, _ = make({"tech_queue": broken})
        r = e.handle({"id": "e4", "text": "error 500"})
        self.assertEqual(r["status"], "dead")
        self.assertEqual(e.store.dlq()[0]["key"], "e4")
        self.assertEqual(e.handle({"id": "e4", "text": "error 500"})["duplicate"], True)

    def test_approval_gate(self):
        e, calls = make()
        r = e.handle({"id": "e5", "text": "I was charged $900 by mistake"})
        self.assertEqual(r["status"], "pending_approval")
        self.assertEqual(calls, [])  # nothing executed before a human decides
        out = e.decide(r["approval_id"], True)
        self.assertEqual((out["status"], calls[0][0]), ("done", "billing_queue"))
        self.assertEqual(e.decide(r["approval_id"], True)["status"], "not_found")  # cannot approve twice

    def test_rejection_executes_nothing(self):
        e, calls = make()
        r = e.handle({"id": "e6", "text": "my account was hacked"})
        self.assertEqual(r["status"], "pending_approval")
        self.assertEqual(e.decide(r["approval_id"], False)["status"], "rejected")
        self.assertEqual(calls, [])

    def test_audit_trail(self):
        e, _ = make()
        e.handle({"id": "e7", "text": "need a demo and a quote"})
        steps = [s["step"] for s in e.store.audit_trail("e7")]
        self.assertEqual(steps, ["classified", "action"])


class Config(unittest.TestCase):
    def test_invalid_workflow_rejected(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write("name: x\nrules:\n  - label: a\n")
        with self.assertRaises(ValueError):
            load_workflow(f.name)


class Http(unittest.TestCase):
    def test_signed_webhook(self):
        e, _ = make()
        srv = HTTPServer(("127.0.0.1", 0), make_handler(e, secret="s3cret"))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_port}/events"
        body = json.dumps({"id": "h1", "text": "pricing for enterprise plan"}).encode()
        try:
            good = hmac.new(b"s3cret", body, hashlib.sha256).hexdigest()
            ok = urllib.request.urlopen(urllib.request.Request(url, data=body, headers={"X-Signature": good}, method="POST"), timeout=5)
            self.assertEqual(json.loads(ok.read())["label"], "sales")
            with self.assertRaises(urllib.error.HTTPError) as cm:
                urllib.request.urlopen(urllib.request.Request(url, data=body, headers={"X-Signature": "bad"}, method="POST"), timeout=5)
            self.assertEqual(cm.exception.code, 401)
        finally:
            srv.shutdown()


if __name__ == "__main__":
    unittest.main()
