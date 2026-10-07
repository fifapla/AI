import time
from typing import Dict, Any, Optional

class SharedStateBus:
    def __init__(self):
        self._state_store: Dict[str, Dict[str, Any]] = {}

    def publish_state(self, key: str, value: Any, agent_id: str) -> None:
        self._state_store[key] = {
            "value": value,
            "updated_by": agent_id,
            "timestamp": time.time()
        }

    def read_state(self, key: str) -> Optional[Dict[str, Any]]:
        return self._state_store.get(key, None)

if __name__ == "__main__":
    bus = SharedStateBus()
    bus.publish_state("user_intent", "LOAN_APPLICATION", "IntentClassifierAgent")
    bus.publish_state("risk_score", 0.12, "RiskAssessmentAgent")
    
    print("State Bus Reading [user_intent]:", bus.read_state("user_intent"))
    print("State Bus Reading [risk_score]:", bus.read_state("risk_score"))
