# agentkit — a tool-using AI agent in ~400 lines

![CI](https://github.com/<your-user>/agentkit/actions/workflows/ci.yml/badge.svg)
![python](https://img.shields.io/badge/python-3.10%2B-blue) ![license](https://img.shields.io/badge/license-MIT-green)

A small, readable ReAct-style agent framework: the model decides which tool to call, the loop executes it safely, and everything is traced. No dependencies, works offline with a built-in heuristic backend, and plugs into any OpenAI-compatible endpoint (OpenAI, Ollama, vLLM, LM Studio).

> 🇪🇬 وكيل ذكاء اصطناعي (ReAct) يستخدم أدوات، بدون أي مكتبات خارجية، مع حماية من الحلقات والتنفيذ الخطر.

## Features
- Think → act → observe loop with a step budget and a full JSON trace
- Loop detection (same call repeated), invalid-JSON recovery, tool errors become observations instead of crashes
- Human-approval gate for tools flagged `requires_approval`
- Safe built-ins: AST-based calculator (never `eval`), file reader and doc search sandboxed against path traversal
- Pluggable LLM: `ScriptedLLM` (deterministic tests), `HeuristicLLM` (offline demo), `OpenAICompatibleLLM`

## How it works
```
task ──► Agent.run ──► LLM.complete ──► parse JSON ──┬─► final  → RunResult
                  ▲                                  └─► action → Tool (approval? sandbox?) → observation ─┐
                  └──────────────────────────────────────────────────────────────────────────────────────┘
```

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
PYTHONPATH=src python -m agentkit "what is (12+8)*3"
PYTHONPATH=src python -m agentkit "search shipping" --docs examples/docs
# with a local model:
PYTHONPATH=src python -m agentkit "summarise the returns policy" --llm openai --model llama3.1
```

## Tests
```bash
python -m unittest discover -s tests -v     # or: pytest
```

## Honest limitations
- The offline `HeuristicLLM` only handles arithmetic and `search <topic>`; real reasoning needs a real model.
- No parallel tool calls or streaming yet.
- Prompt format is plain JSON, not provider-native function calling.

## Roadmap
- [ ] Native function-calling adapters
- [ ] Parallel tool execution
- [ ] Persistent memory / summarisation of long traces

## License
MIT
