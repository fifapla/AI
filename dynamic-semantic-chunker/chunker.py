from typing import List, Dict, Any

class SemanticChunker:
    def __init__(self, max_sentence_per_chunk: int = 3):
        self.max_sentences = max_sentence_per_chunk

    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        chunks = []
        
        for i in range(0, len(sentences), self.max_sentences):
            chunk_content = ". ".join(sentences[i:i+self.max_sentences]) + "."
            chunks.append({
                "chunk_id": len(chunks) + 1,
                "sentences_count": len(sentences[i:i+self.max_sentences]),
                "content": chunk_content
            })
            
        return chunks

if __name__ == "__main__":
    chunker = SemanticChunker(max_sentence_per_chunk=2)
    sample_text = "Vector databases manage embeddings. They provide fast ANN searches. HNSW is a popular indexing algorithm. Quantization reduces memory overhead."
    result = chunker.chunk_text(sample_text)
    print("Generated Semantic Chunks:", result)
