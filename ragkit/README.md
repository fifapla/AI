# ragkit — hybrid RAG with citations and evaluation

![CI](https://github.com/<your-user>/ragkit/actions/workflows/ci.yml/badge.svg)
![python](https://img.shields.io/badge/python-3.10%2B-blue) ![license](https://img.shields.io/badge/license-MIT-green)

Retrieval-augmented QA over local documents that refuses to guess. Hybrid retrieval (BM25 + hashed character-n-gram vectors, fused with Reciprocal Rank Fusion), Arabic-aware normalisation, answers with citations, a grounding guard, and an evaluation harness (hit@k, MRR).

> 🇪🇬 نظام RAG عربي/إنجليزي: بحث هجين (BM25 + متجهات) مع مصادر، ورفض الإجابة عند غياب الدليل، وقياس جودة الاسترجاع.

## Features
- Arabic + English: tashkeel/alef/ya normalisation, `ال` stripping, mixed-language corpus
- Sentence-aware chunking with overlap
- Hybrid retrieval; compare `bm25`, `vector`, `hybrid` with `ragkit eval`
- Grounding guard: if no retrieved chunk covers the question's content words, it says *I don't know*
- LLM mode verifies citations — fabricated `[7]` references are rejected and the extractive answer is used instead
- JSON HTTP API (`/ask`, `/health`), localhost only

## How it works
```
docs ─► chunk ─► BM25 index ─┐
                    └► hashed vectors ┴► RRF fusion ─► grounding guard ─► (extractive | LLM) answer + citations
```

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
PYTHONPATH=src python -m ragkit ask "When is express shipping free?"
PYTHONPATH=src python -m ragkit ask "متى يكون الشحن السريع مجاني؟"
PYTHONPATH=src python -m ragkit eval
PYTHONPATH=src python -m ragkit serve --port 8080
```

## Tests
```bash
python -m unittest discover -s tests -v     # or: pytest
```

## Honest limitations
- The bundled corpus is 7 short documents and the golden set has 10 questions, so the 1.0 hit@3 shows the pipeline works, not that it is state-of-the-art. Bring your own corpus and golden set.
- Hashed n-gram vectors are lexical-ish; swap in a neural embedder for true semantic matching (the `HybridIndex` interface is small).
- The grounding guard is a word-overlap heuristic, not an entailment model.

## Roadmap
- [ ] Pluggable neural embeddings
- [ ] Reranker stage
- [ ] Incremental indexing and PDF ingestion

## License
MIT
