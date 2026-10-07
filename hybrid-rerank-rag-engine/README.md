# Hybrid Rerank RAG Engine

A high-performance Hybrid Retrieval-Augmented Generation (RAG) engine leveraging sparse (BM25 lexical) and dense vector search with cross-encoder reranking.

## Architectural Highlights
- **Hybrid Scoring**: Merges semantic vector space with keyword precision.
- **Top-K Reranker**: Filters and re-orders context chunks to maximize context fidelity.


**Note:** this implementation only computes lexical (Jaccard-style) overlap - there is no dense vector search and no real cross-encoder reranker here. The names in the architecture section describe the target design; this file is a simplified placeholder for that scoring step.
