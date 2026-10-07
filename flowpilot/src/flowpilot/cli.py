import argparse
import json
import sys
from pathlib import Path

from .engine import Engine, load_workflow
from .store import Store


def default_actions(outbox: Path):
    """Demo actions write JSON lines to an outbox folder. Replace with Slack/Jira/email integrations in production."""
    outbox.mkdir(parents=True, exist_ok=True)

    def make(name):
        def act(payload):
            with (outbox / f"{name}.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps({"key": payload["key"], "fields": payload["fields"], "text": payload["event"].get("text", "")}, ensure_ascii=False) + "\n")
            return f"queued in {name}"
        return act
    return {n: make(n) for n in ("billing_queue", "tech_queue", "sales_queue", "security_queue", "triage_queue")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="flowpilot")
    ap.add_argument("--workflow", default="workflows/support_triage.yaml")
    ap.add_argument("--db", default="flowpilot.db")
    ap.add_argument("--outbox", default="outbox")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("text"); r.add_argument("--id", default="")
    sub.add_parser("approvals")
    d = sub.add_parser("decide"); d.add_argument("id", type=int); d.add_argument("decision", choices=["approve", "reject"])
    s = sub.add_parser("serve"); s.add_argument("--port", type=int, default=8090); s.add_argument("--secret", default="")
    a = ap.parse_args(argv)
    eng = Engine(load_workflow(a.workflow), Store(a.db), default_actions(Path(a.outbox)))
    if a.cmd == "run":
        print(json.dumps(eng.handle({"id": a.id or None, "text": a.text} if a.id else {"text": a.text}), ensure_ascii=False, indent=2))
    elif a.cmd == "approvals":
        print(json.dumps(eng.store.pending_approvals(), ensure_ascii=False, indent=2))
    elif a.cmd == "decide":
        print(json.dumps(eng.decide(a.id, a.decision == "approve"), ensure_ascii=False, indent=2))
    else:
        from .server import serve
        serve(eng, a.port, a.secret)
    return 0


if __name__ == "__main__":
    sys.exit(main())
