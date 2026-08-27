from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

RETRIEVE_VERSION = "v0.1"


class RetrieveHit(BaseModel):
    ko_id: str
    title: str = ""
    score: float
    semantic_score: float = 0.0
    graph_score: float = 0.0
    path: str = ""
    concepts: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    summary: str = ""
    why: list[str] = Field(default_factory=list)  # explainability
    vector_id: str = ""
    classification: str = "public"
    access_policy: dict[str, Any] = Field(default_factory=dict)


class RetrieveResult(BaseModel):
    schema_version: str = "0.1"
    retrieve_version: str = RETRIEVE_VERSION
    query: str
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mode: Literal["semantic", "graph_aware"] = "semantic"
    top_k: int = 5
    hits: list[RetrieveHit] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class IndexRecord(BaseModel):
    ko_id: str
    vector_id: str
    title: str = ""
    path: str = ""
    concepts: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    summary: str = ""
    text_hash: str = ""
    indexed_at: str = ""
    classification: str = "public"
    source_project: str = ""
    export_policy: str = "export_ok"
    # Compact access policy snapshot (empty → derive from classification).
    access_policy: dict[str, Any] = Field(default_factory=dict)
    taxonomy_path: list[str] = Field(default_factory=list)


class IndexManifest(BaseModel):
    kind: str = "ko_embedding_index"
    schema_version: str = "0.1"
    retrieve_version: str = RETRIEVE_VERSION
    model: str = ""
    dim: int = 0
    count: int = 0
    ko_ids: list[str] = Field(default_factory=list)
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evidence: dict[str, Any] = Field(default_factory=dict)
