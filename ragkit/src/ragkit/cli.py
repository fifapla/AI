import argparse
import json
import sys

from .evaluate import evaluate
from .rag import RAG


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ragkit")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ask"); a.add_argument("question"); a.add_argument("--docs", default="data/docs")
    e = sub.add_parser("eval"); e.add_argument("--docs", default="data/docs"); e.add_argument("--golden", default="data/golden.jsonl")
    e.add_argument("--k", type=int, default=3)
    s = sub.add_parser("serve"); s.add_argument("--docs", default="data/docs"); s.add_argument("--port", type=int, default=8080)
    args = ap.parse_args(argv)
    rag = RAG.from_directory(args.docs)
    if args.cmd == "ask":
        r = rag.ask(args.question)
        print(r.text); print("sources:", ", ".join(r.citations) or "-")
    elif args.cmd == "eval":
        for mode in ("bm25", "vector", "hybrid"):
            print(json.dumps(evaluate(rag, args.golden, args.k, mode), ensure_ascii=False))
    else:
        from .server import serve
        serve(rag, args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
