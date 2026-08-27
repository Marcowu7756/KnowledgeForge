from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app import config
from app.expression.compile import compile_animation, load_card
from app.expression.ku_parse import compile_animation_fast
from app.expression.render_gif import render_animation_gif
from app.expression.schema import AnimationSchema


@dataclass
class AnimateResult:
    parent_path: Path
    output_dir: Path
    schema_path: Path
    gif_path: Path
    schema: AnimationSchema
    source: str  # llm | fast


def _compile_animation_llm(card_text: str, *, title: str) -> AnimationSchema:
    return compile_animation(card_text, title=title)


def animate_from_card(
    path: str | Path,
    *,
    dest_dir: Path | None = None,
    fast: bool = False,
    schema: AnimationSchema | None = None,
) -> AnimateResult:
    """Layer 3: Knowledge Unit → animation GIF only (no TTS)."""
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

    gif_path = render_animation_gif(schema, out_dir / "animation.gif")

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
        f"gif: {gif_path.as_posix()}",
        "```",
        "",
        "## States",
        "",
    ]
    for i, state in enumerate(schema.animation.states, start=1):
        lines.append(f"{i}. **{state.label}** — {state.caption}")
    manifest.write_text("\n".join(lines), encoding="utf-8")

    return AnimateResult(
        parent_path=parent,
        output_dir=out_dir,
        schema_path=schema_path,
        gif_path=gif_path,
        schema=schema,
        source=source,
    )
