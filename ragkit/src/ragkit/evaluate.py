"""Retrieval evaluation: hit@k and MRR on a golden set (JSONL of {question, expected_source})."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .rag import RAG


def evaluate(rag: RAG, golden_path: str | Path, k: int = 3, mode: str = "hybrid") -> Dict[str, float]:
    rows = [json.loads(l) for l in Path(golden_path).read_text(encoding="utf-8").splitlines() if l.strip()]
    hits, rr = 0, 0.0
    for r in rows:
        ranked = [c.source for c, _ in rag.retrieve(r["question"], k, mode)]
        if r["expected_source"] in ranked:
            hits += 1
            rr += 1.0 / (ranked.index(r["expected_source"]) + 1)
    n = len(rows) or 1
    return {"questions": len(rows), f"hit@{k}": round(hits / n, 3), "mrr": round(rr / n, 3), "mode": mode}
