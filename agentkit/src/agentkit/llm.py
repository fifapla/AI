"""LLM backends. The agent only needs `complete(messages) -> str`, so any provider can be plugged in."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Dict, List, Protocol

Message = Dict[str, str]


class LLMError(RuntimeError):
    pass


class LLM(Protocol):
    def complete(self, messages: List[Message]) -> str: ...


class ScriptedLLM:
    """Returns pre-written replies in order. Deterministic - used by the tests."""

    def __init__(self, replies: List[str]):
        self.replies = list(replies)
        self.calls: List[List[Message]] = []

    def complete(self, messages: List[Message]) -> str:
        self.calls.append([dict(m) for m in messages])
        if not self.replies:
            raise LLMError("ScriptedLLM ran out of replies")
        return self.replies.pop(0)


_EXPR = re.compile(r"[\d\.\s\+\-\*/\(\)\^%]*\d[\d\.\s\+\-\*/\(\)\^%]*")


class HeuristicLLM:
    """A tiny offline 'brain' so the project runs with no API key: math -> calculator, 'search ...' -> search_docs."""

    def complete(self, messages: List[Message]) -> str:
        task = next((m["content"] for m in messages if m["role"] == "user"), "")
        observations = [m["content"] for m in messages if m["role"] == "user" and m["content"].startswith("OBSERVATION:")]
        if observations:
            return json.dumps({"thought": "I have what I need.", "final": observations[-1][len("OBSERVATION:"):].strip()})
        low = task.lower().strip()
        m = re.match(r"^(search|find|ابحث عن|ابحث)\s+(.+)$", low)
        if m:
            return json.dumps({"thought": "Search the local docs.", "action": "search_docs", "input": {"query": m.group(2)}})
        best = max((x.group(0).strip() for x in _EXPR.finditer(task)), key=len, default="")
        if best and re.search(r"[\+\-\*/\^%]", best):
            return json.dumps({"thought": "This is arithmetic.", "action": "calculator", "input": {"expression": best.replace("^", "**")}})
        return json.dumps({"thought": "No tool applies offline.", "final": "I can only do arithmetic and 'search <topic>' without an LLM backend."})


class OpenAICompatibleLLM:
    """Any OpenAI-compatible /chat/completions endpoint (OpenAI, Ollama, vLLM, LM Studio, ...). Stdlib only."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434/v1", model: str = "llama3.1", api_key: str = "", timeout: float = 60.0):
        self.base_url, self.model, self.api_key, self.timeout = base_url.rstrip("/"), model, api_key, timeout

    def complete(self, messages: List[Message]) -> str:
        body = json.dumps({"model": self.model, "messages": messages, "temperature": 0}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        req = urllib.request.Request(self.base_url + "/chat/completions", data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError, TimeoutError) as e:
            raise LLMError(f"LLM request failed: {e}") from e
