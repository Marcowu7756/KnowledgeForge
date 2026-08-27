from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def render_english_derive(payload: dict[str, Any], *, parent_path: str) -> str:
    title = str(payload.get("title") or "English derivation")
    focus = str(payload.get("focus") or "")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        f"# {title} — Examples & Usage",
        "",
        "```yaml",
        "kind: derive",
        "mode: english",
        f"parent: {parent_path}",
        f"created: {stamp}",
        f"focus: {focus}",
        "```",
        "",
        "## Focus",
        "",
        focus or "(none)",
        "",
        "## Patterns",
        "",
    ]
    patterns = payload.get("patterns") or []
    lines.extend([f"- {p}" for p in patterns] or ["- (none)"])
    lines.extend(["", "## Examples", ""])
    for i, ex in enumerate(payload.get("examples") or [], start=1):
        if not isinstance(ex, dict):
            lines.append(f"{i}. {ex}")
            continue
        lines.extend(
            [
                f"### {i}. {ex.get('sentence', '')}",
                "",
                f"- pattern: `{ex.get('pattern', '')}`",
                f"- gloss: {ex.get('gloss', '')}",
                f"- level: {ex.get('level', '')}",
                "",
            ]
        )
    lines.extend(["", "## Contrast (common mistakes)", ""])
    for item in payload.get("contrast") or []:
        if not isinstance(item, dict):
            lines.append(f"- {item}")
            continue
        lines.extend(
            [
                f"- ❌ {item.get('wrong', '')}",
                f"  ✅ {item.get('right', '')}",
                f"  why: {item.get('why', '')}",
            ]
        )
    lines.extend(["", "## Usage tips", ""])
    tips = payload.get("usage_tips") or []
    lines.extend([f"- {t}" for t in tips] or ["- (none)"])
    lines.extend(["", "## Mini drills", ""])
    drills = payload.get("mini_drills") or []
    lines.extend([f"- {d}" for d in drills] or ["- (none)"])
    lines.append("")
    return "\n".join(lines)


def render_physics_derive(payload: dict[str, Any], *, parent_path: str) -> str:
    title = str(payload.get("title") or "Physics derivation")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"# {title} — Process Unfolding",
        "",
        "```yaml",
        "kind: derive",
        "mode: physics",
        f"parent: {parent_path}",
        f"created: {stamp}",
        "```",
        "",
        "## Abstraction",
        "",
        str(payload.get("abstraction") or ""),
        "",
        "## Everyday anchor",
        "",
        str(payload.get("everyday_anchor") or ""),
        "",
        "## Process",
        "",
    ]
    for step in payload.get("process") or []:
        if not isinstance(step, dict):
            lines.append(f"- {step}")
            continue
        lines.extend(
            [
                f"### Step {step.get('step', '?')}: {step.get('name', '')}",
                "",
                f"- what happens: {step.get('what_happens', '')}",
                f"- why it matters: {step.get('why_it_matters', '')}",
                f"- visual: {step.get('visual', '')}",
                f"- symbols: `{step.get('symbols', '')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Analogy",
            "",
            str(payload.get("analogy") or ""),
            "",
            "## Common misconceptions",
            "",
        ]
    )
    misconceptions = payload.get("common_misconceptions") or []
    lines.extend([f"- {m}" for m in misconceptions] or ["- (none)"])
    lines.extend(["", "## Check questions", ""])
    questions = payload.get("check_questions") or []
    lines.extend([f"- {q}" for q in questions] or ["- (none)"])
    lines.extend(
        [
            "",
            "## Manim beats (DEFER — storyboard only; not wired to expression)",
            "",
            "> Status: `not_wired_to_expression`. These beats are planning text only;",
            "> they do **not** drive GIF/Manim renderers in the current pipeline.",
            "",
        ]
    )
    for beat in payload.get("manim_beats") or []:
        if not isinstance(beat, dict):
            lines.append(f"- {beat}")
            continue
        lines.extend(
            [
                f"### {beat.get('scene', '')}",
                "",
                f"- on screen: {beat.get('on_screen', '')}",
                f"- narration: {beat.get('narration', '')}",
                "",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def render_finance_derive(payload: dict[str, Any], *, parent_path: str) -> str:
    title = str(payload.get("title") or "Finance derivation")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"# {title} — Causal & Scenario Expansion",
        "",
        "```yaml",
        "kind: derive",
        "mode: finance",
        f"parent: {parent_path}",
        f"created: {stamp}",
        "```",
        "",
        "## Thesis",
        "",
        str(payload.get("thesis") or ""),
        "",
        "## Causal chain",
        "",
    ]
    for item in payload.get("causal_chain") or []:
        if not isinstance(item, dict):
            lines.append(f"- {item}")
            continue
        lines.append(
            f"{item.get('step', '?')}. {item.get('from', '')} → {item.get('to', '')} "
            f"(because {item.get('because', '')})"
        )
    lines.extend(["", "## Regime shift", ""])
    for item in payload.get("regime_shift") or []:
        if not isinstance(item, dict):
            lines.append(f"- {item}")
            continue
        lines.extend(
            [
                f"- before: {item.get('before', '')}",
                f"  after: {item.get('after', '')}",
                f"  trigger: {item.get('trigger', '')}",
            ]
        )
    lines.extend(["", "## Asset map", ""])
    for item in payload.get("asset_map") or []:
        if not isinstance(item, dict):
            lines.append(f"- {item}")
            continue
        lines.append(
            f"- {item.get('asset', '')}: {item.get('direction', '')} — {item.get('why', '')}"
        )
    lines.extend(["", "## Scenarios", ""])
    for item in payload.get("scenarios") or []:
        if not isinstance(item, dict):
            lines.append(f"- {item}")
            continue
        lines.extend(
            [
                f"### {item.get('name', '')}",
                "",
                f"- if: {item.get('if', '')}",
                f"- then: {item.get('then', '')}",
                f"- watch: {item.get('watch', '')}",
                "",
            ]
        )
    lines.extend(["", "## Historical anchors", ""])
    anchors = payload.get("historical_anchors") or []
    lines.extend([f"- {a}" for a in anchors] or ["- (none)"])
    lines.extend(["", "## Investor checklist", ""])
    checks = payload.get("investor_checklist") or []
    lines.extend([f"- {c}" for c in checks] or ["- (none)"])
    lines.extend(["", "## Open risks", ""])
    risks = payload.get("open_risks") or []
    lines.extend([f"- {r}" for r in risks] or ["- (none)"])
    lines.append("")
    return "\n".join(lines)


def render_generic_derive(payload: dict[str, Any], *, parent_path: str) -> str:
    title = str(payload.get("title") or "Derivation")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        f"# {title} — Derived form\n\n"
        f"```yaml\nkind: derive\nmode: generic\nparent: {parent_path}\n"
        f"created: {stamp}\n```\n\n"
        f"```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```\n"
    )


def render_derive(payload: dict[str, Any], *, mode: str, parent_path: str) -> str:
    if mode == "english":
        return render_english_derive(payload, parent_path=parent_path)
    if mode == "physics":
        return render_physics_derive(payload, parent_path=parent_path)
    if mode == "finance":
        return render_finance_derive(payload, parent_path=parent_path)
    return render_generic_derive(payload, parent_path=parent_path)
