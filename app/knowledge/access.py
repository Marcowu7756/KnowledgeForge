from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel, Field

Classification = Literal["public", "internal", "restricted", "secret"]
SourceProject = Literal["setv", "factorlib", "asharelib", ""]
ExportPolicy = Literal["local_only", "export_ok"]

CLASSIFICATION_ORDER: dict[str, int] = {
    "public": 0,
    "internal": 1,
    "restricted": 2,
    "secret": 3,
}

DEFAULT_PROPRIETARY_CLASSIFICATION: Classification = "restricted"
DEFAULT_PROPRIETARY_EXPORT: ExportPolicy = "local_only"


class AccessBlock(BaseModel):
    classification: Classification = "public"
    source_project: SourceProject = ""
    export_policy: ExportPolicy = "export_ok"

    def is_retrievable(self, *, max_level: Classification | None = None) -> bool:
        ceiling = max_level or max_retrieve_classification()
        return classification_leq(self.classification, ceiling)

    def is_compose_eligible(self, *, llm_provider: str) -> bool:
        return is_compose_eligible(self.classification, llm_provider=llm_provider)


def classification_leq(left: str, right: str) -> bool:
    return CLASSIFICATION_ORDER.get(left, 0) <= CLASSIFICATION_ORDER.get(right, 99)


def max_retrieve_classification() -> Classification:
    raw = os.getenv("KF_ACCESS_MAX_RETRIEVE", "restricted").strip().lower()
    if raw in CLASSIFICATION_ORDER:
        return raw  # type: ignore[return-value]
    return "restricted"


def include_secret_in_retrieve() -> bool:
    return os.getenv("KF_ACCESS_INCLUDE_SECRET", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def is_retrievable(classification: str, *, max_level: Classification | None = None) -> bool:
    if classification == "secret" and not include_secret_in_retrieve():
        return False
    ceiling = max_level or max_retrieve_classification()
    return classification_leq(classification, ceiling)


def is_compose_eligible(classification: str, *, llm_provider: str) -> bool:
    if classification == "secret":
        return False
    provider = (llm_provider or "ollama").strip().lower()
    if provider == "ollama":
        return True
    return classification in {"public", "internal"}


def infer_source_project(*parts: str | None) -> SourceProject:
    blob = " ".join(p for p in parts if p).lower().replace("\\", "/")
    if "setv" in blob:
        return "setv"
    if "factorlib" in blob or "factor-lib" in blob or "factor_lib" in blob:
        return "factorlib"
    if "asharelib" in blob or "ashare-lib" in blob or "ashare_lib" in blob:
        return "asharelib"
    return ""


def default_access_for_ingest(
    *,
    source_path: str | None = None,
    dest_path: str | None = None,
    tags: list[str] | None = None,
) -> AccessBlock:
    """Assign default classification for new KOs (§8)."""
    project = infer_source_project(source_path, dest_path, " ".join(tags or []))
    norm_dest = (dest_path or "").replace("\\", "/").lower()
    if project or "/restricted/" in norm_dest or norm_dest.endswith("/restricted"):
        return AccessBlock(
            classification=DEFAULT_PROPRIETARY_CLASSIFICATION,
            source_project=project,
            export_policy=DEFAULT_PROPRIETARY_EXPORT,
        )
    return AccessBlock()


def access_from_meta(meta: dict) -> AccessBlock:
    nested = meta.get("access")
    if isinstance(nested, dict):
        return AccessBlock.model_validate(nested)
    classification = str(meta.get("access_classification") or meta.get("classification") or "public")
    if classification not in CLASSIFICATION_ORDER:
        classification = "public"
    project = str(meta.get("access_source_project") or meta.get("source_project") or "")
    if project not in {"setv", "factorlib", "asharelib"}:
        project = ""
    export = str(meta.get("access_export_policy") or meta.get("export_policy") or "export_ok")
    if export not in {"local_only", "export_ok"}:
        export = "export_ok"
    return AccessBlock(
        classification=classification,  # type: ignore[arg-type]
        source_project=project,  # type: ignore[arg-type]
        export_policy=export,  # type: ignore[arg-type]
    )


def access_to_meta_lines(access: AccessBlock) -> list[str]:
    if access.classification == "public" and not access.source_project:
        return []
    lines = [
        "access:",
        f"  classification: {access.classification}",
    ]
    if access.source_project:
        lines.append(f"  source_project: {access.source_project}")
    if access.export_policy != "export_ok":
        lines.append(f"  export_policy: {access.export_policy}")
    return lines


def access_dict(access: AccessBlock) -> dict[str, str]:
    payload: dict[str, str] = {"classification": access.classification}
    if access.source_project:
        payload["source_project"] = access.source_project
    if access.export_policy != "export_ok":
        payload["export_policy"] = access.export_policy
    return payload
