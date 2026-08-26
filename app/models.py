from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


SourceType = Literal["youtube", "pdf", "docx", "md", "txt", "web", "audio", "notes"]


class IngestedSource(BaseModel):
    """Raw text extracted from one input. No compression yet."""

    source_type: SourceType
    title: str
    text: str
    url: str | None = None
    path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeUnit(BaseModel):
    """High-density knowledge card. Not a generic summary."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    title: str
    source: str
    type: SourceType
    url: str | None = None
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    summary: str
    concepts: list[str] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)
    formulas: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
