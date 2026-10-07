"""
mini_rag.py
-----------
A minimal, dependency-free Retrieval-Augmented Generation (RAG) pipeline.

Why this exists
================
Most "RAG demos" hide the retrieval step behind a vector-database SDK,
which makes it hard to actually show you understand what's happening.
This implementation builds the retrieval step from scratch using TF-IDF
and cosine similarity — no external libraries required — so every part
of the pipeline is readable and inspectable.

Pipeline stages
===============
1. Ingest   -> load .txt documents from a folder, split into chunks.
2. Index    -> build a TF-IDF vector for every chunk.
3. Retrieve -> embed the user query the same way, rank chunks by
               cosine similarity, return the top-k matches.
4. Generate -> produce a grounded answer that cites the exact source
               chunk it came from (no hallucinated claims).

Usage
=====
    python mini_rag.py                  # runs the demo queries below
    python mini_rag.py --interactive    # ask your own questions

Author: portfolio demo project
"""

from __future__ import annotations

import argparse
import glob
import math
import os
import re
from collections import Counter
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# 1. Ingestion
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    """A single retrievable unit of text, tied back to its source file."""
    text: str
    source_file: str
    chunk_index: int
    tf: Counter = field(default_factory=Counter, repr=False)

    @property
    def label(self) -> str:
        return f"{os.path.basename(self.source_file)} (chunk {self.chunk_index})"


def tokenize(text: str) -> list[str]:
    """Lowercase word tokenizer. Good enough for a demo corpus."""
    return re.findall(r"[a-zA-Z]+", text.lower())


def load_documents(folder: str) -> list[Chunk]:
    """
    Load every .txt file in `folder` and split it into chunks on blank
    lines, mimicking how a real ingestion pipeline would split a long
    policy document into semantically coherent pieces.
    """
    chunks: list[Chunk] = []
    for path in sorted(glob.glob(os.path.join(folder, "*.txt"))):
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        pieces = [p.strip() for p in raw.split("\n\n") if p.strip()]
        for i, piece in enumerate(pieces):
            chunks.append(Chunk(text=piece, source_file=path, chunk_index=i))
    return chunks


# ---------------------------------------------------------------------------
# 2. Indexing (TF-IDF, implemented from first principles)
# ---------------------------------------------------------------------------

class TfidfIndex:
    """
    A small TF-IDF index. Not optimized for scale — optimized for being
    readable, since the point of this file is to show the mechanics.
    """

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self._idf: dict[str, float] = {}
        self._build()

    def _build(self) -> None:
        n_docs = len(self.chunks)
        doc_freq: Counter = Counter()

        for chunk in self.chunks:
            tokens = tokenize(chunk.text)
            chunk.tf = Counter(tokens)
            for term in set(tokens):
                doc_freq[term] += 1

        # Smoothed IDF: log((N + 1) / (df + 1)) + 1, avoids division by zero
        # and avoids zeroing-out terms that appear in every document.
        for term, df in doc_freq.items():
            self._idf[term] = math.log((n_docs + 1) / (df + 1)) + 1

    def _vector(self, tf: Counter) -> dict[str, float]:
        total = sum(tf.values()) or 1
        return {
            term: (count / total) * self._idf.get(term, 0.0)
            for term, count in tf.items()
        }

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        shared = set(a) & set(b)
        if not shared:
            return 0.0
        dot = sum(a[t] * b[t] for t in shared)
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(self, query: str, top_k: int = 1) -> list[tuple[Chunk, float]]:
        query_vec = self._vector(Counter(tokenize(query)))
        scored = [
            (chunk, self._cosine(query_vec, self._vector(chunk.tf)))
            for chunk in self.chunks
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_k]


# ---------------------------------------------------------------------------
# 3 & 4. Retrieve + Generate (grounded answer, no hallucination)
# ---------------------------------------------------------------------------

CONFIDENCE_THRESHOLD = 0.15  # below this, we refuse to answer rather than guess


def answer_question(index: TfidfIndex, question: str) -> str:
    results = index.search(question, top_k=1)
    if not results:
        return "No documents indexed."

    best_chunk, score = results[0]
    if score < CONFIDENCE_THRESHOLD:
        return (
            "I don't have a confident match for that in the indexed documents "
            f"(best similarity score: {score:.2f}). I won't guess — try rephrasing, "
            "or this may genuinely not be covered."
        )

    return (
        f"{best_chunk.text}\n"
        f"[source: {best_chunk.label} | similarity: {score:.2f}]"
    )


# ---------------------------------------------------------------------------
# Demo runner
# ---------------------------------------------------------------------------

DEMO_QUESTIONS = [
    "How many annual leave days do I get?",
    "What are the standard working hours?",
    "Does medical insurance cover my children?",
    "Can I work remotely?",
    "What's the office dress code?",  # deliberately not in the corpus
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal dependency-free RAG demo.")
    parser.add_argument(
        "--docs", default="sample_docs", help="Folder of .txt documents to index."
    )
    parser.add_argument(
        "--interactive", action="store_true", help="Ask your own questions instead."
    )
    args = parser.parse_args()

    docs_path = os.path.join(os.path.dirname(__file__), args.docs)
    chunks = load_documents(docs_path)
    if not chunks:
        raise SystemExit(f"No .txt files found in {docs_path}")

    index = TfidfIndex(chunks)
    print(f"Indexed {len(chunks)} chunks from {docs_path}\n")

    if args.interactive:
        print("Ask a question (Ctrl+C to quit):")
        while True:
            try:
                q = input("\n> ")
            except (KeyboardInterrupt, EOFError):
                print("\nBye.")
                break
            if not q.strip():
                continue
            print(answer_question(index, q))
    else:
        for q in DEMO_QUESTIONS:
            print(f"Q: {q}")
            print(f"A: {answer_question(index, q)}\n")


if __name__ == "__main__":
    main()
