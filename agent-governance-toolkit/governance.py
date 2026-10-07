from typing import List, Dict, Any

class AgentGovernancePolicy:
    def __init__(self, allowed_tools: List[str], max_execution_depth: int = 3):
        self.allowed_tools = allowed_tools
        self.max_execution_depth = max_execution_depth

    def authorize_action(self, tool_name: str, current_depth: int) -> Dict[str, Any]:
        if current_depth > self.max_execution_depth:
            return {"authorized": False, "reason": "Max execution depth exceeded."}
        if tool_name not in self.allowed_tools:
            return {"authorized": False, "reason": f"Tool '{tool_name}' is restricted by policy."}
        return {"authorized": True, "reason": "Action permitted."}

if __name__ == "__main__":
    policy = AgentGovernancePolicy(allowed_tools=["search_db", "format_json"], max_execution_depth=2)
    print("Test 1 (Allowed):", policy.authorize_action("search_db", 1))
    print("Test 2 (Blocked Tool):", policy.authorize_action("execute_shell", 1))
