from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app import config
from app.compression.ecosystem_prompt import (
    ECOSYSTEM_COMPRESS_SYSTEM,
    build_ecosystem_user_prompt,
)
from app.compression.parse import CompressParseError
from app.ingest.docs import ingest_file
from app.knowledge.access import AccessBlock, default_policy_for
from app.knowledge.taxonomy import (
    build_taxonomy_for_ingest,
    project_profile,
)
from app.pipeline import PipelineResult, _prepare_text, _save_raw
from app.models import IngestedSource


@dataclass
class EcosystemHit:
    path: Path
    reason: str = ""


@dataclass
class EcosystemBatchResult:
    project: str
    hits: list[EcosystemHit] = field(default_factory=list)
    results: list[PipelineResult] = field(default_factory=list)
    skipped: list[tuple[Path, str]] = field(default_factory=list)


def discover_design_docs(
    roots: list[str | Path],
    *,
    project: str,
) -> list[EcosystemHit]:
    profile = project_profile(project)
    globs = list(profile.get("doc_globs") or ["**/*.md", "**/*.txt"])
    exclude = {str(x).lower() for x in (profile.get("exclude_dir_names") or [])}
    hits: list[EcosystemHit] = []
    seen: set[str] = set()

    for raw_root in roots:
        root = Path(raw_root).expanduser().resolve()
        if not root.is_dir():
            raise NotADirectoryError(f"not a directory: {root}")
        for pattern in globs:
            for path in sorted(root.glob(pattern)):
                if not path.is_file():
                    continue
                if any(part.lower() in exclude for part in path.parts):
                    continue
                key = str(path)
                if key in seen:
                    continue
                seen.add(key)
                hits.append(EcosystemHit(path=path))
    return hits


def _ecosystem_compress(source: IngestedSource, *, project: str):
    profile = project_profile(project)
    focus = str(profile.get("compress_focus") or "")
    root = list(profile.get("root") or [])
    prepared, _ = _prepare_text(source.text)
    from app.compression.llm import complete_json
    from app.compression.parse import extract_json_object, knowledge_unit_from_payload

    user = build_ecosystem_user_prompt(
        project=project,
        focus=focus,
        title=source.title,
        source_type=source.source_type,
        text=prepared,
        taxonomy_root=root,
    )
    raw = complete_json(ECOSYSTEM_COMPRESS_SYSTEM, user)
    payload = extract_json_object(raw)
    llm_path = payload.get("taxonomy_path") or []
    if isinstance(llm_path, list):
        llm_segments = [str(x).strip() for x in llm_path if str(x).strip()]
    else:
        llm_segments = []
    taxonomy = build_taxonomy_for_ingest(
        project=project,
        source_path=source.path or source.title,
        llm_path=llm_segments,
    )
    return knowledge_unit_from_payload(
        payload,
        source=source.path or source.title,
        source_type=source.source_type,
        url=source.url,
        fallback_title=source.title,
        taxonomy=taxonomy,
    )


def _finalize_ecosystem(
    source: IngestedSource,
    *,
    project: str,
    dest_dir: Path,
    extra_tags: list[str] | None = None,
    index: bool | None = None,
) -> PipelineResult:
    from app.pipeline import _compress_with_retry, split_text, clean_text
    from app.storage.markdown import write_knowledge_unit
    from app.storage.index import upsert_index

    raw_path = _save_raw(source)
    prepared, truncated = _prepare_text(source.text)
    try:
        unit = _ecosystem_compress(source, project=project)
    except CompressParseError:
        # fallback: smaller chunk once
        chunks = split_text(clean_text(source.text), max_chars=6000)
        if not chunks:
            raise
        smaller = IngestedSource(
            source_type=source.source_type,
            title=source.title,
            text=chunks[0],
            url=source.url,
            path=source.path,
            metadata=dict(source.metadata),
        )
        unit = _ecosystem_compress(smaller, project=project)

    profile = project_profile(project)
    unit.access = AccessBlock(
        classification=profile.get("classification") or "restricted",
        source_project=project,  # type: ignore[arg-type]
        export_policy="local_only",
        policy=default_policy_for(profile.get("classification") or "restricted"),
    )
    for tag in [project, "ecosystem-ingest", "read-only-source", *(extra_tags or [])]:
        if tag not in unit.tags:
            unit.tags.append(tag)
    if truncated and "truncated-source" not in unit.tags:
        unit.tags.append("truncated-source")

    filename_stem = None
    if source.path:
        filename_stem = f"{Path(source.path).stem}_{project}"
    md_path = write_knowledge_unit(
        unit,
        dest_dir=dest_dir,
        filename_stem=filename_stem,
    )
    upsert_index(
        unit,
        md_path.relative_to(config.ROOT).as_posix(),
        source_path=source.path,
        dest_dir=dest_dir,
        enabled=index,
    )
    return PipelineResult(
        source=source,
        unit=unit,
        markdown_path=md_path,
        raw_path=raw_path,
        truncated=truncated,
    )


def run_ecosystem_ingest(
    project: str,
    roots: list[str | Path],
    *,
    limit: int | None = None,
    dry_run: bool = False,
    index: bool | None = None,
) -> EcosystemBatchResult:
    """Ingest SETV / FactorLib / AShareLib design docs → graded hierarchical KOs."""
    project = project.strip().lower()
    profile = project_profile(project)
    dest_subdir = str(profile.get("dest_subdir") or f"restricted/{project}")
    dest_dir = config.KNOWLEDGE_DIR / dest_subdir
    dest_dir.mkdir(parents=True, exist_ok=True)

    hits = discover_design_docs(roots, project=project)
    if limit is not None:
        hits = hits[: max(0, limit)]

    batch = EcosystemBatchResult(project=project, hits=hits)
    if dry_run:
        return batch

    total = len(hits)
    for i, hit in enumerate(hits, start=1):
        print(f"[ecosystem:{project}] ({i}/{total}) {hit.path}", flush=True)
        try:
            ingested = ingest_file(hit.path)
            ingested.metadata = {
                **(ingested.metadata or {}),
                "ecosystem_project": project,
                "read_only_source": True,
            }
            result = _finalize_ecosystem(
                ingested,
                project=project,
                dest_dir=dest_dir,
                extra_tags=[dest_subdir.replace("/", "-")],
                index=index,
            )
            batch.results.append(result)
            print(f"[ok] {result.markdown_path}", flush=True)
            print(f"     taxonomy: {result.unit.taxonomy.canonical}", flush=True)
        except Exception as exc:  # noqa: BLE001
            batch.skipped.append((hit.path, str(exc)))
            print(f"[skip] {hit.path}: {exc}", flush=True)
    return batch


__all__ = [
    "EcosystemBatchResult",
    "EcosystemHit",
    "discover_design_docs",
    "run_ecosystem_ingest",
]
