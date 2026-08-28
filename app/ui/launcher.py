"""Freeze-friendly entrypoint for optional desktop / portable Web UI."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def bootstrap_root() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
    else:
        base = Path(__file__).resolve().parents[2]
    os.environ.setdefault("KF_ROOT", str(base))
    return Path(os.environ["KF_ROOT"]).resolve()


def main(argv: list[str] | None = None) -> int:
    root = bootstrap_root()
    parser = argparse.ArgumentParser(
        description="KnowledgeForge Web UI launcher (browser-first; optional --desktop)"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--desktop",
        action="store_true",
        help="Optional pywebview desktop window (default: system browser)",
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        help=argparse.SUPPRESS,  # legacy no-op; browser is now default
    )
    args = parser.parse_args(argv)

    # Ensure project imports resolve when frozen / portable
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    print(f"[ui] KF_ROOT={root}", flush=True)

    from app.ui.server import serve

    serve(host=args.host, port=args.port, desktop=bool(args.desktop))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
