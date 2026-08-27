from __future__ import annotations

import re
from uuid import uuid4

from app import config
from app.expression.objects import (
    DEFAULT_RENDERER,
    EXPRESSION_VERSION,
    AudioExpression,
    ExpressionEvidence,
    StoryboardStep,
    VisualExpression,
)
from app.expression.schema import (
    AnimationSchema,
    AnimationSpec,
    AnimationState,
    AnimationTransition,
)
from app.knowledge.object import KnowledgeObject, RelationEdge


def _intent_for(anim_type: str) -> str:
    return {
        "mechanism": "explain_mechanism",
        "state_transition": "explain_state_transition",
        "graph": "explain_graph",
    }.get(anim_type, "explain_state_transition")


def _storyboard_from_animation(animation: AnimationSpec) -> list[StoryboardStep]:
    steps: list[StoryboardStep] = []
    for i, state in enumerate(animation.states):
        transition = ""
        if i < len(animation.transitions):
            transition = animation.transitions[i].label
        elif i > 0 and i - 1 < len(animation.transitions):
            transition = animation.transitions[i - 1].label
        steps.append(
            StoryboardStep(
                step=i + 1,
                state=state.label,
                transition=transition if i > 0 else "initial",
                caption=state.caption,
            )
        )
    if steps:
        steps[0].transition = steps[0].transition or "initial"
        if len(steps) > 1:
            steps[-1].transition = steps[-1].transition or "final"
    return steps


def _split_chain(line: str) -> list[str]:
    line = line.strip().lstrip("- ").strip()
    if "→" not in line and "->" not in line:
        return []
    line = line.replace("->", "→")
    if "(because" in line:
        line = line.split("(because", 1)[0].strip()
    return [p.strip() for p in line.split("→") if p.strip()]


def _animation_from_relations(edges: list[RelationEdge], title: str) -> AnimationSchema | None:
    if not edges:
        return None
    # Prefer a connected chain: walk edges in order, dedupe nodes.
    nodes: list[str] = []
    labels: list[str] = []
    for edge in edges[:6]:
        if not nodes:
            nodes.append(edge.from_node)
        if edge.from_node == nodes[-1]:
            nodes.append(edge.to_node)
            labels.append(edge.label or edge.type)
        elif edge.to_node not in nodes:
            nodes.append(edge.to_node)
            labels.append(edge.label or edge.type)
    if len(nodes) < 2:
        return None
    states = [AnimationState(label=n[:40], caption=n[:120]) for n in nodes]
    transitions = [
        AnimationTransition.model_validate(
            {"from": i, "to": i + 1, "label": labels[i] if i < len(labels) else ""}
        )
        for i in range(len(states) - 1)
    ]
    return AnimationSchema(
        title=title,
        animation=AnimationSpec(
            type="mechanism" if any(e.type == "controls" for e in edges) else "state_transition",
            states=states,
            transitions=transitions,
        ),
    )


def _animation_from_mechanisms(lines: list[str], title: str) -> AnimationSchema | None:
    for raw in lines:
        parts = _split_chain(raw)
        if len(parts) < 2:
            continue
        states = [AnimationState(label=p[:40], caption=p[:120]) for p in parts]
        transitions = [
            AnimationTransition.model_validate({"from": i, "to": i + 1, "label": ""})
            for i in range(len(states) - 1)
        ]
        return AnimationSchema(
            title=title,
            animation=AnimationSpec(type="mechanism", states=states, transitions=transitions),
        )
    return None


def _animation_from_timeline(lines: list[str], title: str) -> AnimationSchema | None:
    states: list[AnimationState] = []
    for raw in lines:
        line = raw.strip().lstrip("- ").strip()
        if not line or line.startswith("("):
            continue
        if "—" in line:
            label, caption = line.split("—", 1)
        elif " - " in line:
            label, caption = line.split(" - ", 1)
        else:
            label, caption = line, line
        states.append(AnimationState(label=label.strip()[:40], caption=caption.strip()[:120]))
    if len(states) < 2:
        return None
    transitions = [
        AnimationTransition.model_validate({"from": i, "to": i + 1, "label": ""})
        for i in range(len(states) - 1)
    ]
    return AnimationSchema(
        title=title,
        animation=AnimationSpec(
            type="state_transition",
            states=states,
            transitions=transitions,
        ),
    )


