import re
from typing import Dict, Any

class StreamGuardrail:
    PROHIBITED_TERMS = ["bypass_token", "unrestricted_access", "internal_key"]

    def audit_token_chunk(self, chunk: str) -> Dict[str, Any]:
        is_violating = any(term in chunk.lower() for term in self.PROHIBITED_TERMS)
        return {
            "chunk": chunk,
            "is_safe": not is_violating,
            "action": "HALT_STREAM" if is_violating else "EMIT"
        }

if __name__ == "__main__":
    guard = StreamGuardrail()
    token_stream = ["Response:", " Access", " granted", " via", " internal_key", " endpoint."]
    
    for token in token_stream:
        audit = guard.audit_token_chunk(token)
        print("Audit Token:", audit)
        if not audit["is_safe"]:
            print("!!! STREAM INTERCEPTED !!!")
            break
