from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

ArtifactKind = Literal[
    "source",
    "transcript",
    "knowledge_md",
    "knowledge_json",
    "knowledge_object",
    "visual_expression",
    "audio_expression",
    "animation_schema",
    "animation_gif",
    "narration_wav",
    "express_schema",
    "manifest",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Artifact(BaseModel):
    """One validated output produced by a harness step."""

    kind: ArtifactKind
    path: str
    checksum: str = ""
    bytes: int = 0
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    meta: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_path(
        cls,
        kind: ArtifactKind,
        path: Path,
        *,
        meta: dict[str, Any] | None = None,
    ) -> Artifact:
        path = path.resolve()
        if not path.is_file():
            raise FileNotFoundError(f"artifact missing: {path}")
        return cls(
            kind=kind,
            path=path.as_posix(),
            checksum=sha256_file(path),
            bytes=path.stat().st_size,
            meta=meta or {},
        )


def write_json(path: Path, payload: dict[str, Any] | list[Any] | BaseModel) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, BaseModel):
        text = payload.model_dump_json(indent=2)
    else:
        text = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    path.write_text(text + "\n", encoding="utf-8")
    return path


def copy_into(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest
