import json
import time
from typing import Dict, Any

class AgentMessage:
    def __init__(self, sender_id: str, receiver_id: str, performative: str, content: Dict[str, Any]):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.performative = performative  # e.g., REQUEST, INFORM, PROPOSE
        self.content = content
        self.timestamp = time.time()

    def serialize(self) -> str:
        return json.dumps({
            "sender": self.sender_id,
            "receiver": self.receiver_id,
            "performative": self.performative,
            "content": self.content,
            "timestamp": self.timestamp
        })

if __name__ == "__main__":
    msg = AgentMessage(
        sender_id="PlannerAgent",
        receiver_id="ExecutorAgent",
        performative="REQUEST",
        content={"task": "execute_query", "query_id": 1042}
    )
    print("Serialized Agent Message Packet:")
    print(msg.serialize())
