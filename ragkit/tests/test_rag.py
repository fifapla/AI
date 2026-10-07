import json
import pathlib
import sys
import tempfile
import threading
import unittest
import urllib.request
from http.server import HTTPServer

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from ragkit import HybridIndex, RAG, normalize, tokenize  # noqa: E402
from ragkit.evaluate import evaluate  # noqa: E402
from ragkit.rag import NO_ANSWER  # noqa: E402
from ragkit.server import make_handler  # noqa: E402
from ragkit.text import chunk_text  # noqa: E402

RAG_ = RAG.from_directory(ROOT / "data" / "docs")


class Text(unittest.TestCase):
    def test_arabic_normalisation(self):
        self.assertEqual(normalize("الإِرْجَاعُ"), normalize("الارجاعُ"))
        self.assertEqual(tokenize("المنتجات الرقمية"), tokenize("منتجات رقميه"))

    def test_chunking_keeps_sentences_and_overlaps(self):
        text = " ".join(f"Sentence number {i} is here." for i in range(30))
        cs = chunk_text("d", text, max_chars=120, overlap_sentences=1)
        self.assertGreater(len(cs), 3)
        self.assertTrue(all(c.text.endswith(".") for c in cs))
        self.assertTrue(cs[1].text.split(". ")[0] in cs[0].text)


class Retrieval(unittest.TestCase):
    def test_top_hit_is_correct_in_both_languages(self):
        self.assertEqual(RAG_.retrieve("how long does express shipping take")[0][0].source, "shipping_en.md")
        self.assertEqual(RAG_.retrieve("الشحن السريع كم يوم")[0][0].source, "shipping_ar.md")

    def test_eval_quality_floor(self):
        r = evaluate(RAG_, ROOT / "data" / "golden.jsonl", k=3, mode="hybrid")
        self.assertGreaterEqual(r["hit@3"], 0.9)
        self.assertGreaterEqual(r["mrr"], 0.8)

    def test_persistence_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            RAG_.index.save(d)
            idx = HybridIndex.load(d)
        a = [c.source for c, _ in RAG_.retrieve("refund time")]
        b = [c.source for c, _ in RAG(idx).retrieve("refund time")]
        self.assertEqual(a, b)


class Answers(unittest.TestCase):
    def test_grounded_answer_has_citation(self):
        a = RAG_.ask("Are digital products refundable?")
        self.assertTrue(a.grounded)
        self.assertIn("returns_en.md", a.citations[0])
        self.assertIn("not refundable", a.text)

    def test_refuses_out_of_domain(self):
        for q in ["What is the capital of Mars?", "ما هي عاصمة المريخ؟", "Explain quantum chromodynamics"]:
            a = RAG_.ask(q)
            self.assertFalse(a.grounded, q)
            self.assertEqual(a.text, NO_ANSWER)

    def test_llm_answer_with_fake_citation_is_rejected(self):
        bad = RAG(RAG_.index, llm=lambda p: "You have 90 days [7].")
        a = bad.ask("How many days do I have to return an item?")
        self.assertNotIn("90", a.text)
        good = RAG(RAG_.index, llm=lambda p: "Within 30 days of delivery [1].")
        self.assertIn("30 days", good.ask("How many days do I have to return an item?").text)


class Api(unittest.TestCase):
    def test_http_api(self):
        srv = HTTPServer(("127.0.0.1", 0), make_handler(RAG_))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_port}"
        try:
            req = urllib.request.Request(base + "/ask", data=json.dumps({"question": "When is express shipping free?"}).encode(), method="POST")
            out = json.loads(urllib.request.urlopen(req, timeout=5).read())
            self.assertTrue(out["grounded"])
            with self.assertRaises(urllib.error.HTTPError) as cm:
                urllib.request.urlopen(urllib.request.Request(base + "/ask", data=b"{}", method="POST"), timeout=5)
            self.assertEqual(cm.exception.code, 400)
        finally:
            srv.shutdown()


if __name__ == "__main__":
    unittest.main()
