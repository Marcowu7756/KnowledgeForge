from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.harness.artifact import Artifact, write_json
from app.harness.evidence import HARNESS_VERSION
from app.harness.task import TaskRun
from app.knowledge.object import KnowledgeObject, ModelVersions


class PackageManifest(BaseModel):
    """Source of truth for a knowledge package."""

    kind: str = "knowledge_package"
    schema_version: str = "0.1"
    id: str
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "ok"
    source: str = ""
    package_dir: str = ""
    pipeline: str = HARNESS_VERSION
    options: dict[str, Any] = Field(default_factory=dict)
    models: ModelVersions = Field(default_factory=ModelVersions)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    knowledge_object: str = "knowledge_object.json"
    knowledge_md: str = "knowledge.md"
    expressions: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None

    def touch(self) -> None:
        self.updated = datetime.now(timezone.utc)


def load_manifest(package_dir: Path) -> PackageManifest:
    path = package_dir / "manifest.json"
    if not path.is_file():
        raise FileNotFoundError(f"manifest missing: {path}")
    return PackageManifest.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _expression_evidence(artifacts: list[Artifact], obj: KnowledgeObject | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for art in artifacts:
        if art.kind == "visual_expression":
            out["visual"] = {
                "derived_from": (obj.id if obj else art.meta.get("source_ko", "")),
                "expression_version": art.meta.get("expression_version", "v0.1"),
                "renderer": art.meta.get("renderer", "pillow_v1"),
                "artifact": art.path,
                **{k: v for k, v in art.meta.items() if k not in {"expression_version", "renderer"}},
            }
        elif art.kind == "audio_expression":
            out["audio"] = {
                "derived_from": (obj.id if obj else art.meta.get("source_ko", "")),
                "expression_version": art.meta.get("expression_version", "v0.1"),
                "voice_model": art.meta.get("voice_model", ""),
                "artifact": art.path,
                **{k: v for k, v in art.meta.items() if k not in {"expression_version", "voice_model"}},
            }
    return out


def write_manifest(
    package_dir: Path,
    *,
    run: TaskRun,
    models: ModelVersions,
    artifacts: list[Artifact],
    options: dict[str, Any],
    obj: KnowledgeObject | None = None,
    error: str | None = None,
) -> Path:
    manifest = PackageManifest(
        id=run.id,
        status=run.status,
        source=run.source,
        package_dir=package_dir.as_posix(),
        options=options,
        models=models,
        steps=[step.model_dump(mode="json") for step in run.steps],
        artifacts=[art.model_dump(mode="json") for art in artifacts],
        expressions=_expression_evidence(artifacts, obj),
        error=error,
    )
    if obj is not None:
        manifest.knowledge_object = "knowledge_object.json"
    path = package_dir / "manifest.json"
    write_json(path, manifest)
    return path
