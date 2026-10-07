# mini_rag.py — Dependency-free RAG demo

A minimal Retrieval-Augmented Generation pipeline built from first
principles: no vector database, no embedding API, no external
libraries — just TF-IDF + cosine similarity, implemented directly in
Python's standard library.

## Why

Most RAG tutorials hide the retrieval math behind an SDK. This one
doesn't — every stage (ingest, index, retrieve, generate) is a plain
function you can read top to bottom in under 150 lines.

## Run it

```bash
python mini_rag.py                # runs 5 demo questions
python mini_rag.py --interactive  # ask your own questions
python mini_rag.py --docs my_docs # point at a different folder of .txt files
```

## What it demonstrates

- TF-IDF vectorization implemented manually (term frequency + smoothed
  inverse document frequency)
- Cosine similarity ranking over document chunks
- A confidence threshold: the system explicitly refuses to answer
  when no chunk is a good enough match, instead of hallucinating
- Every answer cites its exact source file and chunk

## Extending it

Swap `TfidfIndex` for a real embedding model (e.g. sentence-transformers)
and the rest of the pipeline (chunking, thresholding, citation) stays
the same — that's the point of keeping the interface simple.
