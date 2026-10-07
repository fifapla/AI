"""Workflow engine. A workflow is YAML: classification rules, field extractors, routes and a risk policy."""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

from .store import Store

Action = Callable[[Dict[str, Any]], Any]
Classifier = Callable[[str], Optional[Dict[str, Any]]]  # optional LLM fallback -> {"label":..., "confidence":...}


@dataclass
class Workflow:
    name: str
    rules: List[Dict[str, Any]]
    extract: Dict[str, str] = field(default_factory=dict)
    routes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    default_route: str = "triage_queue"
    require_approval_when: Dict[str, Any] = field(default_factory=dict)
    retries: int = 3
    min_confidence: float = 0.6


def load_workflow(path: str | Path) -> Workflow:
    d = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    for key in ("name", "rules"):
        if key not in d:
            raise ValueError(f"workflow is missing '{key}'")
    for r in d["rules"]:
        if not {"label", "any"} <= set(r):
            raise ValueError("every rule needs 'label' and 'any'")
        re.compile("|".join(r["any"]))
    return Workflow(**{k: v for k, v in d.items() if k in Workflow.__dataclass_fields__})


class Engine:
    def __init__(self, workflow: Workflow, store: Store, actions: Dict[str, Action], llm_classifier: Optional[Classifier] = None,
                 sleep: Callable[[float], None] = time.sleep):
        self.wf, self.store, self.actions, self.llm, self.sleep = workflow, store, actions, llm_classifier, sleep

    @staticmethod
    def key_for(event: Dict[str, Any]) -> str:
        return event.get("id") or hashlib.sha256(json.dumps(event, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:24]

    def classify(self, text: str) -> Dict[str, Any]:
        low = text.lower()
        best = None
        for rule in self.wf.rules:  # first matching rule wins -> predictable and auditable
            hits = [p for p in rule["any"] if re.search(p, low)]
            if hits:
                best = {"label": rule["label"], "confidence": min(1.0, 0.6 + 0.2 * len(hits)), "by": "rules"}
                break
        if best and best["confidence"] >= self.wf.min_confidence:
            return best
        if self.llm:
            out = self.llm(text)
            if out and out.get("label") in {r["label"] for r in self.wf.rules}:
                return {**out, "by": "llm"}
        return best or {"label": "unknown", "confidence": 0.0, "by": "none"}

    def extract(self, text: str) -> Dict[str, str]:
        out = {}
        for name, pattern in self.wf.extract.items():
            m = re.search(pattern, text, flags=re.I)
            if m:
                out[name] = m.group(1) if m.groups() else m.group(0)
        return out

    def needs_approval(self, label: str, fields: Dict[str, str]) -> bool:
        pol = self.wf.require_approval_when
        if label in pol.get("labels", []):
            return True
        amt = fields.get("amount")
        return bool(amt and pol.get("amount_over") is not None and float(amt) > float(pol["amount_over"]))

    def _run_action(self, key: str, name: str, payload: Dict[str, Any]) -> Any:
        last = None
        for attempt in range(1, self.wf.retries + 1):
            try:
                res = self.actions[name](payload)
                self.store.audit(key, "action", {"name": name, "attempt": attempt, "ok": True})
                return res
            except Exception as e:
                last = e
                self.store.audit(key, "action", {"name": name, "attempt": attempt, "ok": False, "error": str(e)})
                if attempt < self.wf.retries:
                    self.sleep(min(30.0, 0.5 * 2 ** (attempt - 1)))  # exponential backoff
        raise last  # type: ignore[misc]

    def handle(self, event: Dict[str, Any]) -> Dict[str, Any]:
        key = self.key_for(event)
        prev = self.store.seen(key)
        if prev and prev["status"] in ("done", "pending_approval", "dead"):
            return {**prev["result"], "duplicate": True}
        text = str(event.get("text", ""))
        cls = self.classify(text)
        fields = self.extract(text)
        route = self.wf.routes.get(cls["label"], {}).get("action", self.wf.default_route)
        payload = {"event": event, "key": key, "classification": cls, "fields": fields, "action": route}
        self.store.audit(key, "classified", {"classification": cls, "fields": fields, "route": route})
        if self.needs_approval(cls["label"], fields):
            aid = self.store.enqueue_approval(key, payload)
            result = {"status": "pending_approval", "approval_id": aid, "label": cls["label"]}
            self.store.mark(key, "pending_approval", result)
            return result
        return self._execute(key, payload)

    def _execute(self, key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            out = self._run_action(key, payload["action"], payload)
            result = {"status": "done", "label": payload["classification"]["label"], "action": payload["action"], "output": out}
            self.store.mark(key, "done", result)
        except Exception as e:
            self.store.dead_letter(key, payload, str(e))
            result = {"status": "dead", "label": payload["classification"]["label"], "error": str(e)}
            self.store.mark(key, "dead", result)
        return result

    def decide(self, approval_id: int, approved: bool) -> Dict[str, Any]:
        item = self.store.resolve_approval(approval_id, approved)
        if not item:
            return {"status": "not_found"}
        self.store.audit(item["key"], "approval", {"approved": approved})
        if not approved:
            result = {"status": "rejected"}
            self.store.mark(item["key"], "done", result)
            return result
        return self._execute(item["key"], item["payload"])
