from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app import config
from app.expression.compile import compile_expression, load_card
from app.expression.render_gif import render_state_gif
from app.expression.render_tts import TtsError, render_narration_wav
from app.expression.schema import ExpressionSchema


@dataclass
class ExpressResult:
    parent_path: Path
    output_dir: Path
    schema_path: Path
    gif_path: Path | None
    audio_path: Path | None
    manifest_path: Path
    schema: ExpressionSchema


def _write_manifest(
    *,
    dest: Path,
    parent: Path,
    schema: ExpressionSchema,
    gif: Path | None,
    audio: Path | None,
) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"# {schema.title} — Expression",
        "",
        "```yaml",
        f"kind: expression",
        f"parent: {parent.as_posix()}",
        f"created: {stamp}",
        f"animation: {gif.as_posix() if gif else ''}",
        f"narration: {audio.as_posix() if audio else ''}",
        "```",
        "",
        "## Narration script",
        "",
        schema.narration.script,
        "",
        "## Animation states",
        "",
    ]
    for i, state in enumerate(schema.animation.states, start=1):
        lines.append(f"{i}. **{state.label}** — {state.caption}")
    manifest = dest / "EXPRESS.md"
    manifest.write_text("\n".join(lines), encoding="utf-8")
    return manifest


def express_from_card(
    path: str | Path,
    *,
    dest_dir: Path | None = None,
    animation: bool = True,
    narration: bool = True,
    voice_name: str | None = None,
    schema: ExpressionSchema | None = None,
) -> ExpressResult:
    """Layer 3: compile KU → animation GIF + local TTS narration."""
    parent = Path(path).expanduser().resolve()
    card_text, title = load_card(parent)

    compiled = schema or compile_expression(card_text, title=title)
    out_dir = dest_dir or (config.EXPRESSION_DIR / parent.stem)
    out_dir.mkdir(parents=True, exist_ok=True)

    schema_path = out_dir / "schema.json"
    schema_path.write_text(
        compiled.model_dump_json(indent=2, by_alias=True),
        encoding="utf-8",
    )

    gif_path: Path | None = None
    if animation:
        gif_path = render_state_gif(compiled, out_dir / "animation.gif")

    audio_path: Path | None = None
    if narration:
        try:
            audio_path = render_narration_wav(
                compiled.narration.script,
                out_dir / "narration.wav",
                voice_hint=compiled.narration.voice_hint,
                voice_name=voice_name,
            )
        except TtsError:
            # Narration script still saved in manifest; audio optional.
            audio_path = None

    manifest_path = _write_manifest(
        dest=out_dir,
        parent=parent,
        schema=compiled,
        gif=gif_path,
        audio=audio_path,
    )

    return ExpressResult(
        parent_path=parent,
        output_dir=out_dir,
        schema_path=schema_path,
        gif_path=gif_path,
        audio_path=audio_path,
        manifest_path=manifest_path,
        schema=compiled,
    )
