"""H2c · Matplotlib second scene renderer for AnimationSchema → GIF.

Approved alternative to Manim when Manim is missing/heavy. Does not consume
derive ``manim_beats`` (still DEFER / not_wired_to_expression).
"""

from __future__ import annotations

from pathlib import Path

from app.expression.schema import AnimationSchema

MPL_RENDERER_ID = "mpl_v0"


def mpl_available() -> bool:
    try:
        import matplotlib  # noqa: F401

        return True
    except Exception:
        return False


def render_animation_mpl_gif(schema: AnimationSchema, dest: Path) -> Path:
    """Render ``schema`` with Matplotlib FuncAnimation → GIF at ``dest``.

    Raises on missing matplotlib / empty output.
    """
    if not mpl_available():
        raise RuntimeError("matplotlib not installed")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.animation import FuncAnimation, PillowWriter
    from matplotlib.patches import FancyBboxPatch

    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    for font_path in (
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ):
        if Path(font_path).is_file():
            try:
                font_manager.fontManager.addfont(font_path)
                prop = font_manager.FontProperties(fname=font_path)
                plt.rcParams["font.family"] = prop.get_name()
                plt.rcParams["axes.unicode_minus"] = False
                break
            except Exception:  # noqa: BLE001
                continue

    title = (schema.title or "Animation")[:80]
    states = list(schema.animation.states or [])[:8]
    if not states:
        labels = ["Start", "End"]
        captions = ["", ""]
    else:
        labels = [(s.label or f"S{i + 1}")[:40] for i, s in enumerate(states)]
        captions = [(s.caption or "")[:60] for s in states]

    n = len(labels)
    fig, ax = plt.subplots(figsize=(9.6, 5.4), dpi=100)
    fig.patch.set_facecolor("#121620")
    ax.set_facecolor("#121620")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title(title, color="#f1f5f9", fontsize=14, pad=12)

    boxes: list[FancyBboxPatch] = []
    texts = []
    gap = 0.04
    width = (0.92 - gap * (n - 1)) / max(n, 1)
    y0, h = 0.28, 0.38
    for i, (lab, cap) in enumerate(zip(labels, captions)):
        x = 0.04 + i * (width + gap)
        box = FancyBboxPatch(
            (x, y0),
            width,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.02",
            linewidth=1.5,
            edgecolor="#475569",
            facecolor="#1e293b",
        )
        ax.add_patch(box)
        boxes.append(box)
        t = ax.text(
            x + width / 2,
            y0 + h * 0.62,
            lab,
            ha="center",
            va="center",
            color="#f1f5f9",
            fontsize=11,
            wrap=True,
        )
        c = ax.text(
            x + width / 2,
            y0 + h * 0.28,
            cap,
            ha="center",
            va="center",
            color="#94a3b8",
            fontsize=8,
            wrap=True,
        )
        texts.append((t, c))

    frames = n + 2

    def _update(frame: int) -> list:
        active = min(frame, n - 1) if n else 0
        for i, box in enumerate(boxes):
            if i < active:
                box.set_edgecolor("#22c55e")
                box.set_facecolor("#14532d")
            elif i == active:
                box.set_edgecolor("#38bdf8")
                box.set_facecolor("#0c4a6e")
            else:
                box.set_edgecolor("#475569")
                box.set_facecolor("#1e293b")
        return boxes

    anim = FuncAnimation(fig, _update, frames=frames, interval=450, blit=False)
    writer = PillowWriter(fps=2)
    anim.save(str(dest), writer=writer)
    plt.close(fig)

    if not dest.is_file() or dest.stat().st_size < 32:
        raise RuntimeError(f"mpl gif missing or empty: {dest}")
    return dest
