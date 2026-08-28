"""H2b · Manim golden scene CI/smoke (deterministic schema, soft GIF bounds)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from app.expression.animate_engine import animate_from_card
from app.expression.golden_h2b import (
    GOLDEN_ID,
    GOLDEN_TITLE,
    MAX_GIF_BYTES,
    MIN_GIF_BYTES,
    golden_animation_schema,
)
from app.expression.render_manim import MANIM_RENDERER_ID, manim_available


pytestmark = pytest.mark.skipif(not manim_available(), reason="manim not installed")


def test_h2b_golden_manim_smoke(tmp_path: Path):
    card = tmp_path / "h2b_golden.md"
    card.write_text(
        f"# {GOLDEN_TITLE}\n\n## Key Points\n\n- Observe\n- Evidence\n- Cite\n",
        encoding="utf-8",
    )
    out = tmp_path / "expr"
    schema = golden_animation_schema()
    assert schema.title == GOLDEN_TITLE
    assert len(schema.animation.states) == 3

    result = animate_from_card(
        card,
        dest_dir=out,
        fast=True,
        schema=schema,
        renderer="manim",
    )

    assert result.manim_wired is True
    assert result.renderer == MANIM_RENDERER_ID
    assert result.gif_path.is_file()
    size = result.gif_path.stat().st_size
    assert MIN_GIF_BYTES <= size <= MAX_GIF_BYTES

    manifest = (out / "ANIMATE.md").read_text(encoding="utf-8")
    assert "manim_wired: true" in manifest
    assert "renderer: manim_v0" in manifest
    assert GOLDEN_TITLE in manifest
    assert "Observe" in manifest

    # GIF must be openable; ql scenes are short but multi-frame
    with Image.open(result.gif_path) as im:
        assert im.format == "GIF"
        w, h = im.size
        assert w >= 320 and h >= 180
        frames = 0
        try:
            while True:
                frames += 1
                im.seek(im.tell() + 1)
        except EOFError:
            pass
        assert frames >= 2

    # Schema sidecar frozen for audit
    schema_path = out / "animation.json"
    assert schema_path.is_file()
    assert GOLDEN_TITLE in schema_path.read_text(encoding="utf-8")
    assert GOLDEN_ID  # document constant stays imported/used
