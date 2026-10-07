"""Tool registry + safe built-in tools (calculator, sandboxed file reader, local doc search)."""
from __future__ import annotations

import ast
import operator
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List

_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow}
_UN = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def safe_eval(expression: str) -> float:
    """Evaluate arithmetic only. No names, calls, attributes or huge powers - never uses eval()."""
    if len(expression) > 200:
        raise ValueError("expression too long")
    tree = ast.parse(expression.strip(), mode="eval")

    def ev(n: ast.AST):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and type(n.value) in (int, float):
            return n.value
        if isinstance(n, ast.UnaryOp) and type(n.op) in _UN:
            return _UN[type(n.op)](ev(n.operand))
        if isinstance(n, ast.BinOp) and type(n.op) in _BIN:
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Pow) and (abs(b) > 100 or abs(a) > 1e6):
                raise ValueError("power too large")
            return _BIN[type(n.op)](a, b)
        raise ValueError("unsupported expression")

    return ev(tree)


@dataclass
class Tool:
    name: str
    description: str
    func: Callable[..., Any]
    parameters: Dict[str, str] = field(default_factory=dict)
    requires_approval: bool = False

    def describe(self) -> str:
        args = ", ".join(f"{k}: {v}" for k, v in self.parameters.items())
        flag = " [needs approval]" if self.requires_approval else ""
        return f"- {self.name}({args}): {self.description}{flag}"


class ToolRegistry:
    def __init__(self, tools: List[Tool] | None = None):
        self._tools: Dict[str, Tool] = {}
        for t in tools or []:
            self.register(t)

    def register(self, tool: Tool) -> Tool:
        if tool.name in self._tools:
            raise ValueError(f"duplicate tool: {tool.name}")
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> List[str]:
        return sorted(self._tools)

    def describe(self) -> str:
        return "\n".join(self._tools[n].describe() for n in self.names())


def calculator_tool() -> Tool:
    def run(expression: str) -> str:
        v = safe_eval(str(expression))
        return str(int(v)) if isinstance(v, float) and v.is_integer() else str(round(v, 10))
    return Tool("calculator", "Evaluate an arithmetic expression.", run, {"expression": "string"})


def _inside(root: Path, p: Path) -> bool:
    try:
        p.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def make_file_tools(root: str | Path) -> List[Tool]:
    """read_file and search_docs, both confined to `root` (path traversal and symlink escapes are blocked)."""
    base = Path(root)

    def read_file(path: str) -> str:
        p = (base / path)
        if not _inside(base, p) or not p.is_file():
            raise PermissionError("path is outside the allowed folder or not a file")
        return p.read_text(encoding="utf-8", errors="replace")[:4000]

    def search_docs(query: str) -> str:
        terms = {t for t in re.findall(r"\w+", query.lower()) if len(t) > 2}
        hits = []
        for p in sorted(base.rglob("*")):
            if p.suffix.lower() not in (".md", ".txt") or not p.is_file() or not _inside(base, p):
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            words = re.findall(r"\w+", text.lower())
            score = sum(words.count(t) for t in terms)
            if score:
                hits.append((score, p.relative_to(base).as_posix(), " ".join(text.split())[:240]))
        hits.sort(key=lambda h: (-h[0], h[1]))
        return "\n".join(f"{name}: {snip}" for _, name, snip in hits[:3]) or "no matches"

    return [Tool("read_file", "Read a text file from the docs folder.", read_file, {"path": "relative path"}),
            Tool("search_docs", "Keyword search over the docs folder.", search_docs, {"query": "string"})]
