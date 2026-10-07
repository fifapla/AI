import re
from typing import Dict, Any, List

class AIGuardrailsEngine:
    BLOCKED_WORDS = ["toxic", "exploit", "malware", "bribe"]

    def validate_output(self, text: str) -> Dict[str, Any]:
        violations: List[str] = []
        
        # Word filter check
        for word in self.BLOCKED_WORDS:
            if re.search(rf"\b{word}\b", text, re.IGNORECASE):
                violations.append(f"Contains prohibited term: '{word}'")

        # PII Detection (Email pattern)
        if re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text):
            violations.append("PII Detected: Email address present")

        is_passed = len(violations) == 0
        return {
            "passed": is_passed,
            "violations_count": len(violations),
            "violations": violations,
            "status": "APPROVED" if is_passed else "FLAGGED"
        }

if __name__ == "__main__":
    engine = AIGuardrailsEngine()
    sample_response = "Here is the summary. Contact support@company.com for details."
    res = engine.validate_output(sample_response)
    print("Guardrails Check:", res)
