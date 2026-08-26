from __future__ import annotations

import re


_WS = re.compile(r"[ \t]+")
_BLANK = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    """Normalize whitespace. Keep content; do not summarize."""
    lines = [line.strip() for line in text.replace("\r\n", "\n").split("\n")]
    joined = "\n".join(_WS.sub(" ", line) for line in lines)
    return _BLANK.sub("\n\n", joined).strip()
