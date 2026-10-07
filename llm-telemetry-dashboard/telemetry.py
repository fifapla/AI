from typing import List, Dict, Any
import time

class LLMTelemetryMonitor:
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []

    def record_request(self, endpoint: str, tokens: int, latency: float, status_code: int):
        self.logs.append({
            "timestamp": time.time(),
            "endpoint": endpoint,
            "tokens": tokens,
            "latency_ms": latency,
            "status": status_code
        })

    def get_summary_metrics(self) -> Dict[str, Any]:
        if not self.logs:
            return {"status": "No data"}
        total_tokens = sum(l["tokens"] for l in self.logs)
        avg_latency = sum(l["latency_ms"] for l in self.logs) / len(self.logs)
        return {
            "total_requests": len(self.logs),
            "total_tokens_consumed": total_tokens,
            "average_latency_ms": round(avg_latency, 2)
        }

if __name__ == "__main__":
    monitor = LLMTelemetryMonitor()
    monitor.record_request("/v1/chat/completions", 150, 240.5, 200)
    monitor.record_request("/v1/chat/completions", 320, 410.2, 200)
    print("Telemetry Summary:", monitor.get_summary_metrics())
