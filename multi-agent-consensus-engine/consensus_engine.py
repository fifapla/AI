from typing import List, Dict, Any
from collections import Counter

class AgentConsensusEngine:
    def __init__(self, agents_count: int = 3):
        self.agents_count = agents_count

    def reach_consensus(self, agent_responses: List[str]) -> Dict[str, Any]:
        if not agent_responses:
            return {"status": "ERROR", "message": "No responses provided"}
        
        counts = Counter(agent_responses)
        most_common, votes = counts.most_common(1)[0]
        confidence = round(votes / len(agent_responses), 2)

        return {
            "consensus_reached": confidence >= 0.5,
            "final_decision": most_common,
            "confidence_score": confidence,
            "vote_distribution": dict(counts)
        }

if __name__ == "__main__":
    engine = AgentConsensusEngine()
    responses = [
        "APPROVE_LOAN",
        "APPROVE_LOAN",
        "REJECT_LOAN",
        "APPROVE_LOAN"
    ]
    result = engine.reach_consensus(responses)
    print("Consensus Result:", result)
