from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app import config
from app.expression.compile import compile_animation, load_card
from app.expression.ku_parse import compile_animation_fast
from app.expression.objects import DEFAULT_RENDERER
from app.expression.render_gif import render_animation_gif
from app.expression.render_manim import (
    MANIM_RENDERER_ID,
    manim_available,
    preferred_animate_renderer,
    render_animation_manim_gif,
)
from app.expression.render_mpl import (
    MPL_RENDERER_ID,
    mpl_available,
    render_animation_mpl_gif,
)
from app.expression.schema import AnimationSchema


@dataclass
class AnimateResult:
    parent_path: Path
    output_dir: Path
    schema_path: Path
    gif_path: Path
    schema: AnimationSchema
    source: str  # llm | fast | provided
    renderer: str = DEFAULT_RENDERER
    manim_wired: bool = False
    mpl_wired: bool = False
    fallback_reason: str = ""


def _compile_animation_llm(card_text: str, *, title: str) -> AnimationSchema:
    return compile_animation(card_text, title=title)


def _try_manim(schema: AnimationSchema, dest: Path) -> Path:
    if not manim_available():
        raise RuntimeError("manim not installed")
    return render_animation_manim_gif(schema, dest)


def _try_mpl(schema: AnimationSchema, dest: Path) -> Path:
    if not mpl_available():
        raise RuntimeError("matplotlib not installed")
    return render_animation_mpl_gif(schema, dest)


def _render_gif(
    schema: AnimationSchema,
    dest: Path,
    *,
    prefer: str | None = None,
) -> tuple[Path, str, bool, bool, str]:
    """Return (gif_path, renderer_id, manim_wired, mpl_wired, fallback_reason)."""
    mode = (prefer or preferred_animate_renderer()).strip().lower()
    if mode == "matplotlib":
        mode = "mpl"

    if mode == "pillow":
        return (
            render_animation_gif(schema, dest),
            DEFAULT_RENDERER,
            False,
            False,
            "forced_pillow",
        )

    if mode == "manim":
        path = _try_manim(schema, dest)
        return path, MANIM_RENDERER_ID, True, False, ""

    if mode == "mpl":
        path = _try_mpl(schema, dest)
        return path, MPL_RENDERER_ID, False, True, ""

    # auto: manim → mpl → pillow
    reasons: list[str] = []
    if manim_available():
        try:
            path = render_animation_manim_gif(schema, dest)
            return path, MANIM_RENDERER_ID, True, False, ""
        except Exception as exc:  # noqa: BLE001
            reasons.append(f"manim_failed:{exc}")
    else:
        reasons.append("manim_unavailable")

    if mpl_available():
        try:
            path = render_animation_mpl_gif(schema, dest)
            reason = ";".join(reasons) if reasons else ""
            return path, MPL_RENDERER_ID, False, True, reason
        except Exception as exc:  # noqa: BLE001
            reasons.append(f"mpl_failed:{exc}")
    else:
        reasons.append("mpl_unavailable")

    path = render_animation_gif(schema, dest)
    return path, DEFAULT_RENDERER, False, False, ";".join(reasons)


def animate_from_card(
    path: str | Path,
    *,
    dest_dir: Path | None = None,
    fast: bool = False,
    schema: AnimationSchema | None = None,
    renderer: str | None = None,
) -> AnimateResult:
    """Layer 3: Knowledge Unit → animation GIF only (no TTS).

    H2a/H2c: prefers Manim, then Matplotlib (``mpl_v0``), else Pillow.
    Derive ``manim_beats`` remain not_wired_to_expression.
    """
    parent = Path(path).expanduser().resolve()
    card_text, title = load_card(parent)

    source = "provided"
    if schema is None:
        if fast:
            schema = compile_animation_fast(card_text, title=title)
            if schema is not None:
                source = "fast"
        if schema is None:
            schema = _compile_animation_llm(card_text, title=title)
            source = "llm"

    out_dir = dest_dir or (config.EXPRESSION_DIR / parent.stem)
    out_dir.mkdir(parents=True, exist_ok=True)

    schema_path = out_dir / "animation.json"
    schema_path.write_text(schema.model_dump_json(indent=2, by_alias=True), encoding="utf-8")

    gif_path, renderer_id, manim_wired, mpl_wired, fallback_reason = _render_gif(
        schema,
        out_dir / "animation.gif",
        prefer=renderer,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest = out_dir / "ANIMATE.md"
    lines = [
        f"# {schema.title} — Animation",
        "",
        "```yaml",
        "kind: animation",
        f"parent: {parent.as_posix()}",
        f"created: {stamp}",
        f"source: {source}",
        f"type: {schema.animation.type}",
        f"renderer: {renderer_id}",
        f"manim_wired: {str(manim_wired).lower()}",
        f"mpl_wired: {str(mpl_wired).lower()}",
        f"gif: {gif_path.as_posix()}",
    ]
    if fallback_reason:
        lines.append(f"fallback_reason: {fallback_reason}")
    lines += [
        "```",
        "",
        "## States",
        "",
    ]
    for i, state in enumerate(schema.animation.states, start=1):
        lines.append(f"{i}. **{state.label}** — {state.caption}")
    if manim_wired:
        lines += [
            "",
            "## H2a",
            "",
            "- Manim Community renderer active (`manim_v0`).",
            "- Derive `manim_beats` remain `not_wired_to_expression` (storyboard only).",
            "",
        ]
    if mpl_wired:
        lines += [
            "",
            "## H2c",
            "",
            "- Matplotlib second renderer active (`mpl_v0`).",
            "- Derive `manim_beats` remain `not_wired_to_expression` (storyboard only).",
            "",
        ]
    manifest.write_text("\n".join(lines), encoding="utf-8")

    return AnimateResult(
        parent_path=parent,
        output_dir=out_dir,
        schema_path=schema_path,
        gif_path=gif_path,
        schema=schema,
        source=source,
        renderer=renderer_id,
        manim_wired=manim_wired,
        mpl_wired=mpl_wired,
        fallback_reason=fallback_reason,
    )
