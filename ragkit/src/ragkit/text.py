"""Arabic/English text normalisation, tokenisation and sentence-aware chunking."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

_TASHKEEL = re.compile(r"[\u064B-\u0652\u0640]")
STOP = {"the", "a", "an", "of", "to", "in", "is", "are", "and", "or", "for", "on", "at", "be", "by", "with", "what", "how", "do", "does",
        "can", "i", "my", "it", "this", "that", "من", "في", "على", "الى", "عن", "ما", "هل", "هو", "هي", "كم", "كيف", "ماذا", "او", "و"}


def normalize(text: str) -> str:
    t = _TASHKEEL.sub("", str(text).lower())
    t = re.sub("[إأآ]", "ا", t).replace("ى", "ي").replace("ة", "ه")
    return t


def tokenize(text: str, keep_stop: bool = False) -> List[str]:
    out = []
    for w in re.findall(r"\w+", normalize(text)):
        if len(w) > 3 and w.startswith("ال"):
            w = w[2:]
        if keep_stop or w not in STOP:
            out.append(w)
    return out


def split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?؟])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


@dataclass
class Chunk:
    source: str
    chunk_id: int
    text: str


def chunk_text(source: str, text: str, max_chars: int = 400, overlap_sentences: int = 1) -> List[Chunk]:
    """Pack whole sentences into chunks of ~max_chars; repeat the last sentence(s) so context isn't cut mid-thought."""
    text = re.sub(r"^#+\s*(.+?)\s*$", r"\1.", text, flags=re.M)  # markdown headings become short sentences
    sents, chunks, cur = split_sentences(text), [], []
    for s in sents:
        if cur and sum(len(x) + 1 for x in cur) + len(s) > max_chars:
            chunks.append(" ".join(cur))
            cur = cur[-overlap_sentences:] if overlap_sentences else []
        cur.append(s)
    if cur and (not chunks or " ".join(cur) != chunks[-1]):
        chunks.append(" ".join(cur))
    return [Chunk(source, i, c) for i, c in enumerate(chunks)]
