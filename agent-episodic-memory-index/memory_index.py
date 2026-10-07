import time
from typing import List, Dict, Any

class EpisodicMemoryIndex:
    def __init__(self):
        self.episodes: List[Dict[str, Any]] = []

    def record_episode(self, agent_id: str, action: str, outcome: str):
        episode = {
            "episode_id": len(self.episodes) + 1,
            "agent_id": agent_id,
            "action": action,
            "outcome": outcome,
            "timestamp": time.time()
        }
        self.episodes.append(episode)

    def query_recent_episodes(self, limit: int = 2) -> List[Dict[str, Any]]:
        return self.episodes[-limit:]

if __name__ == "__main__":
    memory = EpisodicMemoryIndex()
    memory.record_episode("SearchAgent", "Query Vector DB", "Returned 5 matches")
    memory.record_episode("SummarizerAgent", "Compress Context", "Context reduced by 30%")
    
    print("Recent Episodic Memories:", memory.query_recent_episodes(limit=2))
