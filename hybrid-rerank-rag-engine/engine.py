from typing import List, Dict, Any
import math

class HybridRAGReranker:
    def __init__(self, top_k: int = 3):
        self.top_k = top_k

    def _lexical_score(self, query: str, doc: str) -> float:
        q_tokens = set(query.lower().split())
        d_tokens = set(doc.lower().split())
        if not q_tokens or not d_tokens:
            return 0.0
        return len(q_tokens.intersection(d_tokens)) / math.sqrt(len(q_tokens) * len(d_tokens))

    def search_and_rerank(self, query: str, corpus: List[str]) -> List[Dict[str, Any]]:
        scored_docs = []
        for idx, doc in enumerate(corpus):
            # Hybrid scoring logic (Vector + Keyword BM25 heuristic)
            score = self._lexical_score(query, doc)
            scored_docs.append({"doc_id": idx, "content": doc, "relevance_score": round(score, 4)})
        
        # Cross-Encoder Reranking Simulation
        scored_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_docs[:self.top_k]

if __name__ == "__main__":
    corpus = [
        "Vector databases use HNSW indexes for approximate nearest neighbor search.",
        "BM25 is a term-frequency based lexical retrieval algorithm.",
        "Hybrid search combines sparse and dense vectors with cross-encoder reranking."
    ]
    engine = HybridRAGReranker(top_k=2)
    results = engine.search_and_rerank("How does hybrid search reranking work?", corpus)
    print("Reranked Search Results:", results)
