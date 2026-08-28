"""H2a · Manim renderer behind animate (with Pillow fallback)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from app.expression.animate_engine import animate_from_card
from app.expression.render_manim import (
    MANIM_RENDERER_ID,
    manim_available,
    preferred_animate_renderer,
)
from app.expression.schema import AnimationSchema, AnimationSpec, AnimationState


def _tiny_schema() -> AnimationSchema:
    return AnimationSchema(
        title="H2a Demo",
        animation=AnimationSpec(
            type="state_transition",
            states=[
                AnimationState(label="A", caption="start"),
                AnimationState(label="B", caption="end"),
            ],
            transitions=[],
        ),
    )


def test_preferred_renderer_env(monkeypatch):
    monkeypatch.setenv("KF_ANIMATE_RENDERER", "pillow")
    assert preferred_animate_renderer() == "pillow"
    monkeypatch.setenv("KF_ANIMATE_RENDERER", "manim")
    assert preferred_animate_renderer() == "manim"


def test_animate_forced_pillow(tmp_path: Path):
    card = tmp_path / "card.md"
    card.write_text(
        "# Demo\n\n## Key Points\n\n- One\n- Two\n",
        encoding="utf-8",
    )
    out = tmp_path / "expr"
    result = animate_from_card(
        card,
        dest_dir=out,
        fast=True,
        schema=_tiny_schema(),
        renderer="pillow",
    )
    assert result.gif_path.is_file()
    assert result.renderer == "pillow_v1"
    assert result.manim_wired is False
    text = (out / "ANIMATE.md").read_text(encoding="utf-8")
    assert "manim_wired: false" in text
    assert "renderer: pillow_v1" in text


def test_animate_manim_failure_falls_back_in_auto(tmp_path: Path):
    card = tmp_path / "card.md"
    card.write_text("# Demo\n\n## Key Points\n\n- One\n", encoding="utf-8")
    out = tmp_path / "expr"
    with (
        patch("app.expression.animate_engine.manim_available", return_value=True),
        patch(
            "app.expression.animate_engine.render_animation_manim_gif",
            side_effect=RuntimeError("boom"),
        ),
        patch("app.expression.animate_engine.mpl_available", return_value=False),
    ):
        result = animate_from_card(
            card,
            dest_dir=out,
            fast=True,
            schema=_tiny_schema(),
            renderer="auto",
        )
    assert result.manim_wired is False
    assert result.mpl_wired is False
    assert result.renderer == "pillow_v1"
    assert "manim_failed" in result.fallback_reason


@pytest.mark.skipif(not manim_available(), reason="manim not installed")
def test_animate_manim_wired_when_forced(tmp_path: Path):
    card = tmp_path / "card.md"
    card.write_text("# Demo\n\n## Key Points\n\n- One\n- Two\n", encoding="utf-8")
    out = tmp_path / "expr"
    result = animate_from_card(
        card,
        dest_dir=out,
        fast=True,
        schema=_tiny_schema(),
        renderer="manim",
    )
    assert result.manim_wired is True
    assert result.renderer == MANIM_RENDERER_ID
    assert result.gif_path.is_file()
    assert result.gif_path.stat().st_size > 100
    text = (out / "ANIMATE.md").read_text(encoding="utf-8")
    assert "manim_wired: true" in text
    assert "manim_v0" in text
