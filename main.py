import argparse
import os
import sys
from pathlib import Path

from config import AppConfig
from repeater import start


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    description="AI Pair Engineer — periodic codebase review powered by Gemini."
  )
  parser.add_argument(
    "codebase_path",
    nargs="?",
    default=r"C:\Users\SG\Desktop\locust",
    help="Path to the codebase directory to analyze",
  )
  parser.add_argument(
    "--interval",
    type=int,
    default=40,
    help="Seconds between analysis runs (default: 40)",
  )
  parser.add_argument(
    "--notify",
    action=argparse.BooleanOptionalAction,
    default=sys.platform == "win32",
    help="Show a Windows desktop notification after each cycle (default: on for Windows)",
  )
  parser.add_argument(
    "--once",
    action="store_true",
    help="Run a single analysis cycle and exit",
  )
  parser.add_argument(
    "--model",
    default=None,
    help="Gemini model used for analysis (default: GEMINI_MODEL env or gemini-3.1-flash-lite)",
  )
  parser.add_argument(
    "--embedding-model",
    default="gemini-embedding-001",
    help="Gemini embedding model used for retrieval",
  )
  parser.add_argument(
    "--top-k",
    type=int,
    default=12,
    help="Number of retrieved chunks to send to the LLM",
  )
  return parser.parse_args()


def main() -> None:
  args = parse_args()
  config = AppConfig(
    codebase_path=Path(args.codebase_path).resolve(),
    repeat_interval_seconds=args.interval,
    run_once=args.once,
    desktop_notify=args.notify,
    llm_model=args.model or os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
    embedding_model=args.embedding_model,
    retrieval_top_k=args.top_k,
  )
  start(config)


if __name__ == "__main__":
  main()
