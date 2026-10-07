import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from agentkit import Agent, HeuristicLLM, ScriptedLLM, Tool, ToolRegistry, make_file_tools, safe_eval  # noqa: E402
from agentkit.agent import parse_reply  # noqa: E402
from agentkit.tools import calculator_tool  # noqa: E402


def J(**kw):
    return json.dumps(kw)


class SafeEval(unittest.TestCase):
    def test_arithmetic(self):
        self.assertEqual(safe_eval("2 + 3 * 4"), 14)
        self.assertEqual(safe_eval("(2+3)*4 - -1"), 21)

    def test_rejects_code(self):
        for bad in ["__import__('os').system('echo hi')", "open('x')", "a+1", "[1,2]", "2**10000", "9**9**9"]:
            with self.assertRaises(Exception, msg=bad):
                safe_eval(bad)


class Parsing(unittest.TestCase):
    def test_fenced_and_prose(self):
        self.assertEqual(parse_reply('Sure!\n```json\n{"final": "x"}\n```')["final"], "x")
        self.assertIsNone(parse_reply("no json here"))


class Files(unittest.TestCase):
    def test_sandbox(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d) / "docs"
            root.mkdir()
            (root / "a.md").write_text("hello world policy", encoding="utf-8")
            (pathlib.Path(d) / "secret.txt").write_text("nope", encoding="utf-8")
            read, search = make_file_tools(root)
            self.assertIn("hello", read.func("a.md"))
            with self.assertRaises(PermissionError):
                read.func("../secret.txt")
            self.assertIn("a.md", search.func("policy"))


class Loop(unittest.TestCase):
    def reg(self):
        return ToolRegistry([calculator_tool()])

    def test_tool_then_final(self):
        llm = ScriptedLLM([J(thought="t", action="calculator", input={"expression": "6*7"}), J(thought="d", final="42")])
        r = Agent(llm, self.reg()).run("6*7?")
        self.assertEqual((r.status, r.answer, r.steps[0].observation), ("finished", "42", "42"))

    def test_unknown_tool_is_recoverable(self):
        llm = ScriptedLLM([J(action="nope", input={}), J(final="ok")])
        r = Agent(llm, self.reg()).run("x")
        self.assertTrue(r.steps[0].error)
        self.assertEqual(r.status, "finished")

    def test_tool_exception_is_observation(self):
        llm = ScriptedLLM([J(action="calculator", input={"expression": "__import__('os')"}), J(final="gave up")])
        r = Agent(llm, self.reg()).run("x")
        self.assertTrue(r.steps[0].observation.startswith("ERROR"))

    def test_max_steps_and_loop(self):
        same = J(action="calculator", input={"expression": "1+1"})
        r = Agent(ScriptedLLM([same] * 5), self.reg(), max_steps=10).run("x")
        self.assertEqual(r.status, "loop")
        step = J(action="calculator", input={"expression": "1+1"})
        r2 = Agent(ScriptedLLM([J(action="calculator", input={"expression": str(i) + "+1"}) for i in range(5)]), self.reg(), max_steps=3).run("x")
        self.assertEqual(r2.status, "max_steps")
        self.assertTrue(step)

    def test_invalid_output_gives_up(self):
        r = Agent(ScriptedLLM(["blah"] * 5), self.reg()).run("x")
        self.assertEqual(r.status, "invalid_output")

    def test_approval_gate(self):
        danger = Tool("wipe", "dangerous", lambda: "done", requires_approval=True)
        reg = ToolRegistry([danger])
        r = Agent(ScriptedLLM([J(action="wipe", input={})]), reg).run("x")
        self.assertEqual(r.status, "denied")
        r2 = Agent(ScriptedLLM([J(action="wipe", input={}), J(final="ok")]), reg, approver=lambda n, a: True).run("x")
        self.assertEqual((r2.status, r2.steps[0].observation), ("finished", "done"))


class Offline(unittest.TestCase):
    def test_heuristic_end_to_end(self):
        r = Agent(HeuristicLLM(), ToolRegistry([calculator_tool()])).run("what is (12+8)*3 ?")
        self.assertEqual((r.status, r.answer), ("finished", "60"))

    def test_search_end_to_end(self):
        root = pathlib.Path(__file__).resolve().parents[1] / "examples" / "docs"
        r = Agent(HeuristicLLM(), ToolRegistry(make_file_tools(root))).run("search refunds")
        self.assertEqual(r.status, "finished")
        self.assertIn("returns.md", r.answer)


if __name__ == "__main__":
    unittest.main()