def _animation_from_concepts(concepts: list[str], title: str) -> AnimationSchema | None:
    items = [c.strip() for c in concepts if c.strip()][:5]
    if len(items) < 2:
        return None
    states = [AnimationState(label=c[:40], caption=c[:120]) for c in items]
    transitions = [
        AnimationTransition.model_validate({"from": i, "to": i + 1, "label": "related"})
        for i in range(len(states) - 1)
    ]
    return AnimationSchema(
        title=title,
        animation=AnimationSpec(type="graph", states=states, transitions=transitions),
    )


def derive_visual_from_ko(
    obj: KnowledgeObject,
    *,
    compile_source: str = "ko_structure",
    renderer: str = DEFAULT_RENDERER,
) -> VisualExpression:
    """Derive VisualExpression from KO structure (relations + content). No LLM."""
    title = obj.content.title
    schema = (
        _animation_from_mechanisms(obj.content.mechanisms, title)
        or _animation_from_relations(obj.relations, title)
        or _animation_from_timeline(obj.content.timeline, title)
        or _animation_from_concepts(obj.content.atomic_concepts, title)
    )
    if schema is None:
        # Minimal fallback so KO always yields an expression object
        summary = (obj.content.summary or title).strip()[:120]
        schema = AnimationSchema(
            title=title,
            animation=AnimationSpec(
                type="state_transition",
                states=[
                    AnimationState(label="概念", caption=title[:80]),
                    AnimationState(label="要点", caption=summary or title[:80]),
                ],
                transitions=[
                    AnimationTransition.model_validate(
                        {"from": 0, "to": 1, "label": "explains"}
                    )
                ],
            ),
        )
        compile_source = "ko_fallback"

    anim_type = schema.animation.type
    expr_id = f"vx_{obj.id}_{uuid4().hex[:6]}"
    return VisualExpression(
        id=expr_id,
        source_ko=obj.id,
        title=schema.title,
        intent=_intent_for(anim_type),  # type: ignore[arg-type]
        storyboard=_storyboard_from_animation(schema.animation),
        animation=schema.animation,
        renderer=renderer,
        evidence=ExpressionEvidence(
            derived_from=obj.id,
            expression_version=EXPRESSION_VERSION,
            renderer=renderer,
            compile_source=compile_source,
            models={"harness": obj.evidence.pipeline or "harness_v0.1"},
        ),
    )


def _detect_language(text: str) -> str:
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh-CN"
    return "en"


def derive_audio_from_ko(
    obj: KnowledgeObject,
    *,
    voice: str | None = None,
    compile_source: str = "ko_structure",
) -> AudioExpression:
    """Derive AudioExpression script from KO content + relations (no LLM)."""
    title = obj.content.title.strip()
    summary = (obj.content.summary or "").strip()
    parts: list[str] = []
    if title:
        parts.append(f"我们来理解「{title}」。")
    if summary:
        parts.append(summary if summary.endswith(("。", "！", "？", ".", "!", "?")) else summary + "。")

    if obj.relations:
        chain = []
        for edge in obj.relations[:4]:
            chain.append(f"{edge.from_node}作用于{edge.to_node}" if edge.type == "controls" else f"{edge.from_node}关联{edge.to_node}")
        parts.append("核心关系是：" + "；".join(chain) + "。")
    elif obj.content.mechanisms:
        mech = obj.content.mechanisms[0].strip().lstrip("- ").strip()
        parts.append(f"关键机制是：{mech}。")
    elif obj.content.key_points:
        pts = "；".join(obj.content.key_points[:3])
        parts.append(f"需要抓住这几点：{pts}。")

    script = "".join(parts).strip()
    if len(script) < 20:
        script = f"{title}。{summary or '这是一个待展开的知识单元。'}"

    # Keep spoken length reasonable
    if len(script) > 400:
        script = script[:397] + "…"

    voice_name = voice or config.TTS_VOICE_NAME or "local_voice"
    lang = _detect_language(script)
    expr_id = f"ax_{obj.id}_{uuid4().hex[:6]}"
    return AudioExpression(
        id=expr_id,
        source_ko=obj.id,
        script=script,
        voice=voice_name,
        language=lang,
        evidence=ExpressionEvidence(
            derived_from=obj.id,
            expression_version=EXPRESSION_VERSION,
            voice_model=config.TTS_ENGINE or "tts",
            compile_source=compile_source,
            models={
                "tts": config.TTS_ENGINE or "",
                "harness": obj.evidence.pipeline or "harness_v0.1",
            },
        ),
    )


def visual_to_animation_schema(expr: VisualExpression) -> AnimationSchema:
    return AnimationSchema(title=expr.title, animation=expr.animation)
