# mini_agent.py — Minimal ReAct-style tool-calling agent

A small agent framework demonstrating the core architecture behind
tool-calling AI agents: a tool registry, a planner that decides which
tool to call, and an execution loop that produces an auditable
transcript (Thought -> Action -> Observation, repeated).

## Why

The planner here is deliberately rule-based instead of an LLM call, so
this runs anywhere with zero setup and zero API cost. The planner is a
clean seam: swap `Planner.decide()` for a real LLM call (returning the
same tool_name / tool_input / reasoning shape) and every other part of
the architecture — registry, loop, transcript — works unchanged.

## Run it

```bash
python mini_agent.py                  # runs a built-in multi-step demo
python mini_agent.py --interactive    # type your own instructions
python mini_agent.py "calculate 9 * 9"
```

## What it demonstrates

- A `Tool` abstraction with name/description/callable, registered in a
  `ToolRegistry`
- A planner that splits a compound instruction into discrete steps and
  decides which tool handles each one
- An execution loop that calls tools and records a full transcript
  (thought, action, action input, observation) for every step
- Graceful handling of instructions with no matching tool, instead of
  silently failing

## Extending it

- Add new tools by writing a function and registering it with
  `DEFAULT_TOOLS.register(Tool(...))`
- Swap the rule-based `Planner` for an LLM-backed one for free-form
  natural language instructions
- Add a real stop condition (e.g. "goal achieved" check) for multi-turn
  agent loops instead of a fixed step list
