from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.knowledge.access import AccessBlock
from app.knowledge.memory import MemoryKind, SetvArtifactRef
from app.knowledge.taxonomy import TaxonomyBlock
from app.models import KnowledgeUnit, SourceType

RelationType = Literal[
    "controls",
    "causes",
    "depends_on",
    "contrasts",
    "part_of",
    "related",
    "defines",
]


class SourceRef(BaseModel):
    type: SourceType | Literal["card", "package"] = "notes"
    origin: str = ""
    url: str | None = None
    path: str | None = None
    hash: str = ""
    mode: Literal["ingest", "from_card"] = "ingest"


class ContentBlock(BaseModel):
    title: str
    summary: str = ""
    atomic_concepts: list[str] = Field(default_factory=list)
    definitions: list[str] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)
    mechanisms: list[str] = Field(default_factory=list)
    timeline: list[str] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    evidence_notes: list[str] = Field(default_factory=list)
    formulas: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class RelationEdge(BaseModel):
    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")
    type: RelationType = "related"
    label: str = ""

    model_config = {"populate_by_name": True}


class VisualRef(BaseModel):
    type: Literal["gif", "none"] = "none"
    artifact: str = ""
    expression: str = ""  # visual_expression.json
    schema_id: str = Field(default="", alias="schema")
    animation_type: str = ""
    compile_source: str = ""  # ko_structure | fast | llm | express
    intent: str = ""
    renderer: str = ""

    model_config = {"populate_by_name": True}


class AudioRef(BaseModel):
    type: Literal["tts", "none"] = "none"
    voice: str = ""
    artifact: str = ""
    expression: str = ""  # audio_expression.json
    engine: str = ""
    language: str = ""
    compile_source: str = ""


class EmbeddingRef(BaseModel):
    model: str = ""
    vector_id: str = ""
    status: Literal["pending", "ready", "none"] = "none"


class ModelVersions(BaseModel):
    llm: str = ""
    llm_provider: str = ""
    asr: str = ""
    embed: str = ""
    tts: str = ""
    vocos: str = ""
    ocr: str = ""
    harness: str = "harness_v0.1"


class EvidenceBlock(BaseModel):
    pipeline: str = "harness_v0.1"
    package_id: str = ""
    models: ModelVersions = Field(default_factory=ModelVersions)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)


class Lifecycle(BaseModel):
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: Literal["draft", "compiled", "partial", "failed"] = "draft"
    version: int = 1


class KnowledgeObject(BaseModel):
    """System-level knowledge object (KU upgraded). Schema v0.1."""

    schema_version: str = "0.1"
    id: str = Field(default_factory=lambda: f"ko_{uuid4().hex[:12]}")
    source: SourceRef = Field(default_factory=SourceRef)
    access: AccessBlock = Field(default_factory=AccessBlock)
    taxonomy: TaxonomyBlock = Field(default_factory=TaxonomyBlock)
    memory_kind: MemoryKind = "semantic"
    setv_artifact: SetvArtifactRef | None = None
    content: ContentBlock
    relations: list[RelationEdge] = Field(default_factory=list)
    visual: VisualRef = Field(default_factory=VisualRef)
    audio: AudioRef = Field(default_factory=AudioRef)
    embedding: EmbeddingRef = Field(default_factory=EmbeddingRef)
    evidence: EvidenceBlock = Field(default_factory=EvidenceBlock)
    lifecycle: Lifecycle = Field(default_factory=Lifecycle)
    # Backward link to distill-era markdown card
    knowledge_md: str = ""
    unit_id: str = ""

    def touch(self, *, status: str | None = None) -> None:
        self.lifecycle.updated = datetime.now(timezone.utc)
        self.lifecycle.version += 1
        if status:
            self.lifecycle.status = status  # type: ignore[assignment]


def _parse_contrast_line(raw: str) -> RelationEdge | None:
    for sep in (
        " vs ",
        " VS ",
        " versus ",
        " Versus ",
        " 对比 ",
        " 相对于 ",
        " 区别于 ",
        " 不同于 ",
        " 对照 ",
        " 相较 ",
    ):
        if sep in raw:
            left, right = raw.split(sep, 1)
            left, right = left.strip(), right.strip()
            if left and right:
                return RelationEdge.model_validate(
                    {
                        "from": left,
                        "to": right,
                        "type": "contrasts",
                        "label": sep.strip(),
                    }
                )
    return None


def _parse_relation_line(line: str) -> RelationEdge | None:
    raw = line.strip().lstrip("- ").strip()
    if not raw:
        return None
    contrast = _parse_contrast_line(raw)
    if contrast is not None:
        return contrast
    for sep in ("→", "->", "⇒"):
        if sep in raw:
            left, right = raw.split(sep, 1)
            label = ""
            if "(because" in right:
                right, _, rest = right.partition("(because")
                label = rest.rstrip(")").strip()
            frm = left.strip()
            to = right.strip()
            if frm and to:
                return RelationEdge.model_validate(
                    {"from": frm, "to": to, "type": "causes", "label": label}
                )
    return None


def relations_from_unit(unit: KnowledgeUnit) -> list[RelationEdge]:
    edges: list[RelationEdge] = []
    seen: set[tuple[str, str]] = set()
    for line in list(unit.relationships) + list(unit.mechanisms):
        edge = _parse_relation_line(line)
        if edge is None:
            continue
        key = (edge.from_node, edge.to_node)
        if key in seen:
            continue
        seen.add(key)
        edges.append(edge)
    return edges


def from_knowledge_unit(
    unit: KnowledgeUnit,
    *,
    source: SourceRef | None = None,
    knowledge_md: str = "",
    access: AccessBlock | None = None,
) -> KnowledgeObject:
    src = source or SourceRef(
        type=unit.type,
        origin=unit.source,
        url=unit.url,
        path=None,
        mode="ingest",
    )
    return KnowledgeObject(
        id=f"ko_{unit.id}",
        unit_id=unit.id,
        source=src,
        access=access or unit.access,
        taxonomy=unit.taxonomy,
        memory_kind=unit.memory_kind,
        setv_artifact=unit.setv_artifact,
        content=ContentBlock(
            title=unit.title,
            summary=unit.summary,
            atomic_concepts=list(unit.concepts),
            definitions=list(unit.definitions),
            key_points=list(unit.key_points),
            mechanisms=list(unit.mechanisms),
            timeline=list(unit.timeline),
            claims=list(unit.claims),
            evidence_notes=list(unit.evidence),
            formulas=list(unit.formulas),
            examples=list(unit.examples),
            prerequisites=list(unit.prerequisites),
            unknowns=list(unit.unknowns),
            tags=list(unit.tags),
        ),
        relations=relations_from_unit(unit),
        knowledge_md=knowledge_md,
        lifecycle=Lifecycle(status="compiled"),
    )
