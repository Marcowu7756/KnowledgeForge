"""H2a · optional Manim Community renderer for AnimationSchema → GIF.

Falls back to callers when Manim is missing or render fails.
Does not consume derive ``manim_beats`` (still DEFER / not_wired_to_expression).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from app.expression.schema import AnimationSchema

MANIM_RENDERER_ID = "manim_v0"
SCENE_CLASS = "KFStateChain"


def manim_available() -> bool:
    try:
        import manim  # noqa: F401

        return True
    except Exception:
        return False


def preferred_animate_renderer() -> str:
    """auto | manim | mpl | pillow — from KF_ANIMATE_RENDERER (default auto)."""
    raw = (os.environ.get("KF_ANIMATE_RENDERER") or "auto").strip().lower()
    if raw in {"auto", "manim", "mpl", "matplotlib", "pillow"}:
        return "mpl" if raw == "matplotlib" else raw
    return "auto"


def _scene_source(schema: AnimationSchema) -> str:
    title = schema.title or "Animation"
    states = list(schema.animation.states or [])
    if not states:
        states_payload = [("Start", ""), ("End", "")]
    else:
        states_payload = [
            (s.label or f"S{i + 1}", s.caption or "") for i, s in enumerate(states[:8])
        ]

    lines = [
        "from manim import *",
        "",
        f"STATES = {states_payload!r}",
        f"TITLE = {title!r}",
        "",
        f"class {SCENE_CLASS}(Scene):",
        "    def construct(self):",
        "        fonts = ('Microsoft YaHei', 'SimHei', 'Arial', 'DejaVu Sans')",
        "        def T(text, size=28):",
        "            last = None",
        "            for font in fonts:",
        "                try:",
        "                    return Text(str(text)[:80], font=font, font_size=size)",
        "                except Exception as exc:  # noqa: BLE001",
        "                    last = exc",
        "            return Text(str(text)[:80], font_size=size)",
        "        title = T(TITLE, 34)",
        "        title.to_edge(UP)",
        "        self.play(FadeIn(title))",
        "        boxes = VGroup()",
        "        for label, caption in STATES:",
        "            head = T(label, 22)",
        "            body = T(caption, 16) if caption else T(' ', 16)",
        "            body.set_opacity(0.85)",
        "            group = VGroup(head, body).arrange(DOWN, buff=0.12)",
        "            box = SurroundingRectangle(group, buff=0.22, color=BLUE_B, corner_radius=0.12)",
        "            cell = VGroup(box, group)",
        "            boxes.add(cell)",
        "        boxes.arrange(RIGHT, buff=0.35)",
        "        if boxes.width > 12:",
        "            boxes.scale_to_fit_width(12)",
        "        boxes.next_to(title, DOWN, buff=0.7)",
        "        for cell in boxes:",
        "            self.play(FadeIn(cell), run_time=0.45)",
        "            self.wait(0.15)",
        "        self.wait(0.4)",
        "",
    ]
    return "\n".join(lines)


def render_animation_manim_gif(schema: AnimationSchema, dest: Path) -> Path:
    """Render ``schema`` with Manim Community → GIF at ``dest``.

    Raises on missing Manim / non-zero CLI / missing output.
    """
    if not manim_available():
        raise RuntimeError("manim not installed")

    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="kf_manim_") as tmp:
        tmp_path = Path(tmp)
        script = tmp_path / "kf_scene.py"
        script.write_text(_scene_source(schema), encoding="utf-8")
        media_dir = tmp_path / "media"
        cmd = [
            sys.executable,
            "-m",
            "manim",
            "render",
            str(script),
            SCENE_CLASS,
            "-ql",
            "--format",
            "gif",
            "--media_dir",
            str(media_dir),
            "-o",
            "animation",
            "--disable_caching",
            "-v",
            "WARNING",
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(tmp_path),
            check=False,
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip()
            raise RuntimeError(f"manim render failed ({proc.returncode}): {err[-1200:]}")

        gifs = sorted(media_dir.rglob("*.gif"))
        if not gifs:
            # Some builds write mp4 only — convert via Pillow if present
            mp4s = sorted(media_dir.rglob("*.mp4"))
            if not mp4s:
                raise RuntimeError("manim produced no gif/mp4 under media_dir")
            raise RuntimeError(
                f"manim produced mp4 but no gif (unexpected with --format gif): {mp4s[0]}"
            )
        shutil.copy2(gifs[-1], dest)

    if not dest.is_file() or dest.stat().st_size < 32:
        raise RuntimeError(f"manim gif missing or empty: {dest}")
    return dest
