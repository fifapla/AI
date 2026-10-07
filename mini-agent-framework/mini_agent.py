"""
mini_agent.py
-------------
A minimal, dependency-free tool-calling agent built on the ReAct pattern
(Reason -> Act -> Observe, repeated until the goal is satisfied).

Why this exists
================
Most "AI agent" demos just call an LLM API and call it a day, which
hides the actual architecture: a planner that decides which tool to
call, a registry of tools with typed inputs/outputs, an execution loop
with a stop condition, and a transcript you can audit afterwards.

This implementation uses a small deterministic planner instead of a
live LLM call (so it runs anywhere, no API key needed), but the
planner is a drop-in seam: swap `Planner.decide()` for a real LLM call
and the rest of the architecture — tool registry, execution loop,
transcript, stop condition — stays identical. That seam is the part
worth understanding.

Usage
=====
    python mini_agent.py "calculate 12 * 7, then count the words in \
        'the quick brown fox'"
    python mini_agent.py --interactive
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from typing import Callable


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

@dataclass
class Tool:
    name: str
    description: str
    run: Callable[[str], str]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def describe(self) -> str:
        return "\n".join(f"- {t.name}: {t.description}" for t in self._tools.values())


def tool_calculator(expr: str) -> str:
    """Evaluate a simple arithmetic expression safely (digits + operators only)."""
    if not re.fullmatch(r"[\d\s()+\-*/.]+", expr):
        return f"Error: unsafe or invalid expression '{expr}'"
    try:
        return str(eval(expr, {"__builtins__": {}}, {}))  # restricted eval, numeric only
    except Exception as e:  # noqa: BLE001
        return f"Error evaluating '{expr}': {e}"


def tool_word_counter(text: str) -> str:
    text = text.strip("'\" ")
    words = text.split()
    return f"{len(words)} words"


def tool_note_taker(note: str, _log: list[str] = []) -> str:  # noqa: B006 (intentional demo state)
    _log.append(note.strip())
    return f"Saved note #{len(_log)}: {note.strip()}"


DEFAULT_TOOLS = ToolRegistry()
DEFAULT_TOOLS.register(Tool("calculator", "Evaluate a math expression, e.g. '12 * 7'", tool_calculator))
DEFAULT_TOOLS.register(Tool("word_counter", "Count words in a piece of text", tool_word_counter))
DEFAULT_TOOLS.register(Tool("note_taker", "Save a short note for later", tool_note_taker))


# ---------------------------------------------------------------------------
# Planner: decides which tool(s) to call, and in what order
# ---------------------------------------------------------------------------

@dataclass
class PlannedStep:
    tool_name: str
    tool_input: str
    reasoning: str


class Planner:
    """
    A deterministic, rule-based planner. This is intentionally NOT an
    LLM call — it's the clearest way to show the agent's control flow
    without needing an API key to run this file.

    In a production agent, replace `decide()` with a call to an LLM
    that returns the same (tool_name, tool_input, reasoning) shape,
    typically via structured/JSON output or native tool-calling.
    """

    MATH_PATTERN = re.compile(r"calculate\s+([\d\s()+\-*/.]+)", re.IGNORECASE)
    COUNT_PATTERN = re.compile(r"count the words in\s+(.+)", re.IGNORECASE)
    NOTE_PATTERN = re.compile(r"note(?: that)?\s+(.+)", re.IGNORECASE)

    def decide(self, instruction: str) -> list[PlannedStep]:
        steps: list[PlannedStep] = []

        for part in re.split(r",\s*then\s*|;\s*", instruction, flags=re.IGNORECASE):
            part = part.strip()
            if not part:
                continue

            if m := self.MATH_PATTERN.search(part):
                steps.append(PlannedStep(
                    tool_name="calculator",
                    tool_input=m.group(1).strip(),
                    reasoning=f"Instruction asks for a calculation: '{m.group(1).strip()}'",
                ))
            elif m := self.COUNT_PATTERN.search(part):
                steps.append(PlannedStep(
                    tool_name="word_counter",
                    tool_input=m.group(1).strip(),
                    reasoning="Instruction asks to count words in the given text",
                ))
            elif m := self.NOTE_PATTERN.search(part):
                steps.append(PlannedStep(
                    tool_name="note_taker",
                    tool_input=m.group(1).strip(),
                    reasoning="Instruction asks to save a note",
                ))
            else:
                steps.append(PlannedStep(
                    tool_name="unknown",
                    tool_input=part,
                    reasoning=f"No matching tool for: '{part}'",
                ))

        return steps


# ---------------------------------------------------------------------------
# Agent: the Reason -> Act -> Observe execution loop
# ---------------------------------------------------------------------------

@dataclass
class TranscriptEntry:
    thought: str
    action: str
    action_input: str
    observation: str


class Agent:
    def __init__(self, tools: ToolRegistry, planner: Planner | None = None):
        self.tools = tools
        self.planner = planner or Planner()
        self.transcript: list[TranscriptEntry] = []

    def run(self, instruction: str) -> list[TranscriptEntry]:
        self.transcript = []
        plan = self.planner.decide(instruction)

        for step in plan:
            tool = self.tools.get(step.tool_name)
            if tool is None:
                observation = f"No tool available to handle: '{step.tool_input}'"
            else:
                observation = tool.run(step.tool_input)

            self.transcript.append(TranscriptEntry(
                thought=step.reasoning,
                action=step.tool_name,
                action_input=step.tool_input,
                observation=observation,
            ))

        return self.transcript

    def print_transcript(self) -> None:
        for i, entry in enumerate(self.transcript, 1):
            print(f"Step {i}")
            print(f"  Thought:     {entry.thought}")
            print(f"  Action:      {entry.action}({entry.action_input!r})")
            print(f"  Observation: {entry.observation}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

DEMO_INSTRUCTION = (
    "calculate 12 * 7, then count the words in 'the quick brown fox jumps', "
    "then note that the demo ran successfully"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal ReAct-style tool-calling agent.")
    parser.add_argument("instruction", nargs="?", help="Instruction to run the agent on.")
    parser.add_argument("--interactive", action="store_true", help="Enter an interactive loop.")
    args = parser.parse_args()

    agent = Agent(tools=DEFAULT_TOOLS)

    print("Available tools:")
    print(agent.tools.describe())
    print()

    if args.interactive:
        print("Enter an instruction (Ctrl+C to quit):")
        while True:
            try:
                instruction = input("\n> ")
            except (KeyboardInterrupt, EOFError):
                print("\nBye.")
                break
            if not instruction.strip():
                continue
            agent.run(instruction)
            agent.print_transcript()
    else:
        instruction = args.instruction or DEMO_INSTRUCTION
        print(f"Instruction: {instruction}\n")
        agent.run(instruction)
        agent.print_transcript()


if __name__ == "__main__":
    main()
