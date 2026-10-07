from typing import List, Dict

class RAGEvaluator:
    @staticmethod
    def exact_match_score(prediction: str, ground_truth: str) -> float:
        return 1.0 if prediction.strip().lower() == ground_truth.strip().lower() else 0.0

    @staticmethod
    def token_overlap_score(prediction: str, context: str) -> float:
        pred_tokens = set(prediction.lower().split())
        ctx_tokens = set(context.lower().split())
        if not pred_tokens: return 0.0
        overlap = pred_tokens.intersection(ctx_tokens)
        return round(len(overlap) / len(pred_tokens), 2)

    def evaluate(self, prediction: str, context: str, ground_truth: str) -> Dict[str, float]:
        return {
            "faithfulness_score": self.token_overlap_score(prediction, context),
            "exact_match": self.exact_match_score(prediction, ground_truth)
        }

if __name__ == "__main__":
    evaluator = RAGEvaluator()
    res = evaluator.evaluate(
        prediction="RAG uses vector embeddings",
        context="Vector embeddings are used by RAG models for semantic retrieval.",
        ground_truth="RAG uses vector embeddings"
    )
    print("Evaluation Metrics:", res)
