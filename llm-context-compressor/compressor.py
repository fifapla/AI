import re
from typing import Dict, Any

class ContextCompressor:
    def __init__(self, target_reduction: float = 0.3):
        self.target_reduction = target_reduction

    def compress(self, text: str) -> Dict[str, Any]:
        original_tokens = len(text.split())
        
        # Remove redundant whitespace and inline comments
        cleaned = re.sub(r"\s+", " ", text).strip()
        # Remove common filler phrases
        fillers = [r"\bas a matter of fact\b", r"\bin order to\b", r"\bit is important to note that\b"]
        for filler in fillers:
            cleaned = re.sub(filler, "", cleaned, flags=re.IGNORECASE)

        compressed_tokens = len(cleaned.split())
        savings = round((1 - (compressed_tokens / max(1, original_tokens))) * 100, 2)

        return {
            "original_word_count": original_tokens,
            "compressed_word_count": compressed_tokens,
            "token_savings_percent": f"{savings}%",
            "compressed_text": cleaned
        }

if __name__ == "__main__":
    raw_prompt = "It is important to note that in order to deploy RAG applications, as a matter of fact we need vector DBs."
    compressor = ContextCompressor()
    res = compressor.compress(raw_prompt)
    print(res)
