from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.expression.schema import AnimationSpec

EXPRESSION_VERSION = "v0.1"
DEFAULT_RENDERER = "pillow_v1"


class StoryboardStep(BaseModel):
    step: int
    state: str = ""
    transition: str = ""
    caption: str = ""


class ExpressionEvidence(BaseModel):
    """Provenance for a derived expression (not the KO itself)."""

    derived_from: str = ""
    expression_version: str = EXPRESSION_VERSION
    renderer: str = ""
    voice_model: str = ""
    compile_source: str = ""  # ko_structure | ko_llm | card_fast | card_llm
    models: dict[str, str] = Field(default_factory=dict)
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VisualExpression(BaseModel):
    """KO → animation IR. Artifacts (gif) are rendered from this object."""

    schema_version: str = "0.1"
    type: Literal["animation"] = "animation"
    id: str = ""
    source_ko: str = ""
    title: str = ""
    intent: Literal[
        "explain_state_transition",
        "explain_mechanism",
        "explain_graph",
    ] = "explain_state_transition"
    storyboard: list[StoryboardStep] = Field(default_factory=list)
    animation: AnimationSpec
    renderer: str = DEFAULT_RENDERER
    evidence: ExpressionEvidence = Field(default_factory=ExpressionEvidence)
    artifact: str = ""  # relative package path after render

    def to_animation_schema_payload(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "animation": self.animation.model_dump(mode="json", by_alias=True),
        }


class AudioExpression(BaseModel):
    """KO → narration IR. Artifacts (wav) are rendered from this object."""

    schema_version: str = "0.1"
    type: Literal["narration"] = "narration"
    id: str = ""
    source_ko: str = ""
    script: str = ""
    voice: str = ""
    language: str = "zh-CN"
    evidence: ExpressionEvidence = Field(default_factory=ExpressionEvidence)
    artifact: str = ""
