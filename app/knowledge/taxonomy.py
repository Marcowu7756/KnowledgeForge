from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

TAXONOMY_REGISTRY_PATH = Path(__file__).with_name("taxonomy_registry.yaml")

# Display / LLM slot labels only — NOT access.classification levels.
# Target depth for capture/ecosystem chains: 4–5 segments (max clamp below).
LEVEL_NAMES = ("domain", "category", "subcategory", "topic", "leaf")
MAX_TAXONOMY_DEPTH = 5
_CAPTURE_LEAF_MAX_CHARS = 48
_FALLBACK_CAPTURE_ROOT = ["公开媒体", "捕获"]
_FALLBACK_SOURCE_LABELS = {
    "youtube": "YouTube",
    "bilibili": "Bilibili",
    "twitter": "Twitter",
    "file": "本地文件",
    "audio": "音频",
    "image": "图像",
    "search": "检索合成",
    "md": "本地文件",
    "pdf": "本地文件",
    "txt": "本地文件",
    "notes": "笔记",
}


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


def capture_profile() -> dict[str, Any]:
    registry = load_taxonomy_registry()
    raw = registry.get("capture")
    return raw if isinstance(raw, dict) else {}


def clamp_taxonomy_path(path: list[str], *, max_depth: int = MAX_TAXONOMY_DEPTH) -> list[str]:
    cleaned = _dedupe_taxonomy_path(path)
    if max_depth <= 0:
        return []
    return cleaned[:max_depth]


def _capture_leaf_title(leaf_title: str | None) -> str:
    text = " ".join(str(leaf_title or "").split()).strip()
    if not text:
        return "未命名"
    if len(text) <= _CAPTURE_LEAF_MAX_CHARS:
        return text
    return text[: _CAPTURE_LEAF_MAX_CHARS - 1].rstrip() + "…"


def default_taxonomy_for_capture(
    source_type: str,
    *,
    leaf_title: str | None = None,
) -> TaxonomyBlock:
    """Rule path for generic capture — independent of access.classification.

    Shape: capture.root + source label + title leaf (depth ≤ 5).
    """
    profile = capture_profile()
    root = profile.get("root") or _FALLBACK_CAPTURE_ROOT
    root_list = [str(s).strip() for s in root if str(s).strip()]
    if not root_list:
        root_list = list(_FALLBACK_CAPTURE_ROOT)

    key = (source_type or "file").strip().lower()
    by_type = profile.get("by_source_type") or {}
    label = ""
    if isinstance(by_type, dict):
        label = str(by_type.get(key) or "").strip()
    if not label:
        label = _FALLBACK_SOURCE_LABELS.get(key) or key or "本地文件"

    leaf = _capture_leaf_title(leaf_title)
    path = clamp_taxonomy_path([*root_list, label, leaf])
    return TaxonomyBlock(path=path)


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
