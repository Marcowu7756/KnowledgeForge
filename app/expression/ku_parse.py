from __future__ import annotations

import re

from app.expression.schema import AnimationSchema, AnimationSpec, AnimationState, AnimationTransition


def _section(text: str, name: str) -> str:
    match = re.search(rf"^## {re.escape(name)}\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1).strip() if match else ""


def _split_chain(line: str) -> list[str]:
    line = line.strip().lstrip("- ").strip()
    if "→" not in line and "->" not in line:
        return []
    line = line.replace("->", "→")
    if "(because" in line:
        line = line.split("(because", 1)[0].strip()
    parts = [p.strip() for p in line.split("→") if p.strip()]
    return parts


def _from_mechanisms(text: str, title: str) -> AnimationSchema | None:
    body = _section(text, "Mechanisms")
    if not body:
        return None
    for raw in body.splitlines():
        parts = _split_chain(raw)
        if len(parts) < 2:
            continue
        states = [AnimationState(label=part, caption=part) for part in parts]
        transitions = [
            AnimationTransition.model_validate({"from": i, "to": i + 1, "label": ""})
            for i in range(len(parts) - 1)
        ]
        return AnimationSchema(
            title=title,
            animation=AnimationSpec(
                type="mechanism",
                states=states,
                transitions=transitions,
            ),
        )
    return None


def _from_timeline(text: str, title: str) -> AnimationSchema | None:
    body = _section(text, "Timeline")
    if not body:
        return None
    states: list[AnimationState] = []
    for raw in body.splitlines():
        line = raw.strip().lstrip("- ").strip()
        if not line or line.startswith("("):
            continue
        if "—" in line:
            label, caption = line.split("—", 1)
        elif " - " in line:
            label, caption = line.split(" - ", 1)
        else:
            label, caption = line, line
        states.append(
            AnimationState(label=label.strip()[:40], caption=caption.strip()[:120])
        )
    if len(states) < 2:
        return None
    transitions = [
        AnimationTransition.model_validate({"from": i, "to": i + 1, "label": ""})
        for i in range(len(states) - 1)
    ]
    return AnimationSchema(
        title=title,
        animation=AnimationSpec(type="state_transition", states=states, transitions=transitions),
    )


def _from_key_points(text: str, title: str) -> AnimationSchema | None:
    body = _section(text, "Key Points")
    if not body:
        return None
    lines = [
        ln.strip().lstrip("- ").strip()
        for ln in body.splitlines()
        if ln.strip().startswith("-")
    ][:5]
    if len(lines) < 3:
        return None
    states = [AnimationState(label=f"要点{i + 1}", caption=line[:100]) for i, line in enumerate(lines)]
    transitions = [
        AnimationTransition.model_validate({"from": i, "to": i + 1, "label": ""})
        for i in range(len(states) - 1)
    ]
    return AnimationSchema(
        title=title,
        animation=AnimationSpec(type="graph", states=states, transitions=transitions),
    )


def compile_animation_fast(card_text: str, *, title: str) -> AnimationSchema | None:
    """Rule-based animation schema from KU sections (no LLM)."""
    for builder in (_from_mechanisms, _from_timeline, _from_key_points):
        schema = builder(card_text, title)
        if schema is not None:
            return schema
    return None
