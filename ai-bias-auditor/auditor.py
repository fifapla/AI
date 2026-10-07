import re
from typing import Dict, Any, List

class AIBiasAuditor:
    BIAS_INDICATORS = ["always", "never", "obviously", "naturally suited"]

    def audit_text(self, text: str) -> Dict[str, Any]:
        found_terms: List[str] = []
        for term in self.BIAS_INDICATORS:
            if re.search(rf"\b{term}\b", text, re.IGNORECASE):
                found_terms.append(term)

        is_flagged = len(found_terms) > 0
        return {
            "contains_bias_risk": is_flagged,
            "detected_triggers": found_terms,
            "fairness_score": round(1.0 - (len(found_terms) * 0.25), 2),
            "status": "REQUIRES_REVIEW" if is_flagged else "CLEARED"
        }

if __name__ == "__main__":
    auditor = AIBiasAuditor()
    sample = "Candidates from this background are naturally suited for management roles."
    audit_report = auditor.audit_text(sample)
    print("Bias Audit Report:", audit_report)
