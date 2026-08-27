from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app import config
from app.expression.derive import (
    derive_audio_from_ko,
    derive_visual_from_ko,
    visual_to_animation_schema,
)
from app.expression.objects import AudioExpression, VisualExpression
from app.expression.render_gif import render_animation_gif
from app.expression.render_tts import TtsError, render_narration_wav
from app.knowledge.object import KnowledgeObject


@dataclass
class VisualRenderResult:
    expression: VisualExpression
    expression_path: Path
    gif_path: Path


@dataclass
class AudioRenderResult:
    expression: AudioExpression
    expression_path: Path
    wav_path: Path | None


def write_visual_expression(expr: VisualExpression, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(expr.model_dump_json(indent=2, by_alias=True) + "\n", encoding="utf-8")
    return dest


def write_audio_expression(expr: AudioExpression, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(expr.model_dump_json(indent=2, by_alias=True) + "\n", encoding="utf-8")
    return dest


def animate_from_ko(
    obj: KnowledgeObject,
    *,
    dest_dir: Path,
    expression: VisualExpression | None = None,
) -> VisualRenderResult:
    """P1-A: KnowledgeObject → VisualExpression → GIF."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    expr = expression or derive_visual_from_ko(obj)
    schema = visual_to_animation_schema(expr)
    gif_path = render_animation_gif(schema, dest_dir / "animation.gif")
    expr.artifact = "animation.gif"
    expr_path = write_visual_expression(expr, dest_dir / "visual_expression.json")
    return VisualRenderResult(expression=expr, expression_path=expr_path, gif_path=gif_path)


def narrate_from_ko(
    obj: KnowledgeObject,
    *,
    dest_dir: Path,
    voice_name: str | None = None,
    expression: AudioExpression | None = None,
) -> AudioRenderResult:
    """P1-B: KnowledgeObject → AudioExpression → WAV."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    expr = expression or derive_audio_from_ko(obj, voice=voice_name)
    if voice_name:
        expr.voice = voice_name
    expr_path = write_audio_expression(expr, dest_dir / "audio_expression.json")
    wav_path: Path | None = None
    try:
        wav_path = render_narration_wav(
            expr.script,
            dest_dir / "narration.wav",
            voice_hint="zh" if expr.language.startswith("zh") else "en",
            voice_name=voice_name or expr.voice or None,
        )
        expr.artifact = "narration.wav"
        expr.evidence.voice_model = config.TTS_ENGINE or expr.evidence.voice_model
        write_audio_expression(expr, expr_path)
    except TtsError:
        wav_path = None
    return AudioRenderResult(expression=expr, expression_path=expr_path, wav_path=wav_path)
