import time
from typing import List, Dict, Any

class AgentMemoryStore:
    def __init__(self, capacity: int = 5):
        self.capacity = capacity
        self.short_term_memory: List[Dict[str, Any]] = []
        self.long_term_memory: List[Dict[str, Any]] = []

    def add_memory(self, content: str, importance: float = 0.5):
        memory_entry = {
            "content": content,
            "importance": importance,
            "timestamp": time.time()
        }
        
        if importance >= 0.8:
            self.long_term_memory.append(memory_entry)
        else:
            if len(self.short_term_memory) >= self.capacity:
                self.short_term_memory.pop(0)
            self.short_term_memory.append(memory_entry)

    def retrieve_context(self) -> Dict[str, Any]:
        return {
            "short_term_count": len(self.short_term_memory),
            "long_term_count": len(self.long_term_memory),
            "recent_memories": [m["content"] for m in self.short_term_memory],
            "core_memories": [m["content"] for m in self.long_term_memory]
        }

if __name__ == "__main__":
    memory = AgentMemoryStore(capacity=2)
    memory.add_memory("User prefers Python over JavaScript", importance=0.9)
    memory.add_memory("Current session started at 10:00 AM", importance=0.3)
    memory.add_memory("Temporary query context", importance=0.2)
    
    print("Memory Snapshot:", memory.retrieve_context())
