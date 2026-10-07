"""Question answering over local documents: retrieve -> check grounding -> answer with citations."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from .index import HybridIndex
from .text import Chunk, chunk_text, split_sentences, tokenize

NO_ANSWER = "I could not find this in the documents. / لم أجد الإجابة في المستندات."


@dataclass
class Answer:
    text: str
    grounded: bool
    citations: List[str] = field(default_factory=list)
    contexts: List[str] = field(default_factory=list)


class RAG:
    def __init__(self, index: HybridIndex, llm: Optional[Callable[[str], str]] = None, min_overlap: float = 0.34, k: int = 4):
        self.index, self.llm, self.min_overlap, self.k = index, llm, min_overlap, k

    @classmethod
    def from_directory(cls, folder: str | Path, **kw) -> "RAG":
        chunks: List[Chunk] = []
        for p in sorted(Path(folder).rglob("*")):
            if p.suffix.lower() in (".md", ".txt") and p.is_file():
                chunks += chunk_text(p.name, p.read_text(encoding="utf-8", errors="replace"))
        if not chunks:
            raise ValueError(f"no .md/.txt documents found in {folder}")
        return cls(HybridIndex(chunks), **kw)

    def _overlap(self, query: str, text: str) -> float:
        q = set(tokenize(query))
        return len(q & set(tokenize(text))) / len(q) if q else 0.0

    def retrieve(self, query: str, k: Optional[int] = None, mode: str = "hybrid"):
        return self.index.search(query, k or self.k, mode)

    def ask(self, question: str) -> Answer:
        hits = self.retrieve(question)
        # Grounding guard: refuse unless a retrieved chunk actually shares enough of the question's content words.
        good = [(c, s) for c, s in hits if self._overlap(question, c.text) >= self.min_overlap]
        if not good:
            return Answer(NO_ANSWER, False)
        ctx = [f"[{i + 1}] ({c.source}#{c.chunk_id}) {c.text}" for i, (c, _) in enumerate(good)]
        cites = [f"{c.source}#{c.chunk_id}" for c, _ in good]
        if self.llm is None:
            return self._extractive(question, good, cites, ctx)
        prompt = ("Answer ONLY from the numbered context. Cite sources like [1]. If the context is insufficient, say you don't know.\n\n"
                  + "\n".join(ctx) + f"\n\nQuestion: {question}\nAnswer:")
        text = self.llm(prompt).strip()
        used = {int(n) for n in re.findall(r"\[(\d+)\]", text)}
        if not used or any(n < 1 or n > len(good) for n in used):  # missing or fabricated citations -> don't trust it
            return self._extractive(question, good, cites, ctx)
        return Answer(text, True, [cites[n - 1] for n in sorted(used)], ctx)

    def _extractive(self, question, good, cites, ctx) -> Answer:
        scored = []
        for ci, (c, _) in enumerate(good):
            for s in split_sentences(c.text):
                scored.append((self._overlap(question, s), -ci, s, ci))
        scored.sort(reverse=True)
        best = [x for x in scored[:2] if x[0] > 0] or scored[:1]
        text = " ".join(f"{s} [{ci + 1}]" for _, _, s, ci in best)
        return Answer(text, True, sorted({cites[ci] for *_, ci in best}), ctx)
