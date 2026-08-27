from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app import config
from app.models import KnowledgeUnit

_YAML_BLOCK = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)
_CORE_IDEA = re.compile(r"## Core Idea\n\n(.*?)(?=\n## |\Z)", re.DOTALL)
_CONCEPTS = re.compile(r"## Concepts\n\n(.*?)(?=\n## |\Z)", re.DOTALL)


def global_jsonl_path() -> Path:
    return config.KNOWLEDGE_DIR / "index" / "units.jsonl"


def global_markdown_path() -> Path:
    return config.KNOWLEDGE_DIR / "index" / "INDEX.md"


def local_json_path(dest_dir: Path) -> Path:
    return dest_dir / "index.json"


def local_markdown_path(dest_dir: Path) -> Path:
    return dest_dir / "INDEX.md"


def record_from_unit(
    unit: KnowledgeUnit,
    markdown_path: str,
    *,
    source_path: str | None = None,
) -> dict[str, Any]:
    return {
        "id": unit.id,
        "title": unit.title,
        "type": unit.type,
        "source": unit.source,
        "source_path": source_path or (unit.source if "\\" in unit.source or "/" in unit.source else None),
        "url": unit.url,
        "tags": list(unit.tags),
        "concepts": list(unit.concepts),
        "summary": unit.summary,
        "path": markdown_path.replace("\\", "/"),
        "indexed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict) and item.get("path"):
            records.append(item)
    return _dedupe(records)


def save_jsonl(path: Path, records: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(item, ensure_ascii=False) for item in _dedupe(records)]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return path


def load_local_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict) and isinstance(data.get("units"), list):
        return _dedupe([u for u in data["units"] if isinstance(u, dict)])
    if isinstance(data, list):
        return _dedupe([u for u in data if isinstance(u, dict)])
    return []


