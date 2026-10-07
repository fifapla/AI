"""BM25 + hashed char-ngram vectors, fused with Reciprocal Rank Fusion. numpy only; deterministic hashing."""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from .text import Chunk, normalize, tokenize


class BM25:
    def __init__(self, docs: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b, self.docs = k1, b, docs
        self.tf = [Counter(d) for d in docs]
        self.len = np.array([len(d) for d in docs], dtype=float)
        self.avg = float(self.len.mean()) if len(docs) else 0.0
        df: Counter = Counter()
        for d in docs:
            df.update(set(d))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: List[str]) -> np.ndarray:
        s = np.zeros(len(self.docs))
        for t in set(query):
            idf = self.idf.get(t)
            if idf is None:
                continue
            for i, tf in enumerate(self.tf):
                f = tf.get(t, 0)
                if f:
                    s[i] += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.len[i] / (self.avg or 1)))
        return s


class HashingEmbedder:
    """Signed feature hashing of word unigrams + character trigrams. No model download, stable across runs."""

    def __init__(self, dim: int = 1024):
        self.dim = dim

    def _h(self, feat: str) -> Tuple[int, float]:
        d = hashlib.blake2b(feat.encode("utf-8"), digest_size=8).digest()
        v = int.from_bytes(d, "little")
        return v % self.dim, 1.0 if (v >> 63) & 1 else -1.0

    def embed(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim)
        for w in tokenize(text):
            i, sgn = self._h("w:" + w)
            v[i] += 2.0 * sgn
            padded = f"#{w}#"
            for j in range(len(padded) - 2):
                i, sgn = self._h("c:" + padded[j:j + 3])
                v[i] += sgn
        n = np.linalg.norm(v)
        return v / n if n else v


def rrf(rankings: List[List[int]], k: int = 60) -> Dict[int, float]:
    fused: Dict[int, float] = {}
    for r in rankings:
        for pos, idx in enumerate(r):
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (k + pos + 1)
    return fused


class HybridIndex:
    def __init__(self, chunks: List[Chunk], dim: int = 1024):
        self.chunks, self.dim = chunks, dim
        self.embedder = HashingEmbedder(dim)
        self.bm25 = BM25([tokenize(c.text) for c in chunks])
        self.matrix = np.vstack([self.embedder.embed(c.text) for c in chunks]) if chunks else np.zeros((0, dim))

    def search(self, query: str, k: int = 4, mode: str = "hybrid") -> List[Tuple[Chunk, Dict[str, float]]]:
        if not self.chunks:
            return []
        bm = self.bm25.scores(tokenize(query))
        cos = self.matrix @ self.embedder.embed(query)
        bm_rank = [int(i) for i in np.argsort(-bm, kind="stable") if bm[i] > 0]
        cos_rank = [int(i) for i in np.argsort(-cos, kind="stable")[: max(k * 3, 10)]]
        if mode == "bm25":
            order = {i: bm[i] for i in bm_rank}
        elif mode == "vector":
            order = {i: cos[i] for i in cos_rank}
        else:
            order = rrf([bm_rank, cos_rank])
        top = sorted(order, key=lambda i: (-order[i], i))[:k]
        return [(self.chunks[i], {"fused": float(order[i]), "bm25": float(bm[i]), "cosine": float(cos[i])}) for i in top]

    def save(self, folder: str | Path) -> None:
        p = Path(folder)
        p.mkdir(parents=True, exist_ok=True)
        (p / "chunks.json").write_text(json.dumps([c.__dict__ for c in self.chunks], ensure_ascii=False), encoding="utf-8")
        (p / "meta.json").write_text(json.dumps({"dim": self.dim}), encoding="utf-8")

    @classmethod
    def load(cls, folder: str | Path) -> "HybridIndex":
        p = Path(folder)
        raw = json.loads((p / "chunks.json").read_text(encoding="utf-8"))
        return cls([Chunk(**r) for r in raw], json.loads((p / "meta.json").read_text())["dim"])
