# AI Engineering Portfolio

A collection of Python projects covering AI agents, RAG, MLOps, and LLM
safety/ops tooling — four substantial, fully-tested packages, plus a
set of small, focused utilities. Everything runs offline with
Python's standard library (plus `scikit-learn`/`pandas`/`pyyaml` for
the two projects that need them) — no API keys required to try any of
it.

Every file in this repo has been reviewed and tested: broken code was
fixed, projects with fabricated/hardcoded "metrics" were either
corrected to compute something real or removed, and READMEs that
oversold what the code actually does were corrected. See
`PORTFOLIO_GUIDE.pdf` for a walkthrough of each project and likely
interview questions.

## Flagship projects (substantial, fully tested)

### [`agentkit/`](./agentkit) — Tool-calling agent framework
A real ReAct-loop agent: pluggable LLM backends (offline heuristic,
scripted for tests, or any OpenAI-compatible HTTP endpoint), a safe
AST-based calculator (no `eval()`), sandboxed file tools, loop
detection, and a human-approval gate for sensitive tools. 12/12 tests
passing.
```bash
cd agentkit && python -m pip install -e . && python -m agentkit "what is 12*7?"
```

### [`ragkit/`](./ragkit) — Hybrid RAG with grounding & evaluation
Retrieve → check grounding → answer with citations, over bilingual
(Arabic/English) documents. Refuses to trust an LLM answer that cites
a chunk it wasn't given. Includes a real hit@k/MRR evaluation harness
against a golden question set, and an HTTP API. 9/9 tests passing.
```bash
cd ragkit && python -m pip install -e . && ragkit ask "What's the return policy?"
```

### [`flowpilot/`](./flowpilot) — Event-driven workflow automation
A YAML-configured automation engine: rule-based classification with
an optional LLM fallback, field extraction, idempotent event
processing, retries with a dead-letter queue, and an approval gate for
risky routes. 11/11 tests passing.

### [`mlflowlite/`](./mlflowlite) — Minimal MLOps pipeline
Train → validate → track → register → serve, on a real dataset
(scikit-learn's breast-cancer data). Includes data validation, a
model registry with a promotion gate, and drift detection. 9/9 tests
passing.

## Core demos

| Project | What it shows |
|---|---|
| [`python-rag-demo/`](./python-rag-demo) | RAG from scratch: TF-IDF + cosine similarity, no libraries |
| [`mini-agent-framework/`](./mini-agent-framework) | Minimal ReAct agent loop with a tool registry |
| [`arabic-text-toolkit/`](./arabic-text-toolkit) | Arabic normalization + auditable lexicon sentiment |
| [`automation-report-bot/`](./automation-report-bot) | CSV → Markdown performance report with recommendations |
| [`web-chatbot-demos/`](./web-chatbot-demos) | 4 self-contained HTML/JS chatbot UIs |

## Supporting utilities

Small, focused, single-file tools — each demonstrates one specific
concept. Grouped by area:

**Agents & orchestration:** `agent-communication-protocol`,
`agent-governance-toolkit`, `agent-episodic-memory-index`,
`agent-memory-store`, `agent-shared-state-bus`,
`agentic-workflow-orchestrator`, `multi-agent-consensus-engine`

**RAG & retrieval:** `hybrid-rerank-rag-engine` (lexical scoring only
— see its README), `graph-rag-entity-extractor`,
`dynamic-semantic-chunker` (fixed-size, not true semantic — see its
README), `auto-rag-eval-optimizer`, `rag-evaluation-harness`,
`dynamic-few-shot-selector`, `streaming-rag-pipeline`,
`llm-hallucination-detector`

**LLM ops & safety:** `llm-prompt-guard`, `prompt-injection-firewall`,
`prompt-sanitizer-engine`, `realtime-guardrail-stream`,
`ai-guardrails-engine`, `ai-vulnerability-scanner`,
`ai-code-privacy-masker`, `ai-code-reviewer-bot`, `ai-bias-auditor`,
`ai-explainability-toolkit`, `llm-semantic-cache`,
`llm-cost-and-token-tracer`, `llm-telemetry-dashboard`,
`llm-fine-tuning-monitor`, `llm-model-distiller`,
`llm-context-compressor`, `prompt-version-control`

**Other:** `medical-intent-classifier` (toy demo — see disclaimer in
its README), `edge-llm-quantizer` (size estimator, not real
quantization — see its README), `vector-index-quantizer`,
`vector-index-hnsw-optimizer`, `mcp-windows-system-agent`

Each has its own README. A few READMEs include a **Note** or
**Disclaimer** added during review — read those before describing the
project as more than it is.

## Why this repo exists

Built to demonstrate practical, working AI/automation skills for
freelance and remote AI-related roles, rather than just describing
them in a resume.

## License

MIT — feel free to reuse any part of this for learning purposes.
