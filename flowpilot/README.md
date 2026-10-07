# flowpilot — event-driven AI automation with guardrails

![CI](https://github.com/<your-user>/flowpilot/actions/workflows/ci.yml/badge.svg)
![python](https://img.shields.io/badge/python-3.10%2B-blue) ![license](https://img.shields.io/badge/license-MIT-green)

A production-minded automation engine. Events (support tickets here) are classified by transparent rules with an optional LLM fallback, fields are extracted, work is routed, and risky actions wait for a human. Everything is idempotent, retried with backoff, dead-lettered on failure, and audited.

> 🇪🇬 أتمتة بالذكاء الاصطناعي: تصنيف ← استخراج ← توجيه ← تنفيذ، مع إعادة المحاولة ومنع التكرار وطابور موافقات.

## Features
- YAML-defined workflow: rules, extractors, routes, approval policy
- Idempotency: the same event id never executes twice
- Retries with exponential backoff → dead-letter queue
- Human approval for configured labels or amounts over a threshold
- SQLite audit trail per event
- Webhook server with optional HMAC signature check

## How it works
```
event ─► dedupe ─► classify (rules → LLM fallback) ─► extract ─► policy ─┬─► action (retry/backoff) ─► done | DLQ
                                                                              └─► approval queue ─► human ─► action
```

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
PYTHONPATH=src python -m flowpilot run "I was charged twice, order #123456, refund please"
PYTHONPATH=src python -m flowpilot run "my account was hacked" --id t-9   # waits for approval
PYTHONPATH=src python -m flowpilot approvals
PYTHONPATH=src python -m flowpilot decide 1 approve
PYTHONPATH=src python -m flowpilot serve --port 8090 --secret s3cret
```

## Tests
```bash
python -m unittest discover -s tests -v     # or: pytest
```

## Honest limitations
- Demo actions write JSONL files to `outbox/`; real Slack/Jira/email actions are yours to plug in via the `actions` dict.
- Single-process SQLite — fine for a demo or small team, not horizontally scaled.
- Rules are regex; the LLM fallback is an interface, not a bundled model.

## Roadmap
- [ ] Real connectors (Slack, Jira, email)
- [ ] Worker queue for parallel processing
- [ ] Web UI for approvals

## License
MIT
