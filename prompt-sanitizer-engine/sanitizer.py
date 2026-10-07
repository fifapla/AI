import re
from typing import Dict, Any

class PromptSanitizer:
    def __init__(self):
        self.email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
        self.phone_pattern = r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"

    def sanitize(self, text: str) -> Dict[str, Any]:
        sanitized_text = re.sub(self.email_pattern, "[REDACTED_EMAIL]", text)
        sanitized_text = re.sub(self.phone_pattern, "[REDACTED_PHONE]", sanitized_text)
        
        has_pii = sanitized_text != text
        return {
            "contains_pii": has_pii,
            "sanitized_prompt": sanitized_text
        }

if __name__ == "__main__":
    sanitizer = PromptSanitizer()
    raw = "My email is john.doe@example.com and phone is 123-456-7890."
    res = sanitizer.sanitize(raw)
    print("Sanitized Output:", res)
