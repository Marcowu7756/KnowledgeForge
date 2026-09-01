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
    """Detect language tag from plain text (voice routing helper)."""
    if re.search(r"[\u3040-\u309f\u30a0-\u30ff]", text):
        return "ja"
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh-CN"
    if re.search(r"[A-Za-z]", text):
        return "en"
    return "unknown"


class AudioLanguageNotSupportedError(RuntimeError):
    """KO language has no registered narration template / voice gate."""

    def __init__(self, language: str, *, ko_id: str = "") -> None:
        self.language = language
        self.ko_id = ko_id
        super().__init__(
            f"audio expression HOLD: language={language!r} not supported"
            + (f" ko={ko_id!r}" if ko_id else "")
        )


SUPPORTED_AUDIO_LANGUAGES = frozenset({"zh-CN", "en"})


def _voice_name_for_script(lang: str) -> str | None:
    from app.voice.bank import voice_for_language

    return voice_for_language(lang)


def _ko_canonical_blob(obj: KnowledgeObject) -> str:
    chunks: list[str] = [
        obj.content.title,
        obj.content.summary,
        *obj.content.key_points,
        *obj.content.mechanisms,
        *obj.content.definitions,
        *obj.content.claims,
    ]
    for edge in obj.relations:
        chunks.extend([edge.from_node, edge.to_node, edge.label])
    return " ".join(c.strip() for c in chunks if c and c.strip())


def _detect_ko_language(obj: KnowledgeObject) -> str:
    """Language of canonical KO meaning — not the derived narration script."""
    blob = _ko_canonical_blob(obj)
    if not blob.strip():
        return "unknown"
    if re.search(r"[\u3040-\u309f\u30a0-\u30ff]", blob):
        return "ja"
    cjk = len(re.findall(r"[\u4e00-\u9fff]", blob))
    latin = len(re.findall(r"[A-Za-z]", blob))
    if cjk > 0 and cjk >= latin:
        return "zh-CN"
    if latin > 0:
        return "en"
    if re.search(r"[\u0400-\u04ff]", blob):
        return "ru"
    return "unknown"


def _normalize_audio_language(tag: str) -> str:
    low = (tag or "").strip().lower()
    if low.startswith("zh"):
        return "zh-CN"
    if low.startswith("en"):
        return "en"
    return low or "unknown"


def _ends_with_punct(text: str, endings: tuple[str, ...]) -> bool:
    return any(text.endswith(end) for end in endings)


def _ensure_end(text: str, endings: tuple[str, ...], default: str) -> str:
    text = text.strip()
    if not text:
        return text
    if _ends_with_punct(text, endings):
        return text
    return text + default


def _ko_canonical_parts(obj: KnowledgeObject) -> dict[str, object]:
    return {
        "title": obj.content.title.strip(),
        "summary": (obj.content.summary or "").strip(),
        "mechanisms": [m.strip().lstrip("- ").strip() for m in obj.content.mechanisms if m.strip()],
        "key_points": [k.strip() for k in obj.content.key_points if k.strip()],
        "relations": obj.relations[:4],
    }


def _relation_phrase(edge: RelationEdge, lang: str) -> str:
    if lang == "zh-CN":
        if edge.type == "controls":
            return f"{edge.from_node}作用于{edge.to_node}"
        return f"{edge.from_node}关联{edge.to_node}"
    if edge.label.strip():
        return f"{edge.from_node} {edge.label.strip()} {edge.to_node}".strip()
    if edge.type == "controls":
        return f"{edge.from_node} controls {edge.to_node}"
    return f"{edge.from_node} relates to {edge.to_node}"


def _assemble_script_zh(parts: dict[str, object]) -> str:
    title = str(parts["title"])
    summary = str(parts["summary"])
    mechanisms: list[str] = parts["mechanisms"]  # type: ignore[assignment]
    key_points: list[str] = parts["key_points"]  # type: ignore[assignment]
    relations: list[RelationEdge] = parts["relations"]  # type: ignore[assignment]

    segments: list[str] = []
    if title:
        segments.append(_ensure_end(title, ("。", "！", "？"), "。"))
    if summary:
        segments.append(_ensure_end(summary, ("。", "！", "？"), "。"))
    if relations:
        rel = "；".join(_relation_phrase(edge, "zh-CN") for edge in relations)
        segments.append(_ensure_end(rel, ("。",), "。"))
    elif mechanisms:
        segments.append(_ensure_end(mechanisms[0], ("。",), "。"))
    elif key_points:
        segments.append(_ensure_end("；".join(key_points[:3]), ("。",), "。"))

    script = "".join(segments).strip()
    if len(script) < 20:
        script = f"{title}。{summary or '这是一个待展开的知识单元。'}".strip()
    if len(script) > 400:
        script = script[:397] + "…"
    return script


def _assemble_script_en(parts: dict[str, object]) -> str:
    title = str(parts["title"])
    summary = str(parts["summary"])
    mechanisms: list[str] = parts["mechanisms"]  # type: ignore[assignment]
    key_points: list[str] = parts["key_points"]  # type: ignore[assignment]
    relations: list[RelationEdge] = parts["relations"]  # type: ignore[assignment]

    segments: list[str] = []
    if title:
        segments.append(_ensure_end(title, (".", "!", "?"), "."))
    if summary:
        segments.append(_ensure_end(summary, (".", "!", "?"), "."))
    if relations:
        rel = "; ".join(_relation_phrase(edge, "en") for edge in relations)
        segments.append(_ensure_end(rel, (".",), "."))
    elif mechanisms:
        segments.append(_ensure_end(mechanisms[0], (".",), "."))
    elif key_points:
        segments.append(_ensure_end("; ".join(key_points[:3]), (".",), "."))

    script = " ".join(segments).strip()
    if len(script) < 20:
        script = f"{title}. {summary or 'This knowledge unit is pending expansion.'}".strip()
    if len(script) > 400:
        script = script[:397] + "…"
    return script


def derive_audio_from_ko(
    obj: KnowledgeObject,
    *,
    voice: str | None = None,
    compile_source: str = "ko_structure",
) -> AudioExpression:
    """Derive AudioExpression from KO canonical meaning (no LLM, no cross-language shell)."""
    lang_tag = _normalize_audio_language(_detect_ko_language(obj))
    if lang_tag not in SUPPORTED_AUDIO_LANGUAGES:
        raise AudioLanguageNotSupportedError(_detect_ko_language(obj), ko_id=obj.id)

    parts = _ko_canonical_parts(obj)
    if lang_tag == "zh-CN":
        script = _assemble_script_zh(parts)
        resolved_voice = voice or _voice_name_for_script("zh-CN")
    else:
        script = _assemble_script_en(parts)
        resolved_voice = voice or _voice_name_for_script("en")

    expr_id = f"ax_{obj.id}_{uuid4().hex[:6]}"
    return AudioExpression(
        id=expr_id,
        source_ko=obj.id,
        script=script,
        voice=resolved_voice,
        language=lang_tag,
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
