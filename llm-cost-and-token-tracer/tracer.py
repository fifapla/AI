import time
from typing import Dict, Any

class TokenCostTracer:
    MODEL_RATES = {
        "gpt-4o": {"input": 0.000005, "output": 0.000015},
        "gpt-3.5-turbo": {"input": 0.0000005, "output": 0.0000015},
        "claude-3-5-sonnet": {"input": 0.000003, "output": 0.000015}
    }

    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self.rates = self.MODEL_RATES.get(model_name, self.MODEL_RATES["gpt-4o"])

    def trace_request(self, prompt: str, completion: str, latency_ms: float) -> Dict[str, Any]:
        input_tokens = len(prompt.split()) * 1.3  # Estimated token ratio
        output_tokens = len(completion.split()) * 1.3
        
        input_cost = input_tokens * self.rates["input"]
        output_cost = output_tokens * self.rates["output"]
        total_cost = round(input_cost + output_cost, 6)

        return {
            "model": self.model_name,
            "estimated_input_tokens": int(input_tokens),
            "estimated_output_tokens": int(output_tokens),
            "total_tokens": int(input_tokens + output_tokens),
            "total_cost_usd": total_cost,
            "latency_ms": latency_ms
        }

if __name__ == "__main__":
    tracer = TokenCostTracer("gpt-4o")
    prompt_text = "Analyze the vector database performance for RAG pipelines."
    completion_text = "Vector databases optimize semantic search by indexing high-dimensional embeddings."
    
    metrics = tracer.trace_request(prompt_text, completion_text, 142.5)
    print("Execution Metrics:", metrics)
