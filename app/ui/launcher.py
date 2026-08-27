"""Freeze-friendly entrypoint for Windows UI (.exe / portable)."""

from __future__ import annotations

import argparse
import os
import sys
import threading
import time
import webbrowser
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
    parser = argparse.ArgumentParser(description="KnowledgeForge Windows UI launcher")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Open system browser instead of pywebview desktop window",
    )
    args = parser.parse_args(argv)

    # Ensure project imports resolve when frozen / portable
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    print(f"[ui] KF_ROOT={root}", flush=True)

    if not args.browser:
        from app.ui.server import serve

        serve(host=args.host, port=args.port, desktop=True)
        return 0

    import uvicorn

    from app.ui.server import create_app

    url = f"http://{args.host}:{args.port}"

    def _open() -> None:
        time.sleep(0.8)
        webbrowser.open(url)

    threading.Thread(target=_open, daemon=True).start()
    print(f"[ui] KnowledgeForge workshop → {url}", flush=True)
    uvicorn.run(create_app(), host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
