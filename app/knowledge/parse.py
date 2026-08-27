from __future__ import annotations

import json
import re
from pathlib import Path

from app.knowledge.access import AccessBlock, access_from_meta
from app.knowledge.object import (
    KnowledgeObject,
    SourceRef,
    from_knowledge_unit,
)
from app.knowledge.taxonomy import TaxonomyBlock, taxonomy_from_meta
from app.knowledge.yaml_meta import parse_card_yaml
from app.models import KnowledgeUnit, SourceType

_YAML_BLOCK = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)
_SECTION = re.compile(r"^## ([^\n]+)\n+(.*?)(?=^## |\Z)", re.M | re.S)


def _bullets(body: str) -> list[str]:
    items: list[str] = []
    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith("- "):
            items.append(line[2:].strip())
    return items


def _yaml_map(block: str) -> dict[str, str]:
    meta = parse_card_yaml(block)
    out: dict[str, str] = {}
    for key, value in meta.items():
        if key == "access" and isinstance(value, dict):
            continue
        if isinstance(value, (list, dict)):
            out[key] = json.dumps(value, ensure_ascii=False)
        elif value is None:
            out[key] = ""
        else:
            out[key] = str(value)
    return out


def _access_from_block(block: str) -> AccessBlock:
    meta = parse_card_yaml(block)
    return access_from_meta(meta)


def _taxonomy_from_block(block: str) -> TaxonomyBlock:
    meta = parse_card_yaml(block)
    return taxonomy_from_meta(meta)


def load_unit_from_markdown(path: Path) -> KnowledgeUnit:
    """Best-effort parse of a distill-era KU markdown card."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    title_match = re.match(r"^# (.+)$", text, re.M)
    title = title_match.group(1).strip() if title_match else path.stem

    yaml_match = _YAML_BLOCK.search(text)
    meta = _yaml_map(yaml_match.group(1)) if yaml_match else {}
    access = _access_from_block(yaml_match.group(1)) if yaml_match else AccessBlock()
    taxonomy = _taxonomy_from_block(yaml_match.group(1)) if yaml_match else TaxonomyBlock()

    sections: dict[str, str] = {}
    for match in _SECTION.finditer(text):
        sections[match.group(1).strip()] = match.group(2).strip()

    source_type = meta.get("type", "md")
    if source_type not in {
        "youtube",
        "bilibili",
        "twitter",
        "pdf",
        "docx",
        "md",
        "txt",
        "image",
        "web",
        "audio",
        "notes",
    }:
        source_type = "md"

    return KnowledgeUnit(
        id=meta.get("id") or path.stem[:12],
        title=meta.get("title") or title,
        source=meta.get("source") or str(path),
        type=source_type,  # type: ignore[arg-type]
        url=meta.get("url") or None,
        summary=sections.get("Core Idea", ""),
        concepts=_bullets(sections.get("Concepts", "")),
        definitions=_bullets(sections.get("Definitions", "")),
        key_points=_bullets(sections.get("Key Points", "")),
        mechanisms=_bullets(sections.get("Mechanisms", "")),
        relationships=_bullets(sections.get("Relationship", "")),
        timeline=_bullets(sections.get("Timeline", "")),
        claims=_bullets(sections.get("Claims", "")),
        evidence=_bullets(sections.get("Evidence", "")),
        formulas=_bullets(sections.get("Formulas", "")),
        examples=_bullets(sections.get("Examples", "")),
        prerequisites=_bullets(sections.get("Prerequisites", "")),
        unknowns=_bullets(sections.get("Unknowns", "")),
        tags=json.loads(meta["tags"]) if meta.get("tags", "").startswith("[") else [],
        access=access,
        taxonomy=taxonomy,
    )


def load_knowledge_object(
    path: Path,
    *,
    source: SourceRef | None = None,
) -> KnowledgeObject:
    path = path.expanduser().resolve()
    if path.name == "knowledge_object.json" or path.suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return KnowledgeObject.model_validate(payload)

    unit = load_unit_from_markdown(path)
    src = source or SourceRef(
        type=unit.type,
        origin=str(path),
        path=str(path),
        url=unit.url,
        mode="from_card",
    )
    return from_knowledge_unit(unit, source=src, knowledge_md=path.as_posix())


def write_knowledge_object(obj: KnowledgeObject, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        obj.model_dump_json(indent=2, by_alias=True) + "\n",
        encoding="utf-8",
    )
    return dest
