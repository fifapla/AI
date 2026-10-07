from typing import List, Dict, Any
import re

class KnowledgeGraphExtractor:
    def __init__(self):
        self.entity_pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"

    def extract_triplets(self, text: str) -> Dict[str, Any]:
        entities = list(set(re.findall(self.entity_pattern, text)))
        triplets: List[Dict[str, str]] = []
        
        if len(entities) >= 2:
            for i in range(len(entities) - 1):
                triplets.append({
                    "subject": entities[i],
                    "predicate": "RELATED_TO",
                    "object": entities[i+1]
                })

        return {
            "entity_count": len(entities),
            "entities": entities,
            "knowledge_triplets": triplets
        }

if __name__ == "__main__":
    extractor = KnowledgeGraphExtractor()
    sample_text = "LangChain and LlamaIndex interact with OpenAI models to improve RAG performance."
    graph = extractor.extract_triplets(sample_text)
    print("Extracted Graph Knowledge:", graph)
