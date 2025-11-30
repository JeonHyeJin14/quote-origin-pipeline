"""
Example CLI runner for the qdd2 pipeline.

Usage:
  python main.py --text '트럼프 "베네수엘라 상공 전면폐쇄"' --date 2024-11-29
  python main.py --file sample.txt --quote "북한과의 대화를 재개해야 한다"

Flags:
  --text / --file : input text (one must be provided)
  --quote         : specific quote sentence (optional; if omitted, pass None)
  --date          : article date YYYY-MM-DD (optional)
  --top-n         : number of keywords to extract (default 15)
  --top-k         : keywords used in the final query (default 3)
  --rollcall      : rollcall.com-friendly query mode (boolean flag)
  --debug         : verbose prints from NER/keyword extraction (boolean flag)

Only query generation is performed here; Google CSE search requires API keys and is not invoked by default.
"""

import argparse
import sys

from qdd2.pipeline import build_queries_from_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="QDD2 extraction/query test runner")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", type=str, help="Inline text to process")
    src.add_argument("--file", type=str, help="Path to a UTF-8 text file to process")

    parser.add_argument("--quote", type=str, default=None, help="Specific quote sentence (optional)")
    parser.add_argument("--date", type=str, default=None, help="Article date YYYY-MM-DD")
    parser.add_argument("--top-n", type=int, default=15, help="Number of keywords to extract (default: 15)")
    parser.add_argument("--top-k", type=int, default=3, help="Keywords to include in query (default: 3)")
    parser.add_argument("--rollcall", action="store_true", help="Use rollcall.com-oriented query construction")
    parser.add_argument("--debug", action="store_true", help="Verbose debug logs")
    return parser.parse_args()


def load_text(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Failed to read file {args.file}: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    args = parse_args()
    text = load_text(args)

    result = build_queries_from_text(
        text=text,
        top_n_keywords=args.top_n,
        top_k_for_query=args.top_k,
        quote_sentence=args.quote,
        article_date=args.date,
        rollcall_mode=args.rollcall,
        device=0,  # CPU by default
        debug=args.debug,
    )

    print("\n=== Entities by type ===")
    for label, words in result["entities_by_type"].items():
        print(f"{label}: {words}")

    print("\n=== Top keywords ===")
    for kw, score in result["keywords"]:
        print(f"{kw}  ({score:.4f})")

    print("\n=== Queries ===")
    print(f"KO: {result['queries']['ko']}")
    print(f"EN: {result['queries']['en']}")


if __name__ == "__main__":
    main()
