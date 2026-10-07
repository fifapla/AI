from typing import Dict, Optional, Any
import math

class SemanticCache:
    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
        self.cache: Dict[str, str] = {}

    def _simulated_embedding_similarity(self, q1: str, q2: str) -> float:
        words1, words2 = set(q1.lower().split()), set(q2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        return len(intersection) / math.sqrt(len(words1) * len(words2))

    def get(self, query: str) -> Optional[str]:
        for cached_query, response in self.cache.items():
            sim = self._simulated_embedding_similarity(query, cached_query)
            if sim >= self.threshold:
                return response
        return None

    def set(self, query: str, response: str) -> None:
        self.cache[query] = response

if __name__ == "__main__":
    cache = SemanticCache(similarity_threshold=0.7)
    cache.set("How do I setup RAG with Python?", "Use LangChain or LlamaIndex with a Vector DB.")
    
    result = cache.get("How to setup RAG in Python?")
    print("Cache Hit Result:", result)
