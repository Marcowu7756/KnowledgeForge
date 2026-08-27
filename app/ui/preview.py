"""Safe artifact preview helpers (paths must stay under data/)."""

from __future__ import annotations

from pathlib import Path

from app import config
from app.knowledge.parse import load_knowledge_object

_ALLOWED_SUFFIX = {".md", ".txt", ".json", ".gif", ".wav", ".png", ".jpg", ".jpeg", ".webp"}


def allowed_roots() -> list[Path]:
    return [
        config.DATA_DIR.resolve(),
    ]


def _classification_for_path(path: Path) -> str:
    if path.suffix.lower() != ".md":
        return "public"
    try:
        obj = load_knowledge_object(path)
        return obj.access.classification
    except Exception:
        return "public"


def resolve_data_path(raw: str) -> Path:
    """Resolve a user/path string and ensure it stays under data/."""
    if not raw or not str(raw).strip():
        raise ValueError("path required")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        cand = (config.ROOT / path).resolve()
        if cand.is_file() or cand.is_dir():
            path = cand
        else:
            path = path.resolve()
    else:
        path = path.resolve()

    if not path.is_file():
        raise FileNotFoundError(f"not a file: {path}")

    data_root = config.DATA_DIR.resolve()
    try:
        path.relative_to(data_root)
    except ValueError as exc:
        raise PermissionError(f"preview only allowed under {data_root}") from exc

    if path.suffix.lower() not in _ALLOWED_SUFFIX:
        raise ValueError(f"unsupported preview type: {path.suffix}")

    if _classification_for_path(path) == "secret":
        raise PermissionError("preview blocked for secret classification")
    return path


def preview_payload(path: Path) -> dict:
    suffix = path.suffix.lower()
    kind = "text" if suffix in {".md", ".txt", ".json"} else "media"
    payload: dict = {
        "ok": True,
        "path": str(path),
        "name": path.name,
        "suffix": suffix,
        "kind": kind,
        "bytes": path.stat().st_size,
        "file_url": f"/api/preview/file?path={path.as_posix()}",
    }
    if kind == "text":
        text = path.read_text(encoding="utf-8", errors="replace")
        # Cap very large drafts in JSON preview
        if len(text) > 200_000:
            text = text[:200_000] + "\n\n… [truncated]"
        payload["text"] = text
    return payload
