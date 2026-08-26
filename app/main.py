from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app import config

USAGE = """KnowledgeForge — Personal Knowledge Compression Engine

  python main.py youtube <URL>
  python main.py pdf <FILE>
  python main.py file <FILE>

Phase 0: environment and pipeline skeleton only.
YouTube / PDF / LLM compression land in Phase 1–2.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="knowledgeforge",
        description="Compress unstructured input into Knowledge Units.",
    )
    sub = parser.add_subparsers(dest="command")

    yt = sub.add_parser("youtube", help="Ingest a YouTube URL (Phase 1)")
    yt.add_argument("url")

    pdf = sub.add_parser("pdf", help="Ingest a local PDF (Phase 2)")
    pdf.add_argument("file")

    file_cmd = sub.add_parser("file", help="Ingest MD / TXT / DOCX (Phase 2)")
    file_cmd.add_argument("file")

    sub.add_parser("status", help="Show Phase 0 environment")
    return parser


def cmd_status() -> int:
    print("KnowledgeForge Phase 0")
    print(f"  root:      {config.ROOT}")
    print(f"  python:    {sys.version.split()[0]}")
    print(f"  provider:  {config.LLM_PROVIDER}")
    print(f"  knowledge: {config.KNOWLEDGE_DIR}")
    print(f"  inbox:     {config.INBOX_DIR}")
    print()
    print("Next: Phase 1 YouTube URL → captions → LLM → Markdown")
    return 0


def cmd_phase_gate(command: str, target: str) -> int:
    phase = "1" if command == "youtube" else "2"
    print(USAGE)
    print(f"[{command}] {target}")
    print(f"Blocked: this command is Phase {phase}. Current milestone is Phase 0.")
    print(f"LLM_PROVIDER={config.LLM_PROVIDER}")
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command or args.command == "status":
        return cmd_status()

    target = args.url if args.command == "youtube" else str(Path(args.file))
    return cmd_phase_gate(args.command, target)


if __name__ == "__main__":
    raise SystemExit(main())
