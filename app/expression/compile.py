from __future__ import annotations

from pathlib import Path

from app.compression.llm import complete_json
from app.compression.parse import extract_json_object
from app.expression.prompt import ANIMATE_SYSTEM, EXPRESS_SYSTEM
from app.expression.schema import AnimationSchema, ExpressionSchema, animation_from_payload, schema_from_payload


def build_express_user_prompt(*, card_text: str, title: str) -> str:
    return (
        f"Title: {title}\n\n"
        "Knowledge Unit:\n"
        f"{card_text[:10000]}\n\n"
        "Compile expression schema for animation + narration."
    )


def compile_expression(card_text: str, *, title: str) -> ExpressionSchema:
    raw = complete_json(
        EXPRESS_SYSTEM,
        build_express_user_prompt(card_text=card_text, title=title),
    )
    payload = extract_json_object(raw)
    payload.setdefault("title", title)
    return schema_from_payload(payload)


def compile_animation(card_text: str, *, title: str) -> AnimationSchema:
    raw = complete_json(
        ANIMATE_SYSTEM,
        build_animate_user_prompt(card_text=card_text, title=title),
    )
    payload = extract_json_object(raw)
    payload.setdefault("title", title)
    return animation_from_payload(payload)


def build_animate_user_prompt(*, card_text: str, title: str) -> str:
    return (
        f"Title: {title}\n\n"
        "Knowledge Unit:\n"
        f"{card_text[:10000]}\n\n"
        "Compile animation schema only."
    )


def load_card(path: str | Path) -> tuple[str, str]:
    card_path = Path(path).expanduser().resolve()
    if not card_path.is_file():
        raise FileNotFoundError(f"knowledge card not found: {card_path}")
    text = card_path.read_text(encoding="utf-8")
    import re

    match = re.match(r"^# (.+)$", text, re.M)
    title = match.group(1).strip() if match else card_path.stem
    return text, title
