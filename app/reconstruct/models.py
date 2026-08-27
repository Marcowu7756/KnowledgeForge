from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

RECONSTRUCT_VERSION = "v0.2"

EdgeKind = Literal[
    "intra_ko",
    "shared_concept",
    "shared_tag",
    "prerequisite",
    "ko_mentions",
    "contrast_cross_ko",
]

NodeKind = Literal["concept", "knowledge_object", "theme"]


class EdgeEvidence(BaseModel):
    """Provenance for one graph edge (relation quality)."""

    rule_id: str = ""
    reason: str = ""
    sources: list[str] = Field(default_factory=list)  # KO ids or concept labels
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GraphNode(BaseModel):
    id: str
    kind: NodeKind
    label: str
    ko_ids: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")
    type: str = "related"
    kind: EdgeKind = "intra_ko"
    label: str = ""
    weight: float = 1.0
    confidence: float = 0.5
    source_ko_ids: list[str] = Field(default_factory=list)
    evidence: EdgeEvidence = Field(default_factory=EdgeEvidence)

    model_config = {"populate_by_name": True}


class RelationLayer(BaseModel):
    """Multi-KO relation layer (not a single-KO RelationEdge list)."""

    schema_version: str = "0.2"
    edges: list[GraphEdge] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)
    rules_version: str = "rq_v0.2"


class ConceptGraph(BaseModel):
    schema_version: str = "0.2"
    id: str = ""
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    generation: int = 1
    reconstruct_version: str = RECONSTRUCT_VERSION
    source_ko_ids: list[str] = Field(default_factory=list)
    nodes: list[GraphNode] = Field(default_factory=list)
    relations: RelationLayer = Field(default_factory=RelationLayer)
    evidence: dict[str, Any] = Field(default_factory=dict)


class ViewSection(BaseModel):
    title: str
    kind: str = "cluster"
    node_ids: list[str] = Field(default_factory=list)
    ko_ids: list[str] = Field(default_factory=list)
    edges: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    rationale: str = ""  # why this section exists (explainability)


class ReconstructedView(BaseModel):
    """A new knowledge structure over multiple KOs — not a text rewrite."""

    schema_version: str = "0.2"
    id: str = ""
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    view_type: Literal["theme", "concept", "learning_path", "taxonomy", "contrast"] = "theme"
    title: str = ""
    seed: str = ""
    graph_id: str = ""
    source_ko_ids: list[str] = Field(default_factory=list)
    sections: list[ViewSection] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    stability: dict[str, Any] = Field(default_factory=dict)
