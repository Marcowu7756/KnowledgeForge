from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

TAXONOMY_REGISTRY_PATH = Path(__file__).with_name("taxonomy_registry.yaml")

# Ordered levels for display / LLM hints (path may extend beyond these).
LEVEL_NAMES = ("domain", "category", "subcategory", "topic", "leaf")


class TaxonomyBlock(BaseModel):
    """Hierarchical chain: 纲举目张 — e.g. 生物 > 动物 > 哺乳动物 > 灵长类 > 人."""

    path: list[str] = Field(default_factory=list)

    @field_validator("path", mode="before")
    @classmethod
    def _normalize_path(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            sep = "/" if "/" in raw else ">"
            return [p.strip() for p in raw.split(sep) if p.strip()]
        if isinstance(value, list):
            return [str(p).strip() for p in value if str(p).strip()]
        return []

    @property
    def canonical(self) -> str:
        return "/".join(self.path)

    @property
    def depth(self) -> int:
        return len(self.path)

    @property
    def leaf(self) -> str:
        return self.path[-1] if self.path else ""

    def prefix(self, n: int) -> list[str]:
        return self.path[: max(0, n)]

    def prefixes(self) -> list[list[str]]:
        return [self.path[: i + 1] for i in range(len(self.path))]

    def matches_prefix(self, prefix: list[str] | str) -> bool:
        if isinstance(prefix, str):
            prefix = [p for p in prefix.replace("\\", "/").split("/") if p]
        if len(prefix) > len(self.path):
            return False
        return self.path[: len(prefix)] == prefix

    def extend(self, *segments: str) -> TaxonomyBlock:
        extra = [s.strip() for s in segments if s and s.strip()]
        return TaxonomyBlock(path=[*self.path, *extra])

    def merged_with(self, other: TaxonomyBlock | None) -> TaxonomyBlock:
        if other is None or not other.path:
            return TaxonomyBlock(path=list(self.path))
        if not self.path:
            return TaxonomyBlock(path=list(other.path))
        if other.matches_prefix(self.path):
            return TaxonomyBlock(path=list(other.path))
        if self.matches_prefix(other.path):
            return TaxonomyBlock(path=list(self.path))
        return TaxonomyBlock(path=[*self.path, *other.path])


def taxonomy_from_payload(raw: Any) -> TaxonomyBlock:
    if raw is None:
        return TaxonomyBlock()
    if isinstance(raw, TaxonomyBlock):
        return raw
    if isinstance(raw, list):
        return TaxonomyBlock(path=raw)
    if isinstance(raw, str):
        return TaxonomyBlock(path=raw)
    if isinstance(raw, dict):
        if raw.get("path"):
            return TaxonomyBlock(path=raw.get("path"))
        ordered: list[str] = []
        for key in LEVEL_NAMES:
            val = str(raw.get(key) or "").strip()
            if val:
                ordered.append(val)
        return TaxonomyBlock(path=ordered)
    return TaxonomyBlock()


def taxonomy_from_meta(meta: dict) -> TaxonomyBlock:
    nested = meta.get("taxonomy")
    if nested is not None:
        return taxonomy_from_payload(nested)
    if meta.get("taxonomy_path"):
        return taxonomy_from_payload(meta.get("taxonomy_path"))
    return TaxonomyBlock()


def taxonomy_to_meta_lines(taxonomy: TaxonomyBlock) -> list[str]:
    if not taxonomy.path:
        return []
    # safe_dump escapes backslashes / quotes so Windows path noise cannot break YAML.
    path_yaml = yaml.safe_dump(
        list(taxonomy.path),
        allow_unicode=True,
        default_flow_style=True,
        sort_keys=False,
        width=10_000,
    ).strip()
    return ["taxonomy:", f"  path: {path_yaml}"]


def taxonomy_dict(taxonomy: TaxonomyBlock) -> dict[str, Any]:
    if not taxonomy.path:
        return {}
    return {"path": list(taxonomy.path)}


def load_taxonomy_registry() -> dict[str, Any]:
    if not TAXONOMY_REGISTRY_PATH.is_file():
        return {"projects": {}}
    data = yaml.safe_load(TAXONOMY_REGISTRY_PATH.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {"projects": {}}


def project_profile(project: str) -> dict[str, Any]:
    registry = load_taxonomy_registry()
    projects = registry.get("projects") or {}
    key = project.strip().lower()
    if key not in projects:
        raise ValueError(f"unknown ecosystem project {project!r}; expected setv|factorlib|asharelib")
    return projects[key]


def default_taxonomy_for_project(project: str) -> TaxonomyBlock:
    profile = project_profile(project)
    root = profile.get("root") or profile.get("taxonomy_root") or []
    return TaxonomyBlock(path=list(root))


def _is_windows_drive(part: str) -> bool:
    """True for Path.parts drive anchors like 'D:\\' or 'D:'."""
    s = str(part or "").strip().rstrip("\\/")
    return len(s) == 2 and s[0].isalpha() and s[1] == ":"


def infer_taxonomy_segments(source_path: str | Path) -> list[str]:
    """Best-effort segments from doc path (after stripping noise dirs)."""
    path = Path(source_path)
    skip = {
        "docs",
        "doc",
        "design",
        "documentation",
        "src",
        "lib",
        "data",
        "test",
        "tests",
        "readme",
    }
    parts: list[str] = []
    for raw in path.parts:
        if _is_windows_drive(raw) or raw in ("/", "\\"):
            continue
        stem = Path(raw).stem.lower()
        if stem in skip or raw.startswith("."):
            continue
        if raw.lower().endswith((".md", ".txt", ".pdf", ".docx")):
            label = Path(raw).stem.replace("_", " ").replace("-", " ").strip()
            if label:
                parts.append(label)
            continue
        label = raw.replace("_", " ").replace("-", " ").strip()
        if label and label.lower() not in skip:
            parts.append(label)
    return parts[-3:] if len(parts) > 3 else parts


_REPO_NOISE = {
    "fxtrading",
    "reference",
    "references",
}


def _dedupe_taxonomy_path(path: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for seg in path:
        key = str(seg or "").strip()
        if not key or _is_windows_drive(key):
            continue
        low = key.lower()
        if low in seen:
            continue
        seen.add(low)
        out.append(key)
    return out


def build_taxonomy_for_ingest(
    *,
    project: str,
    source_path: str | Path,
    llm_path: list[str] | None = None,
) -> TaxonomyBlock:
    base = default_taxonomy_for_project(project)
    inferred = infer_taxonomy_segments(source_path)
    merged = base
    if inferred:
        root_keys = {p.lower() for p in merged.path}
        filtered = [
            s
            for s in inferred
            if s.lower() not in root_keys and s.lower() not in _REPO_NOISE
        ]
        if filtered:
            merged = merged.extend(*filtered)
    if llm_path:
        merged = merged.merged_with(TaxonomyBlock(path=llm_path))
    return TaxonomyBlock(path=_dedupe_taxonomy_path(merged.path))
