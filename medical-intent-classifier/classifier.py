import re
from typing import Dict, Any

class MedicalIntentClassifier:
    URGENT_KEYWORDS = ["chest pain", "shortness of breath", "severe bleeding", "unconscious"]

    def classify_triage(self, query: str) -> Dict[str, Any]:
        query_lower = query.lower()
        is_urgent = any(re.search(rf"\b{kw}\b", query_lower) for kw in self.URGENT_KEYWORDS)
        
        triage_level = "EMERGENCY" if is_urgent else "ROUTINE_CONSULT"
        return {
            "query": query,
            "triage_level": triage_level,
            "requires_immediate_care": is_urgent,
            "recommendation": "Direct to ER immediately" if is_urgent else "Schedule general consultation"
        }

if __name__ == "__main__":
    classifier = MedicalIntentClassifier()
    print("Patient 1:", classifier.classify_triage("I have severe shortness of breath since morning."))
    print("Patient 2:", classifier.classify_triage("I need a routine refill for my vitamin D."))
