from typing import List, Dict, Any
import math

class DynamicFewShotSelector:
    def __init__(self, examples: List[Dict[str, str]]):
        self.examples = examples

    def _similarity(self, query: str, candidate: str) -> float:
        q_words = set(query.lower().split())
        c_words = set(candidate.lower().split())
        if not q_words or not c_words:
            return 0.0
        return len(q_words.intersection(c_words)) / math.sqrt(len(q_words) * len(c_words))

    def select_k_samples(self, query: str, k: int = 2) -> List[Dict[str, str]]:
        scored = []
        for ex in self.examples:
            score = self._similarity(query, ex["input"])
            scored.append((score, ex))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:k]]

if __name__ == "__main__":
    dataset = [
        {"input": "Translate Python code to Rust", "output": "fn main() { ... }"},
        {"input": "Optimize SQL query index", "output": "CREATE INDEX idx_user ON ..."},
        {"input": "Refactor Python class", "output": "class CleanCode: ..."}
    ]
    selector = DynamicFewShotSelector(dataset)
    selected = selector.select_k_samples("How to convert Python script to Rust?", k=1)
    print("Dynamically Selected Few-Shot Samples:", selected)
