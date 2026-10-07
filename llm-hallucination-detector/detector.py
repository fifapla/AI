from typing import Dict, Any, List

class HallucinationDetector:
    def __init__(self, confidence_threshold: float = 0.75):
        self.threshold = confidence_threshold

    def verify_factuality(self, context: str, response: str) -> Dict[str, Any]:
        context_words = set(context.lower().split())
        response_words = set(response.lower().split())
        
        if not response_words:
            return {"overlap_score": 0.0, "is_hallucination": True}

        overlap = len(context_words.intersection(response_words)) / len(response_words)
        overlap_score = round(overlap, 2)
        
        is_hallucination = overlap_score < self.threshold
        return {
            "factuality_score": overlap_score,
            "threshold": self.threshold,
            "is_hallucination": is_hallucination,
            "status": "FLAGGED_HALLUCINATION" if is_hallucination else "VERIFIED"
        }

if __name__ == "__main__":
    detector = HallucinationDetector(confidence_threshold=0.5)
    source_context = "Vector databases use approximate nearest neighbor search to index high dimensional embeddings."
    llm_output = "Vector databases use high dimensional embeddings for search."
    
    report = detector.verify_factuality(source_context, llm_output)
    print("Factuality Verification Report:", report)
