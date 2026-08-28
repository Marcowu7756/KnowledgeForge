"""H2c · Matplotlib second renderer for animate."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from app.expression.animate_engine import animate_from_card
from app.expression.render_manim import preferred_animate_renderer
from app.expression.render_mpl import MPL_RENDERER_ID, mpl_available
from app.expression.schema import AnimationSchema, AnimationSpec, AnimationState


def _tiny_schema() -> AnimationSchema:
    return AnimationSchema(
        title="H2c Demo",
        animation=AnimationSpec(
            type="state_transition",
            states=[
                AnimationState(label="Observe", caption="state"),
                AnimationState(label="Evidence", caption="proof"),
                AnimationState(label="Cite", caption="KO"),
            ],
            transitions=[],
        ),
    )


def test_preferred_renderer_accepts_mpl(monkeypatch):
    monkeypatch.setenv("KF_ANIMATE_RENDERER", "mpl")
    assert preferred_animate_renderer() == "mpl"
    monkeypatch.setenv("KF_ANIMATE_RENDERER", "matplotlib")
    assert preferred_animate_renderer() == "mpl"


@pytest.mark.skipif(not mpl_available(), reason="matplotlib not installed")
def test_animate_forced_mpl(tmp_path: Path):
    card = tmp_path / "card.md"
    card.write_text("# Demo\n\n## Key Points\n\n- One\n- Two\n", encoding="utf-8")
    out = tmp_path / "expr"
    result = animate_from_card(
        card,
        dest_dir=out,
        fast=True,
        schema=_tiny_schema(),
        renderer="mpl",
    )
    assert result.mpl_wired is True
    assert result.manim_wired is False
    assert result.renderer == MPL_RENDERER_ID
    assert result.gif_path.is_file()
    assert result.gif_path.stat().st_size > 100
    text = (out / "ANIMATE.md").read_text(encoding="utf-8")
    assert "mpl_wired: true" in text
    assert "H2c" in text


def test_auto_falls_to_mpl_when_manim_missing(tmp_path: Path):
    card = tmp_path / "card.md"
    card.write_text("# Demo\n\n## Key Points\n\n- One\n", encoding="utf-8")
    out = tmp_path / "expr"

    def _fake_mpl(schema, dest):
        p = Path(dest)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"GIF89a" + b"\x00" * 200)
        return p

    with (
        patch("app.expression.animate_engine.manim_available", return_value=False),
        patch("app.expression.animate_engine.mpl_available", return_value=True),
        patch(
            "app.expression.animate_engine.render_animation_mpl_gif",
            side_effect=_fake_mpl,
        ),
    ):
        result = animate_from_card(
            card,
            dest_dir=out,
            fast=True,
            schema=_tiny_schema(),
            renderer="auto",
        )
    assert result.renderer == MPL_RENDERER_ID
    assert result.mpl_wired is True
    assert result.manim_wired is False
    assert "manim_unavailable" in result.fallback_reason
