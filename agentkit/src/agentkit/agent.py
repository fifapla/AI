"""The agent loop: think -> act -> observe, with budgets, loop detection, approvals and a full trace."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .llm import LLM, LLMError
from .tools import ToolRegistry

SYSTEM_PROMPT = """You are a careful assistant that solves tasks with tools.
Reply with ONE JSON object and nothing else.
To use a tool: {"thought": "...", "action": "<tool name>", "input": {<arguments>}}
To finish:     {"thought": "...", "final": "<answer>"}
Tools:
%s
Never invent tool results. If a tool errors, adapt or explain."""


@dataclass
class Step:
    index: int
    thought: str = ""
    action: str = ""
    action_input: Dict[str, Any] = field(default_factory=dict)
    observation: str = ""
    error: bool = False


@dataclass
class RunResult:
    answer: str
    status: str  # finished | max_steps | loop | denied | invalid_output | llm_error
    steps: List[Step] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"answer": self.answer, "status": self.status, "steps": [asdict(s) for s in self.steps]}


def parse_reply(text: str) -> Optional[Dict[str, Any]]:
    """Extract the first JSON object from a model reply (tolerates prose and ```json fences)."""
    dec = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch == "{":
            try:
                obj, _ = dec.raw_decode(text[i:])
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                return obj
    return None


class Agent:
    def __init__(self, llm: LLM, tools: ToolRegistry, max_steps: int = 8, max_obs_chars: int = 2000,
                 approver: Optional[Callable[[str, Dict[str, Any]], bool]] = None, max_format_errors: int = 2):
        self.llm, self.tools, self.max_steps = llm, tools, max_steps
        self.max_obs_chars, self.approver, self.max_format_errors = max_obs_chars, approver, max_format_errors

    def run(self, task: str) -> RunResult:
        messages = [{"role": "system", "content": SYSTEM_PROMPT % self.tools.describe()}, {"role": "user", "content": task}]
        steps: List[Step] = []
        seen: Dict[str, int] = {}
        format_errors = 0
        while len(steps) < self.max_steps:
            try:
                raw = self.llm.complete(messages)
            except LLMError as e:
                return RunResult(f"LLM error: {e}", "llm_error", steps)
            obj = parse_reply(raw)
            if obj is None or ("final" not in obj and "action" not in obj):
                format_errors += 1
                if format_errors > self.max_format_errors:
                    return RunResult("The model did not return valid JSON.", "invalid_output", steps)
                messages += [{"role": "assistant", "content": raw},
                             {"role": "user", "content": 'OBSERVATION: invalid reply. Return one JSON object with "action" or "final".'}]
                continue
            step = Step(index=len(steps) + 1, thought=str(obj.get("thought", "")))
            if "final" in obj:
                steps.append(step)
                return RunResult(str(obj["final"]), "finished", steps)
            name, args = str(obj["action"]), obj.get("input") or {}
            step.action, step.action_input = name, args if isinstance(args, dict) else {"value": args}
            steps.append(step)
            key = name + json.dumps(step.action_input, sort_keys=True, default=str)
            seen[key] = seen.get(key, 0) + 1
            tool = self.tools.get(name)
            if seen[key] >= 3:
                step.observation, step.error = "Stopped: the same call was repeated.", True
                return RunResult("Stopped because the agent repeated the same action.", "loop", steps)
            if tool is None:
                step.observation, step.error = f"ERROR: unknown tool '{name}'. Available: {', '.join(self.tools.names())}", True
            elif seen[key] == 2:
                step.observation, step.error = "ERROR: repeated call. Use the earlier result or finish.", True
            else:
                if tool.requires_approval and not (self.approver and self.approver(name, step.action_input)):
                    step.observation, step.error = "Denied: human approval was not granted.", True
                    return RunResult(f"Action '{name}' needs approval and was not approved.", "denied", steps)
                try:
                    step.observation = str(tool.func(**step.action_input))
                except Exception as e:  # tool failures are observations, not crashes
                    step.observation, step.error = f"ERROR: {type(e).__name__}: {e}", True
            step.observation = step.observation[: self.max_obs_chars]
            messages += [{"role": "assistant", "content": raw}, {"role": "user", "content": "OBSERVATION: " + step.observation}]
        return RunResult("Reached the step limit without a final answer.", "max_steps", steps)
