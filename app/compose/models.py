from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

COMPOSE_VERSION = "v0.1"
ComposeKind = Literal["paper", "lecture"]


class ComposeSourceHit(BaseModel):
    ko_id: str
    title: str = ""
    score: float = 0.0
    path: str = ""


class ComposeResultMeta(BaseModel):
    schema_version: str = "0.1"
    compose_version: str = COMPOSE_VERSION
    id: str = Field(default_factory=lambda: f"cp_{uuid4().hex[:10]}")
    kind: ComposeKind
    query: str
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sources: list[ComposeSourceHit] = Field(default_factory=list)
    llm_provider: str = ""
    retrieve_mode: str = ""
    evidence: dict[str, Any] = Field(default_factory=dict)
