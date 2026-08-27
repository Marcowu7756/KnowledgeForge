from __future__ import annotations

from pathlib import Path

from app.harness.artifact import Artifact, ArtifactKind


class ValidationError(RuntimeError):
    """Artifact failed harness validation."""


_MIN_BYTES: dict[ArtifactKind, int] = {
    "source": 20,
    "transcript": 1,
    "knowledge_md": 80,
    "knowledge_json": 40,
    "knowledge_object": 80,
    "visual_expression": 80,
    "audio_expression": 40,
    "animation_schema": 40,
    "animation_gif": 500,
    "narration_wav": 500,
    "express_schema": 40,
    "manifest": 40,
}


def validate_artifact(artifact: Artifact) -> Artifact:
    path = Path(artifact.path)
    if not path.is_file():
        raise ValidationError(f"{artifact.kind}: file missing ({path})")
    if artifact.bytes <= 0:
        raise ValidationError(f"{artifact.kind}: empty file ({path})")
    minimum = _MIN_BYTES.get(artifact.kind, 1)
    if artifact.bytes < minimum:
        raise ValidationError(
            f"{artifact.kind}: too small ({artifact.bytes} < {minimum} bytes)"
        )
    if not artifact.checksum:
        raise ValidationError(f"{artifact.kind}: missing checksum")
    return artifact


def validate_many(artifacts: list[Artifact]) -> list[Artifact]:
    return [validate_artifact(item) for item in artifacts]
