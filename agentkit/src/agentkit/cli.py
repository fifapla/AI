import argparse
import json
import sys

from .agent import Agent
from .llm import HeuristicLLM, OpenAICompatibleLLM
from .tools import ToolRegistry, calculator_tool, make_file_tools


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="agentkit", description="Run the tool-using agent")
    ap.add_argument("task")
    ap.add_argument("--docs", default="examples/docs", help="folder for read_file / search_docs")
    ap.add_argument("--llm", choices=["heuristic", "openai"], default="heuristic")
    ap.add_argument("--base-url", default="http://127.0.0.1:11434/v1")
    ap.add_argument("--model", default="llama3.1")
    ap.add_argument("--api-key", default="")
    ap.add_argument("--max-steps", type=int, default=8)
    ap.add_argument("--json", action="store_true", help="print the full trace as JSON")
    a = ap.parse_args(argv)
    llm = HeuristicLLM() if a.llm == "heuristic" else OpenAICompatibleLLM(a.base_url, a.model, a.api_key)
    agent = Agent(llm, ToolRegistry([calculator_tool(), *make_file_tools(a.docs)]), max_steps=a.max_steps)
    res = agent.run(a.task)
    if a.json:
        print(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
    else:
        for s in res.steps:
            if s.action:
                print(f"[{s.index}] {s.action}({json.dumps(s.action_input, ensure_ascii=False)}) -> {s.observation[:120]}")
        print(f"\n{res.status}: {res.answer}")
    return 0 if res.status == "finished" else 1


if __name__ == "__main__":
    sys.exit(main())
