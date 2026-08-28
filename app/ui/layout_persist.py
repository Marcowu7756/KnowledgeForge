"""H1c · persist multi-card UI layout (family id + selection + compose fields).

Does not invent KOs or edit ontology — only remembers workshop view state.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app import config

SCHEMA = "kf.ui.multi_card_layout.v0"
LAYOUT_NAME = "multi_card_layout.json"


def layout_path() -> Path:
    return config.UI_DIR / LAYOUT_NAME


def empty_layout() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "h1": "H1c",
        "artifact_id": "",
        "selected_paths": [],
        "compose_query": "",
        "compose_kind": "lecture",
        "updated": None,
    }


def load_layout() -> dict[str, Any]:
    path = layout_path()
    if not path.is_file():
        return empty_layout()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty_layout()
    if not isinstance(raw, dict):
        return empty_layout()
    out = empty_layout()
    out["artifact_id"] = str(raw.get("artifact_id") or "").strip()
    paths = raw.get("selected_paths") or []
    if isinstance(paths, list):
        out["selected_paths"] = [str(p).strip() for p in paths if str(p).strip()]
    out["compose_query"] = str(raw.get("compose_query") or "")
    kind = str(raw.get("compose_kind") or "lecture").strip().lower()
    out["compose_kind"] = kind if kind in ("lecture", "paper") else "lecture"
    out["updated"] = raw.get("updated")
    return out


def save_layout(
    *,
    artifact_id: str,
    selected_paths: list[str] | None = None,
    compose_query: str = "",
    compose_kind: str = "lecture",
) -> dict[str, Any]:
    config.UI_DIR.mkdir(parents=True, exist_ok=True)
    kind = (compose_kind or "lecture").strip().lower()
    if kind not in ("lecture", "paper"):
        kind = "lecture"
    payload = {
        "schema": SCHEMA,
        "h1": "H1c",
        "artifact_id": (artifact_id or "").strip(),
        "selected_paths": [
            str(p).strip() for p in (selected_paths or []) if str(p).strip()
        ],
        "compose_query": compose_query or "",
        "compose_kind": kind,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    layout_path().write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def clear_layout() -> dict[str, Any]:
    path = layout_path()
    if path.is_file():
        path.unlink()
    return empty_layout()
