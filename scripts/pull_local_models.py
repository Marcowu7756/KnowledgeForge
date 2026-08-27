"""Download local model weights into models/ (offline-first setup).

Usage:
  .\\.venv\\Scripts\\python.exe scripts/pull_local_models.py
  .\\.venv\\Scripts\\python.exe scripts/pull_local_models.py --only whisper,embed
  .\\.venv\\Scripts\\python.exe scripts/pull_local_models.py --status
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.local_models import CATALOG, pull, status_rows  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pull KnowledgeForge local model weights")
    parser.add_argument(
        "--only",
        default="whisper,embed,ollama,tts,vocos,ocr,pix2tex",
        help="Comma-separated: whisper,embed,ollama,tts,vocos,ocr,pix2tex or all",
    )
    parser.add_argument("--force", action="store_true", help="Re-download even if present")
    parser.add_argument("--status", action="store_true", help="Show readiness only")
    args = parser.parse_args(argv)

    if args.status:
        print("Local model status:")
        for name, path, state in status_rows():
            print(f"  {name:12} {state:14} {path}")
        return 0

    kinds = [k.strip() for k in args.only.split(",") if k.strip()]
    for kind in kinds:
        if kind not in CATALOG:
            print(f"Unknown model kind: {kind}", file=sys.stderr)
            return 2
        print(f"[pull] {kind} ...", flush=True)
        try:
            result = pull(kind, force=args.force)  # type: ignore[arg-type]
            print(f"[ok] {kind}: {result}", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"[skip] {kind}: {exc}", file=sys.stderr)

    print("\nAfter all pulls, set in .env:")
    print("  HF_HUB_OFFLINE=1")
    print("  WHISPER_MODEL=D:\\KnowledgeForge\\models\\faster-whisper-medium")
    print("  EMBED_MODEL_PATH=D:\\KnowledgeForge\\models\\bge-small-zh-v1.5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
