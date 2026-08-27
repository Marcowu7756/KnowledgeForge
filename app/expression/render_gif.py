from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.expression.schema import AnimationSchema

_WIDTH = 960
_HEIGHT = 540
_BG = (18, 22, 32)
_ACTIVE = (56, 189, 248)
_DONE = (34, 197, 94)
_INACTIVE = (71, 85, 105)
_TEXT = (241, 245, 249)
_MUTED = (148, 163, 184)
_ARROW = (251, 191, 36)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _wrap(text: str, font: ImageFont.ImageFont, max_width: int, max_lines: int = 3) -> list[str]:
    if not text:
        return []
    lines: list[str] = []
    for paragraph in text.splitlines():
        if not paragraph.strip():
            continue
        current = ""
        for ch in paragraph:
            trial = current + ch
            box = font.getbbox(trial)
            if box[2] - box[0] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = ch
        if current:
            lines.append(current)
    return lines[:max_lines]


def _state_color(index: int, active: int, revealed: int) -> tuple[int, int, int]:
    if index == active:
        return _ACTIVE
    if index < revealed:
        return _DONE
    return _INACTIVE


def _draw_header(draw: ImageDraw.ImageDraw, title: str) -> None:
    draw.text((_WIDTH // 2, 28), title, fill=_TEXT, font=_font(26), anchor="mt")


def _draw_box(
    draw: ImageDraw.ImageDraw,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    label: str,
    caption: str,
    color: tuple[int, int, int],
    active: bool,
    pulse: float,
) -> None:
    if active:
        glow = int(6 + 5 * pulse)
        draw.rounded_rectangle(
            (x - glow, y - glow, x + w + glow, y + h + glow),
            radius=14,
            outline=_ACTIVE,
            width=2,
        )
    fill = (15, 76, 92) if active else (30, 41, 59)
    draw.rounded_rectangle(
        (x, y, x + w, y + h),
        radius=12,
        fill=fill,
        outline=color,
        width=3 if active else 1,
    )
    label_font = _font(20)
    cap_font = _font(15)
    for i, line in enumerate(_wrap(label, label_font, w - 16, 2)):
        draw.text((x + w // 2, y + 16 + i * 24), line, fill=_TEXT, font=label_font, anchor="mt")
    if active and caption:
        cy = y + h + 8
        for line in _wrap(caption, cap_font, w + 60, 2):
            draw.text((x + w // 2, cy), line, fill=_MUTED, font=cap_font, anchor="mt")
            cy += 18


def _draw_arrow_h(
    draw: ImageDraw.ImageDraw,
    x1: int,
    y: int,
    x2: int,
    *,
    progress: float = 1.0,
    label: str = "",
) -> None:
    if x2 <= x1:
        return
    end_x = int(x1 + (x2 - x1) * max(0.0, min(1.0, progress)))
    draw.line((x1, y, end_x, y), fill=_ARROW, width=3)
    if progress >= 0.95:
        draw.polygon(
            [(x2 - 8, y), (x2 - 18, y - 6), (x2 - 18, y + 6)],
            fill=_ARROW,
        )
    if label and progress > 0.5:
        draw.text(((x1 + x2) // 2, y - 14), label, fill=_ARROW, font=_font(14), anchor="ms")


def _draw_arrow_v(
    draw: ImageDraw.ImageDraw,
    x: int,
    y1: int,
    y2: int,
    *,
    progress: float = 1.0,
    label: str = "",
) -> None:
    end_y = int(y1 + (y2 - y1) * max(0.0, min(1.0, progress)))
    draw.line((x, y1, x, end_y), fill=_ARROW, width=3)
    if progress >= 0.95:
        draw.polygon(
            [(x, y2 - 8), (x - 6, y2 - 18), (x + 6, y2 - 18)],
            fill=_ARROW,
        )
    if label and progress > 0.5:
        draw.text((x + 14, (y1 + y2) // 2), label, fill=_ARROW, font=_font(14), anchor="lm")


def _draw_horizontal(
    schema: AnimationSchema,
    *,
    active: int,
    revealed: int,
    pulse: float,
    edge_progress: float,
) -> Image.Image:
    img = Image.new("RGB", (_WIDTH, _HEIGHT), _BG)
    draw = ImageDraw.Draw(img)
    _draw_header(draw, schema.title)

    states = schema.animation.states
    n = len(states)
    gap = 36
    box_w = min(180, (_WIDTH - gap * (n + 1)) // max(n, 1))
    box_h = 100
    total_w = n * box_w + (n - 1) * gap
    start_x = (_WIDTH - total_w) // 2
    y = 200
    boxes: list[tuple[int, int, int, int]] = []

    for i, state in enumerate(states):
        x = start_x + i * (box_w + gap)
        color = _state_color(i, active, revealed)
        _draw_box(
            draw,
            x=x,
            y=y,
            w=box_w,
            h=box_h,
            label=state.label,
            caption=state.caption,
            color=color,
            active=(i == active),
            pulse=pulse,
        )
        boxes.append((x, y, box_w, box_h))

    transitions = {t.to_index: t for t in schema.animation.transitions}
    for i in range(n - 1):
        x1 = boxes[i][0] + boxes[i][2]
        x2 = boxes[i + 1][0]
        prog = 1.0
        if i + 1 == active and i + 1 == revealed:
            prog = edge_progress
        elif i + 1 <= revealed:
            prog = 1.0
        elif i + 1 > revealed:
            prog = 0.0
        tr = transitions.get(i + 1)
        lbl = tr.label if tr else ""
        _draw_arrow_h(draw, x1 + 8, y + box_h // 2, x2 - 8, progress=prog, label=lbl if i + 1 == active else "")

    draw.text((_WIDTH - 20, _HEIGHT - 18), f"{active + 1}/{n}", fill=_MUTED, font=_font(14), anchor="rb")
    return img


def _draw_vertical(
    schema: AnimationSchema,
    *,
    active: int,
    revealed: int,
    pulse: float,
    edge_progress: float,
) -> Image.Image:
    img = Image.new("RGB", (_WIDTH, _HEIGHT), _BG)
    draw = ImageDraw.Draw(img)
    _draw_header(draw, schema.title)

    states = schema.animation.states
    n = len(states)
    box_w = 420
    box_h = 72
    gap = 28
    total_h = n * box_h + (n - 1) * gap
    start_y = max(90, (_HEIGHT - total_h) // 2 + 20)
    x = (_WIDTH - box_w) // 2
    boxes: list[tuple[int, int, int, int]] = []

    for i, state in enumerate(states):
        y = start_y + i * (box_h + gap)
        color = _state_color(i, active, revealed)
        _draw_box(
            draw,
            x=x,
            y=y,
            w=box_w,
            h=box_h,
            label=state.label,
            caption=state.caption if i == active else "",
            color=color,
            active=(i == active),
            pulse=pulse,
        )
        boxes.append((x, y, box_w, box_h))

    transitions = {t.to_index: t for t in schema.animation.transitions}
    cx = x + box_w // 2
    for i in range(n - 1):
        y1 = boxes[i][1] + boxes[i][3]
        y2 = boxes[i + 1][1]
        prog = 1.0
        if i + 1 == active and i + 1 == revealed:
            prog = edge_progress
        elif i + 1 <= revealed:
            prog = 1.0
        elif i + 1 > revealed:
            prog = 0.0
        tr = transitions.get(i + 1)
        lbl = tr.label if tr else ""
        _draw_arrow_v(draw, cx, y1 + 6, y2 - 6, progress=prog, label=lbl if i + 1 == active else "")

    draw.text((_WIDTH - 20, _HEIGHT - 18), f"{active + 1}/{n}", fill=_MUTED, font=_font(14), anchor="rb")
    return img


def _draw_graph(
    schema: AnimationSchema,
    *,
    active: int,
    revealed: int,
    pulse: float,
    edge_progress: float,
) -> Image.Image:
    img = Image.new("RGB", (_WIDTH, _HEIGHT), _BG)
    draw = ImageDraw.Draw(img)
    _draw_header(draw, schema.title)

    states = schema.animation.states
    n = len(states)
    cx, cy = _WIDTH // 2, _HEIGHT // 2 + 20
    radius = min(180, 60 + n * 18)
    positions: list[tuple[int, int]] = []
    for i in range(n):
        import math

        angle = -math.pi / 2 + (2 * math.pi * i / n)
        positions.append((int(cx + radius * math.cos(angle)), int(cy + radius * math.sin(angle))))

    node_r = 36
    for i, (px, py) in enumerate(positions):
        color = _state_color(i, active, revealed)
        r = node_r + (4 if i == active else 0)
        if i == active:
            glow = int(4 + 4 * pulse)
            draw.ellipse(
                (px - r - glow, py - r - glow, px + r + glow, py + r + glow),
                outline=_ACTIVE,
                width=2,
            )
        fill = (15, 76, 92) if i == active else (30, 41, 59)
        draw.ellipse((px - r, py - r, px + r, py + r), fill=fill, outline=color, width=3 if i == active else 1)
        label = _wrap(states[i].label, _font(13), 64, 2)
        ty = py - 8
        for line in label[:2]:
            draw.text((px, ty), line, fill=_TEXT, font=_font(13), anchor="mm")
            ty += 15

    for i in range(n):
        j = (i + 1) % n if n > 2 else i + 1
        if j >= n:
            continue
        if j > revealed:
            continue
        x1, y1 = positions[i]
        x2, y2 = positions[j]
        prog = edge_progress if j == active else 1.0
        mx = int(x1 + (x2 - x1) * prog)
        my = int(y1 + (y2 - y1) * prog)
        draw.line((x1, y1, mx, my), fill=_ARROW, width=2)

    if states[active].caption:
        cap = _wrap(states[active].caption, _font(16), _WIDTH - 80, 2)
        ty = _HEIGHT - 70
        for line in cap:
            draw.text((_WIDTH // 2, ty), line, fill=_MUTED, font=_font(16), anchor="mt")
            ty += 20

    draw.text((_WIDTH - 20, _HEIGHT - 18), f"{active + 1}/{n}", fill=_MUTED, font=_font(14), anchor="rb")
    return img


def _draw_frame(
    schema: AnimationSchema,
    *,
    active: int,
    revealed: int,
    pulse: float,
    edge_progress: float,
) -> Image.Image:
    kind = schema.animation.type
    if kind == "mechanism":
        return _draw_vertical(schema, active=active, revealed=revealed, pulse=pulse, edge_progress=edge_progress)
    if kind == "graph":
        return _draw_graph(schema, active=active, revealed=revealed, pulse=pulse, edge_progress=edge_progress)
    return _draw_horizontal(schema, active=active, revealed=revealed, pulse=pulse, edge_progress=edge_progress)


def render_animation_gif(schema: AnimationSchema, dest: Path, *, fps: int = 6) -> Path:
    """Render animation GIF with step hold + animated transitions."""
    frames: list[Image.Image] = []
    hold = max(3, fps // 2)
    trans = max(4, fps)
    n = len(schema.animation.states)

    for step in range(n):
        for p in range(hold):
            pulse = p / hold
            frames.append(
                _draw_frame(
                    schema,
                    active=step,
                    revealed=step,
                    pulse=pulse,
                    edge_progress=1.0,
                )
            )
        if step < n - 1:
            for p in range(trans):
                prog = (p + 1) / trans
                frames.append(
                    _draw_frame(
                        schema,
                        active=step + 1,
                        revealed=step + 1,
                        pulse=prog,
                        edge_progress=prog,
                    )
                )

    dest.parent.mkdir(parents=True, exist_ok=True)
    duration_ms = int(1000 / fps)
    frames[0].save(
        dest,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )
    return dest


# Back-compat alias used by express
def render_state_gif(schema: AnimationSchema, dest: Path, *, fps: int = 6) -> Path:
    return render_animation_gif(schema, dest, fps=fps)