def save_local_json(path: Path, records: list[dict[str, Any]], *, title: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "title": title,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(records),
        "units": _dedupe(records),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _dedupe(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep latest record per markdown path."""
    by_path: dict[str, dict[str, Any]] = {}
    for item in records:
        key = str(item.get("path") or item.get("id") or "").replace("\\", "/")
        if not key:
            continue
        by_path[key] = item
    return sorted(by_path.values(), key=lambda r: str(r.get("title") or r.get("path") or "").lower())


def render_markdown_index(
    records: list[dict[str, Any]],
    *,
    title: str,
    relative_to: Path | None = None,
) -> str:
    records = _dedupe(records)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"# {title}",
        "",
        f"Updated: {stamp}",
        f"Units: {len(records)}",
        "",
        "| Title | Type | Tags | Concepts | Path |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in records:
        path = str(item.get("path") or "")
        link = path
        if relative_to is not None and path:
            abs_path = (config.ROOT / path).resolve() if not Path(path).is_absolute() else Path(path)
            try:
                link = abs_path.relative_to(relative_to.resolve()).as_posix()
            except ValueError:
                link = path
        tags = ", ".join(item.get("tags") or [])
        concepts = ", ".join((item.get("concepts") or [])[:6])
        title_text = str(item.get("title") or "").replace("|", "\\|")
        lines.append(
            f"| [{title_text}]({link}) | {item.get('type') or ''} | {tags} | {concepts} | `{path}` |"
        )

    # Concept inverted glance (optional, lightweight).
    concept_map: dict[str, list[str]] = {}
    for item in records:
        card = str(item.get("title") or item.get("path") or "")
        for concept in item.get("concepts") or []:
            concept_map.setdefault(str(concept), []).append(card)
    if concept_map:
        lines.extend(["", "## Concepts", ""])
        for concept in sorted(concept_map, key=str.lower):
            cards = ", ".join(sorted(set(concept_map[concept])))
            lines.append(f"- **{concept}**: {cards}")

    lines.append("")
    return "\n".join(lines)


def write_markdown_index(
    path: Path,
    records: list[dict[str, Any]],
    *,
    title: str,
    relative_to: Path | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_markdown_index(records, title=title, relative_to=relative_to or path.parent),
        encoding="utf-8",
    )
    return path


def upsert_index(
    unit: KnowledgeUnit,
    markdown_path: str,
    *,
    source_path: str | None = None,
    dest_dir: Path | None = None,
    enabled: bool | None = None,
) -> dict[str, Path]:
    """Attach index artifacts for one knowledge unit. No-op when disabled."""
    if enabled is None:
        enabled = config.INDEX_ENABLED
    if not enabled:
        return {}

    record = record_from_unit(unit, markdown_path, source_path=source_path)
    written: dict[str, Path] = {}

    global_records = load_jsonl(global_jsonl_path())
    global_records.append(record)
    written["global_jsonl"] = save_jsonl(global_jsonl_path(), global_records)
    written["global_md"] = write_markdown_index(
        global_markdown_path(),
        global_records,
        title="KnowledgeForge Index",
        relative_to=global_markdown_path().parent,
    )

    if dest_dir is not None:
        local_records = load_local_json(local_json_path(dest_dir))
        local_records.append(record)
        title = f"Knowledge Index — {dest_dir.name}"
        written["local_json"] = save_local_json(local_json_path(dest_dir), local_records, title=title)
        written["local_md"] = write_markdown_index(
            local_markdown_path(dest_dir),
            local_records,
            title=title,
            relative_to=dest_dir,
        )
    return written


def parse_knowledge_markdown(path: Path) -> dict[str, Any] | None:
    """Recover an index record from an existing Knowledge Unit markdown file."""
    text = path.read_text(encoding="utf-8")
    yaml_match = _YAML_BLOCK.search(text)
    meta: dict[str, str] = {}
    if yaml_match:
        for line in yaml_match.group(1).splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"')

    title_match = re.match(r"^# (.+)$", text, re.M)
    title = meta.get("title") or (title_match.group(1).strip() if title_match else path.stem)
    summary_match = _CORE_IDEA.search(text)
    summary = summary_match.group(1).strip() if summary_match else ""
    concepts: list[str] = []
    concepts_match = _CONCEPTS.search(text)
    if concepts_match:
        for line in concepts_match.group(1).splitlines():
            if line.startswith("- ") and line[2:].strip() not in {"", "(none)"}:
                concepts.append(line[2:].strip())

    tags_raw = meta.get("tags") or "[]"
    try:
        tags = json.loads(tags_raw) if tags_raw.startswith("[") else [tags_raw]
    except json.JSONDecodeError:
        tags = []

    rel = path.resolve().relative_to(config.ROOT).as_posix()
    return {
        "id": meta.get("id") or path.stem,
        "title": title,
        "type": meta.get("type") or "md",
        "source": meta.get("source") or "",
        "source_path": meta.get("source") if meta.get("source", "").lower().endswith((".md", ".txt")) else None,
        "url": meta.get("url") or None,
        "tags": tags if isinstance(tags, list) else [],
        "concepts": concepts,
        "summary": summary,
        "path": rel,
        "indexed_at": meta.get("created")
        or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def rebuild_index(
    *,
    subdir: str | None = None,
    enabled: bool | None = None,
) -> dict[str, Path]:
    """Rebuild indexes from existing knowledge markdown files."""
    if enabled is None:
        enabled = config.INDEX_ENABLED
    if not enabled:
        return {}

    if subdir:
        scan_dir = config.KNOWLEDGE_DIR / subdir
        files = sorted(p for p in scan_dir.glob("*.md") if p.name.upper() != "INDEX.MD")
        records = [r for p in files if (r := parse_knowledge_markdown(p))]
        written: dict[str, Path] = {}
        title = f"Knowledge Index — {subdir}"
        written["local_json"] = save_local_json(local_json_path(scan_dir), records, title=title)
        written["local_md"] = write_markdown_index(
            local_markdown_path(scan_dir),
            records,
            title=title,
            relative_to=scan_dir,
        )
        # Merge into global.
        global_records = [r for r in load_jsonl(global_jsonl_path()) if not str(r.get("path", "")).startswith(f"data/knowledge/{subdir}/")]
        global_records.extend(records)
        written["global_jsonl"] = save_jsonl(global_jsonl_path(), global_records)
        written["global_md"] = write_markdown_index(
            global_markdown_path(),
            global_records,
            title="KnowledgeForge Index",
            relative_to=global_markdown_path().parent,
        )
        return written

    # Full rebuild under knowledge/
    files = sorted(
        p
        for p in config.KNOWLEDGE_DIR.rglob("*.md")
        if p.name.upper() != "INDEX.MD"
    )
    records = [r for p in files if (r := parse_knowledge_markdown(p))]
    written = {
        "global_jsonl": save_jsonl(global_jsonl_path(), records),
        "global_md": write_markdown_index(
            global_markdown_path(),
            records,
            title="KnowledgeForge Index",
            relative_to=global_markdown_path().parent,
        ),
    }

    # Local indexes per immediate subfolder that contains cards.
    by_dir: dict[Path, list[dict[str, Any]]] = {}
    for record in records:
        abs_path = config.ROOT / str(record["path"])
        parent = abs_path.parent
        if parent == config.KNOWLEDGE_DIR:
            continue
        by_dir.setdefault(parent, []).append(record)
    for dest_dir, local_records in by_dir.items():
        title = f"Knowledge Index — {dest_dir.name}"
        written[f"local_json:{dest_dir.name}"] = save_local_json(
            local_json_path(dest_dir), local_records, title=title
        )
        written[f"local_md:{dest_dir.name}"] = write_markdown_index(
            local_markdown_path(dest_dir),
            local_records,
            title=title,
            relative_to=dest_dir,
        )
    return written


# Backward-compatible name used by earlier Phase 0 code.
def append_index(unit: KnowledgeUnit, markdown_path: str) -> Path:
    paths = upsert_index(unit, markdown_path)
    return paths.get("global_jsonl", global_jsonl_path())
