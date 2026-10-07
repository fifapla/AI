from typing import Dict, Any

class HNSWOptimizer:
    def __init__(self, default_m: int = 16, default_ef_construction: int = 200):
        self.m = default_m
        self.ef_construction = default_ef_construction

    def optimize_params(self, dataset_size: int, target_recall: float) -> Dict[str, Any]:
        recommended_m = self.m
        recommended_ef = self.ef_construction
        
        if dataset_size > 1000000:
            recommended_m = 32
            recommended_ef = 400
            
        estimated_search_latency_ms = round(0.5 + (recommended_m * 0.02), 2)
        
        return {
            "dataset_size": dataset_size,
            "target_recall": f"{target_recall * 100}%",
            "recommended_M": recommended_m,
            "recommended_efConstruction": recommended_ef,
            "estimated_search_latency_ms": estimated_search_latency_ms
        }

if __name__ == "__main__":
    optimizer = HNSWOptimizer()
    config = optimizer.optimize_params(dataset_size=2500000, target_recall=0.98)
    print("HNSW Index Configuration:", config)
