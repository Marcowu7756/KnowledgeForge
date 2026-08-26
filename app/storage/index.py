from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app import config
from app.models import KnowledgeUnit


def index_path() -> Path:
    return config.KNOWLEDGE_DIR / "index" / "units.jsonl"


def append_index(unit: KnowledgeUnit, markdown_path: str) -> Path:
    """Append a one-line catalog record. No vector DB in Phase 0."""
    path = index_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "id": unit.id,
        "title": unit.title,
        "type": unit.type,
        "url": unit.url,
        "tags": unit.tags,
        "path": markdown_path,
        "indexed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path
