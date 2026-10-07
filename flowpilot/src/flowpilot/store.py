"""SQLite state: processed events (idempotency), approval queue, dead-letter queue and an append-only audit log."""
from __future__ import annotations

import json
import sqlite3
import time
from typing import Any, Dict, List, Optional


class Store:
    def __init__(self, path: str = ":memory:"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS events(key TEXT PRIMARY KEY, status TEXT, result TEXT, ts REAL);
            CREATE TABLE IF NOT EXISTS approvals(id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT, payload TEXT, status TEXT, ts REAL);
            CREATE TABLE IF NOT EXISTS dlq(id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT, payload TEXT, error TEXT, ts REAL);
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT, step TEXT, detail TEXT, ts REAL);
        """)

    def seen(self, key: str) -> Optional[Dict[str, Any]]:
        r = self.db.execute("SELECT status,result FROM events WHERE key=?", (key,)).fetchone()
        return {"status": r["status"], "result": json.loads(r["result"])} if r else None

    def mark(self, key: str, status: str, result: Dict[str, Any]) -> None:
        self.db.execute("INSERT OR REPLACE INTO events VALUES(?,?,?,?)", (key, status, json.dumps(result, ensure_ascii=False), time.time()))
        self.db.commit()

    def audit(self, key: str, step: str, detail: Any) -> None:
        self.db.execute("INSERT INTO audit(key,step,detail,ts) VALUES(?,?,?,?)", (key, step, json.dumps(detail, ensure_ascii=False, default=str), time.time()))
        self.db.commit()

    def enqueue_approval(self, key: str, payload: Dict[str, Any]) -> int:
        c = self.db.execute("INSERT INTO approvals(key,payload,status,ts) VALUES(?,?,?,?)", (key, json.dumps(payload, ensure_ascii=False), "pending", time.time()))
        self.db.commit()
        return int(c.lastrowid)

    def pending_approvals(self) -> List[Dict[str, Any]]:
        return [{"id": r["id"], "key": r["key"], "payload": json.loads(r["payload"])} for r in self.db.execute("SELECT * FROM approvals WHERE status='pending' ORDER BY id")]

    def resolve_approval(self, approval_id: int, approved: bool) -> Optional[Dict[str, Any]]:
        r = self.db.execute("SELECT * FROM approvals WHERE id=? AND status='pending'", (approval_id,)).fetchone()
        if not r:
            return None
        self.db.execute("UPDATE approvals SET status=? WHERE id=?", ("approved" if approved else "rejected", approval_id))
        self.db.commit()
        return {"key": r["key"], "payload": json.loads(r["payload"])}

    def dead_letter(self, key: str, payload: Dict[str, Any], error: str) -> None:
        self.db.execute("INSERT INTO dlq(key,payload,error,ts) VALUES(?,?,?,?)", (key, json.dumps(payload, ensure_ascii=False), error, time.time()))
        self.db.commit()

    def dlq(self) -> List[Dict[str, Any]]:
        return [dict(r) for r in self.db.execute("SELECT key,error FROM dlq ORDER BY id")]

    def audit_trail(self, key: str) -> List[Dict[str, Any]]:
        return [{"step": r["step"], "detail": json.loads(r["detail"])} for r in self.db.execute("SELECT step,detail FROM audit WHERE key=? ORDER BY id", (key,))]
