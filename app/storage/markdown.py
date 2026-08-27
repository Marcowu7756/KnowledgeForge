from __future__ import annotations

import json
import re
from pathlib import Path

from app import config
from app.knowledge.access import access_to_meta_lines
from app.knowledge.taxonomy import taxonomy_to_meta_lines
from app.models import KnowledgeUnit


def slugify(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title, flags=re.UNICODE).strip().lower()
    slug = re.sub(r"[\s_]+", "_", slug)
    return slug[:80] or "untitled"


def render_markdown(unit: KnowledgeUnit) -> str:
    def bullets(items: list[str]) -> str:
        if not items:
            return "- (none)"
        return "\n".join(f"- {item}" for item in items)

    created = unit.created.strftime("%Y-%m-%dT%H:%M:%SZ")
    source_line = unit.url or unit.source
    access_lines = access_to_meta_lines(unit.access)
    access_block = ("\n".join(access_lines) + "\n") if access_lines else ""
    taxonomy_lines = taxonomy_to_meta_lines(unit.taxonomy)
    taxonomy_block = ("\n".join(taxonomy_lines) + "\n") if taxonomy_lines else ""
    taxonomy_section = ""
    if unit.taxonomy.path:
        chain = " > ".join(unit.taxonomy.path)
        taxonomy_section = f"""
## Taxonomy

{chain}
"""
    return f"""# {unit.title}

```yaml
id: {unit.id}
title: {unit.title}
source: {unit.source}
type: {unit.type}
url: {unit.url or ""}
created: {created}
tags: {json.dumps(unit.tags, ensure_ascii=False)}
{access_block}{taxonomy_block}```

## Core Idea

{unit.summary}
{taxonomy_section}
## Concepts

{bullets(unit.concepts)}

## Definitions

{bullets(unit.definitions)}

## Key Points

{bullets(unit.key_points)}

## Mechanisms

{bullets(unit.mechanisms)}

## Relationship

{bullets(unit.relationships)}

## Timeline

{bullets(unit.timeline)}

## Claims

{bullets(unit.claims)}

## Evidence

{bullets(unit.evidence)}

## Formulas

{bullets(unit.formulas)}

## Examples

{bullets(unit.examples)}

## Prerequisites

{bullets(unit.prerequisites)}

## Unknowns

{bullets(unit.unknowns)}

## Source

{unit.type}:
{source_line}
"""


def write_knowledge_unit(
    unit: KnowledgeUnit,
    dest_dir: Path | None = None,
    *,
    filename_stem: str | None = None,
) -> Path:
    dest_dir = dest_dir or config.KNOWLEDGE_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    stem = slugify(filename_stem or unit.title)
    path = dest_dir / f"{stem}.md"
    path.write_text(render_markdown(unit), encoding="utf-8")
    return path
