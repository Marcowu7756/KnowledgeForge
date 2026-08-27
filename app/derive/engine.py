from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.compression.llm import complete_json
from app.compression.parse import extract_json_object
from app.derive.prompt import build_derive_user_prompt, system_for_mode
from app.derive.render import render_derive

DeriveMode = Literal["auto", "english", "physics", "finance", "generic"]

_ENGLISH_HINTS = (
    "english",
    "grammar",
    "clause",
    "relative",
    "attributive",
    "定语",
    "从句",
    "语法",
    "tense",
    "vocabulary",
)
_PHYSICS_HINTS = (
    "physics",
    "force",
    "newton",
    "acceleration",
    "momentum",
    "energy",
    "gravity",
    "物理",
    "力学",
    "牛顿",
    "加速度",
    "动量",
    "能量",
)
_FINANCE_HINTS = (
    "finance",
    "macro",
    "treasury",
    "bond",
    "dollar",
    "usd",
    "fed",
    "bitcoin",
    "gold",
    "金融",
    "美债",
    "美元",
    "国债",
    "黄金",
    "比特币",
    "汇率",
    "央行",
    "储备",
    "全球化",
)


@dataclass
class DeriveResult:
    mode: str
    parent_path: Path
    output_path: Path
    payload: dict


def detect_mode(card_text: str, title: str, tags: list[str] | None = None) -> str:
    hay = " ".join([title, card_text, " ".join(tags or [])]).lower()
    if any(h in hay for h in _ENGLISH_HINTS):
        return "english"
    if any(h in hay for h in _PHYSICS_HINTS):
        return "physics"
    if any(h in hay for h in _FINANCE_HINTS):
        return "finance"
    return "generic"


def _extract_title(card_text: str, fallback: str) -> str:
    match = re.match(r"^# (.+)$", card_text, re.M)
    return match.group(1).strip() if match else fallback


def _extract_tags(card_text: str) -> list[str]:
    match = re.search(r"^tags:\s*(\[.*\])\s*$", card_text, re.M)
    if not match:
        return []
    raw = match.group(1)
    try:
        import json

        data = json.loads(raw)
        return [str(x) for x in data] if isinstance(data, list) else []
    except Exception:  # noqa: BLE001
        return []


def derive_from_card(
    path: str | Path,
    *,
    mode: DeriveMode = "auto",
    dest_dir: Path | None = None,
) -> DeriveResult:
    """Expand an existing Knowledge Unit into examples/process forms."""
    parent = Path(path).expanduser().resolve()
    if not parent.is_file():
        raise FileNotFoundError(f"knowledge card not found: {parent}")

    card_text = parent.read_text(encoding="utf-8")
    title = _extract_title(card_text, parent.stem)
    tags = _extract_tags(card_text)
    resolved_mode = detect_mode(card_text, title, tags) if mode == "auto" else mode

    raw = complete_json(
        system_for_mode(resolved_mode),
        build_derive_user_prompt(mode=resolved_mode, card_text=card_text, title=title),
    )
    payload = extract_json_object(raw)
    payload.setdefault("mode", resolved_mode)
    payload.setdefault("title", title)

    out_dir = dest_dir or (parent.parent / "derived")
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = {
        "english": "examples",
        "physics": "process",
        "finance": "scenarios",
        "generic": "derived",
    }.get(resolved_mode, "derived")
    out_path = out_dir / f"{parent.stem}.{suffix}.md"
    out_path.write_text(
        render_derive(
            payload,
            mode=resolved_mode,
            parent_path=parent.as_posix(),
        ),
        encoding="utf-8",
    )
    return DeriveResult(
        mode=resolved_mode,
        parent_path=parent,
        output_path=out_path,
        payload=payload,
    )
