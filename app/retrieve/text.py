from __future__ import annotations

import hashlib
import re

from app.knowledge.object import KnowledgeObject


def ko_embed_text(obj: KnowledgeObject) -> str:
    """Canonical text for one KO embedding — whole object, not chunks."""
    c = obj.content
    relations = []
    for edge in obj.relations[:12]:
        relations.append(f"{edge.from_node}→{edge.to_node}")
    parts = [
        c.title.strip(),
        (c.summary or "").strip(),
        "概念: " + "、".join(c.atomic_concepts[:20]),
        "要点: " + "；".join(c.key_points[:8]),
        "机制: " + "；".join(c.mechanisms[:6]),
        "关系: " + "；".join(relations),
        "标签: " + "、".join(c.tags[:12]),
    ]
    if obj.taxonomy.path:
        parts.append("分类: " + " > ".join(obj.taxonomy.path))
    text = "\n".join(p for p in parts if p and not p.endswith(": "))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:4000]


def text_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def vector_id_for(ko_id: str, model: str) -> str:
    raw = f"{ko_id}|{model}"
    return "emb_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
