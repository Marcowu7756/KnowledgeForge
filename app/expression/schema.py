from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AnimationState(BaseModel):
    label: str
    caption: str = ""


class AnimationTransition(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_index: int = Field(alias="from")
    to_index: int = Field(alias="to")
    label: str = ""


class AnimationSpec(BaseModel):
    type: Literal["state_transition", "mechanism", "graph"] = "state_transition"
    states: list[AnimationState]
    transitions: list[AnimationTransition] = Field(default_factory=list)


class NarrationSpec(BaseModel):
    script: str
    voice_hint: str = "zh"


class ExpressionSchema(BaseModel):
    title: str
    animation: AnimationSpec
    narration: NarrationSpec


class AnimationSchema(BaseModel):
    """Animation-only schema (no narration)."""

    title: str
    animation: AnimationSpec


def animation_from_payload(payload: dict[str, Any]) -> AnimationSchema:
    animation_raw = payload.get("animation") or {}
    states = [
        AnimationState(
            label=str(item.get("label") or f"Step {i + 1}"),
            caption=str(item.get("caption") or ""),
        )
        for i, item in enumerate(animation_raw.get("states") or [])
        if isinstance(item, dict)
    ]
    if len(states) < 2:
        raise ValueError("animation needs at least 2 states")

    transitions: list[AnimationTransition] = []
    for item in animation_raw.get("transitions") or []:
        if not isinstance(item, dict):
            continue
        transitions.append(
            AnimationTransition(
                **{
                    "from": int(item.get("from", 0)),
                    "to": int(item.get("to", 1)),
                    "label": str(item.get("label") or ""),
                }
            )
        )
    if not transitions and len(states) >= 2:
        for i in range(len(states) - 1):
            transitions.append(
                AnimationTransition.model_validate(
                    {"from": i, "to": i + 1, "label": ""}
                )
            )

    anim_type = animation_raw.get("type") or "state_transition"
    if anim_type not in ("state_transition", "mechanism", "graph"):
        anim_type = "state_transition"

    return AnimationSchema(
        title=str(payload.get("title") or "Animation"),
        animation=AnimationSpec(
            type=anim_type,
            states=states,
            transitions=transitions,
        ),
    )


def schema_from_payload(payload: dict[str, Any]) -> ExpressionSchema:
    base = animation_from_payload(payload)
    narration_raw = payload.get("narration") or {}
    script = str(narration_raw.get("script") or payload.get("narration_script") or "").strip()
    if not script:
        raise ValueError("narration script is empty")
    return ExpressionSchema(
        title=base.title,
        animation=base.animation,
        narration=NarrationSpec(
            script=script,
            voice_hint=str(narration_raw.get("voice_hint") or "zh"),
        ),
    )
