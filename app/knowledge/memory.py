"""Memory kind + SETV Artifact citation (Export Contract v0 · cite-only)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

MemoryKind = Literal["semantic", "state"]

# AE-2 asset classes from SETV_ARTIFACT_EXPORT_CONTRACT_V0
SetvAssetClass = Literal[
    "snapshot",
    "evolution",
    "family",
    "measurement",
    "experiment",
    "uncertainty",
]

EXPORT_CONTRACT_VERSION = "setv_artifact_export_v0@v0.0.0"


class SetvArtifactRef(BaseModel):
    """Minimal Export Triple (AE-1) — consumer cite handle, not SETV runtime."""

    artifact_id: str
    evidence_pointer: str
    export_contract_version: str = EXPORT_CONTRACT_VERSION
    asset_class: SetvAssetClass = "snapshot"
    object_version: str = ""
    assembled_at: str = ""
    setv_root: str = ""

    def citation_block(self) -> str:
        lines = [
            f"artifact_id: {self.artifact_id}",
            f"asset_class: {self.asset_class}",
            f"evidence_pointer: {self.evidence_pointer}",
            f"export_contract_version: {self.export_contract_version}",
        ]
        if self.object_version:
            lines.append(f"object_version: {self.object_version}")
        return "\n".join(lines)


def setv_artifact_from_meta(meta: dict[str, Any]) -> SetvArtifactRef | None:
    nested = meta.get("setv_artifact") or meta.get("setv_cite")
    if isinstance(nested, dict) and nested.get("artifact_id"):
        return SetvArtifactRef.model_validate(nested)
    aid = str(meta.get("artifact_id") or "").strip()
    ptr = str(meta.get("evidence_pointer") or "").strip()
    if aid and ptr:
        return SetvArtifactRef(
            artifact_id=aid,
            evidence_pointer=ptr,
            export_contract_version=str(
                meta.get("export_contract_version") or EXPORT_CONTRACT_VERSION
            ),
            asset_class=str(meta.get("asset_class") or "snapshot"),  # type: ignore[arg-type]
        )
    return None


def setv_artifact_to_meta_lines(ref: SetvArtifactRef | None) -> list[str]:
    if ref is None or not ref.artifact_id:
        return []
    lines = [
        "setv_artifact:",
        f'  artifact_id: "{ref.artifact_id}"',
        f'  asset_class: "{ref.asset_class}"',
        f'  evidence_pointer: "{ref.evidence_pointer}"',
        f'  export_contract_version: "{ref.export_contract_version}"',
    ]
    if ref.object_version:
        lines.append(f'  object_version: "{ref.object_version}"')
    if ref.assembled_at:
        lines.append(f'  assembled_at: "{ref.assembled_at}"')
    return lines


def setv_artifact_dict(ref: SetvArtifactRef | None) -> dict[str, Any]:
    if ref is None or not ref.artifact_id:
        return {}
    return ref.model_dump(exclude_defaults=False)


def memory_kind_from_meta(meta: dict[str, Any]) -> MemoryKind:
    raw = str(meta.get("memory_kind") or "semantic").strip().lower()
    if raw == "state":
        return "state"
    return "semantic"


def memory_kind_to_meta_lines(kind: MemoryKind) -> list[str]:
    if kind == "semantic":
        return []
    return [f"memory_kind: {kind}"]
