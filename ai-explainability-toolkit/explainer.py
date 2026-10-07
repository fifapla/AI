from typing import Dict, Any, List

class AIExplainabilityToolkit:
    def trace_decision_lineage(self, prompt: str, retrieved_chunks: List[str], final_response: str) -> Dict[str, Any]:
        chunk_attributions = []
        response_words = set(final_response.lower().split())

        for idx, chunk in enumerate(retrieved_chunks):
            chunk_words = set(chunk.lower().split())
            overlap = len(chunk_words.intersection(response_words))
            weight = round(overlap / max(1, len(response_words)), 2)
            chunk_attributions.append({"chunk_id": idx, "attribution_weight": weight})

        return {
            "prompt": prompt,
            "chunks_analyzed": len(retrieved_chunks),
            "attributions": chunk_attributions,
            "explainability_status": "HIGH_ATTRIBUTION" if chunk_attributions and max(a["attribution_weight"] for a in chunk_attributions) >= 0.5 else "LOW_ATTRIBUTION"
        }

if __name__ == "__main__":
    toolkit = AIExplainabilityToolkit()
    chunks = [
        "HNSW index provides fast approximate vector search.",
        "Quantization reduces memory footprint of embeddings."
    ]
    response = "HNSW index enables fast vector search."
    lineage = toolkit.trace_decision_lineage("How does HNSW work?", chunks, response)
    print("Explainability Lineage Report:", lineage)
