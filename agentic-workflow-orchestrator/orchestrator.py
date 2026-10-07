from typing import List, Dict, Any, Callable
import json

class Agent:
    def __init__(self, name: str, role: str, task_fn: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self.name = name
        self.role = role
        self.task_fn = task_fn

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        print(f"[{self.name} - {self.role}] Executing task...")
        result = self.task_fn(context)
        context.update(result)
        return context

class WorkflowOrchestrator:
    def __init__(self):
        self.pipeline: List[Agent] = []

    def add_agent(self, agent: Agent) -> "WorkflowOrchestrator":
        self.pipeline.append(agent)
        return self

    def run(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        context = initial_context.copy()
        for agent in self.pipeline:
            context = agent.execute(context)
        return context

if __name__ == "__main__":
    def researcher(ctx): return {"findings": "RAG improves LLM factual accuracy by 40%."}
    def writer(ctx): return {"draft": f"Report based on: {ctx.get('findings')}"}
    def reviewer(ctx): return {"status": "APPROVED", "final_output": ctx.get("draft").upper()}

    swarm = WorkflowOrchestrator()
    swarm.add_agent(Agent("Agent-1", "Researcher", researcher))
    swarm.add_agent(Agent("Agent-2", "Writer", writer))
    swarm.add_agent(Agent("Agent-3", "Reviewer", reviewer))

    result = swarm.run({"topic": "AI RAG Architectures"})
    print("\n--- Workflow Execution Result ---")
    print(json.dumps(result, indent=2))
