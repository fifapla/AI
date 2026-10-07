import time
from typing import Generator, Dict, Any

class StreamingRAGPipeline:
    def __init__(self, chunk_size: int = 5):
        self.chunk_size = chunk_size

    def retrieve_and_stream(self, query: str, mock_context: str) -> Generator[Dict[str, Any], None, None]:
        tokens = f"Answer based on context [{mock_context[:20]}...]: Analysis indicates optimal vector index usage.".split()
        
        start_time = time.time()
        for i in range(0, len(tokens), self.chunk_size):
            chunk = " ".join(tokens[i:i+self.chunk_size])
            latency = round((time.time() - start_time) * 1000, 2)
            yield {
                "chunk": chunk,
                "latency_ms": latency,
                "is_final": (i + self.chunk_size) >= len(tokens)
            }
            time.sleep(0.02)  # Simulate API network stream

if __name__ == "__main__":
    pipeline = StreamingRAGPipeline()
    print("Streaming RAG Response Tokens:")
    for packet in pipeline.retrieve_and_stream("What is the index strategy?", "HNSW vector configuration context"):
        print(packet)
