from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from app import config
from app.knowledge.access import default_access_for_ingest
from app.compression.llm import compress
from app.compression.parse import CompressParseError
from app.ingest.bilibili import BilibiliIngestError, ingest_bilibili
from app.ingest.docs import ingest_file
from app.ingest.errors import FileIngestError
from app.ingest.audio import AudioIngestError, ingest_audio
from app.ingest.image import ImageIngestError, ingest_image
from app.ingest.search import SearchHit, search_files
from app.ingest.twitter import TwitterIngestError, ingest_twitter, ingest_twitter_timeline
from app.ingest.youtube import YouTubeIngestError, ingest_youtube
from app.models import IngestedSource, KnowledgeUnit
from app.process.cleaner import clean_text
from app.process.splitter import split_text
from app.storage.index import upsert_index
from app.storage.markdown import write_knowledge_unit

# Keep compressor input inside typical local-model context budgets.
_MAX_COMPRESS_CHARS = 12_000
_RETRY_COMPRESS_CHARS = 6_000


@dataclass
class PipelineResult:
    source: IngestedSource
    unit: KnowledgeUnit
    markdown_path: Path
    raw_path: Path
    truncated: bool


@dataclass
class SearchBatchResult:
    hits: list[SearchHit]
    results: list[PipelineResult] = field(default_factory=list)
    synthesis: PipelineResult | None = None
    skipped: list[tuple[Path, str]] = field(default_factory=list)


def _save_raw(source: IngestedSource) -> Path:
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    video_id = source.metadata.get("video_id") if source.metadata else None
    stem_src = video_id or (Path(source.path).stem if source.path else None)
    stem = stem_src or source.title.replace(" ", "_")[:40] or "source"
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in stem)[:60]
    path = config.RAW_DIR / f"{stamp}_{safe}.txt"
    header = [
        f"title: {source.title}",
        f"type: {source.source_type}",
        f"url: {source.url or ''}",
        f"path: {source.path or ''}",
        "",
        source.text,
    ]
    path.write_text("\n".join(header), encoding="utf-8")
    return path


def _prepare_text(text: str) -> tuple[str, bool]:
    cleaned = clean_text(text)
    chunks = split_text(cleaned, max_chars=_MAX_COMPRESS_CHARS)
    if not chunks:
        raise ValueError("source text is empty after cleaning")
    if len(chunks) == 1:
        return chunks[0], False
    return chunks[0], True


def _compress_with_retry(source: IngestedSource, prepared: str) -> KnowledgeUnit:
    try:
        return compress(
            prepared,
            title=source.title,
            source_type=source.source_type,
            source=source.path or source.title,
            url=source.url,
        )
    except CompressParseError:
        chunks = split_text(clean_text(source.text), max_chars=_RETRY_COMPRESS_CHARS)
        if not chunks:
            raise
        return compress(
            chunks[0],
            title=source.title,
            source_type=source.source_type,
            source=source.path or source.title,
            url=source.url,
        )


def _finalize(
    source: IngestedSource,
    *,
    dest_dir: Path | None = None,
    extra_tags: list[str] | None = None,
    index: bool | None = None,
) -> PipelineResult:
    raw_path = _save_raw(source)
    prepared, truncated = _prepare_text(source.text)
    unit = _compress_with_retry(source, prepared)
    if extra_tags:
        for tag in extra_tags:
            if tag not in unit.tags:
                unit.tags.append(tag)
    if truncated and "truncated-source" not in unit.tags:
        unit.tags.append("truncated-source")
    if truncated:
        unit.unknowns.append(
            "Source text exceeded compressor context; only the first chunk was compressed."
        )
    dest_rel = ""
    if dest_dir is not None:
        try:
            dest_rel = dest_dir.relative_to(config.ROOT).as_posix()
        except ValueError:
            dest_rel = str(dest_dir)
    unit.access = default_access_for_ingest(
        source_path=source.path or source.source,
        dest_path=dest_rel,
        tags=unit.tags,
    )
    filename_stem = None
    if source.path:
        filename_stem = f"{Path(source.path).stem}_{source.source_type}"
    elif source.metadata.get("kind") == "synthesis":
        filename_stem = source.title
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


def run_youtube(url: str, *, index: bool | None = None) -> PipelineResult:
    source = ingest_youtube(url)
    return _finalize(source, extra_tags=["youtube"], index=index)


def run_bilibili(url: str, *, index: bool | None = None) -> PipelineResult:
    source = ingest_bilibili(url)
    return _finalize(source, extra_tags=["bilibili"], index=index)


def run_twitter(url: str, *, index: bool | None = None) -> PipelineResult:
    source = ingest_twitter(url)
    return _finalize(source, extra_tags=["twitter"], index=index)


def run_twitter_timeline(
    username: str,
    *,
    limit: int = 10,
    index: bool | None = None,
) -> PipelineResult:
    source = ingest_twitter_timeline(username, limit=limit)
    return _finalize(source, extra_tags=["twitter", "timeline"], index=index)


def run_file(
    path: str | Path,
    *,
    dest_dir: Path | None = None,
    extra_tags: list[str] | None = None,
    index: bool | None = None,
) -> PipelineResult:
    source = ingest_file(path)
    return _finalize(source, dest_dir=dest_dir, extra_tags=extra_tags, index=index)


def run_image(
    path: str | Path,
    *,
    dest_dir: Path | None = None,
    index: bool | None = None,
) -> PipelineResult:
    source = ingest_image(path)
    return _finalize(source, dest_dir=dest_dir, extra_tags=["image", "ocr"], index=index)


def run_audio(
    path: str | Path,
    *,
    dest_dir: Path | None = None,
    index: bool | None = None,
) -> PipelineResult:
    source = ingest_audio(path)
    return _finalize(source, dest_dir=dest_dir, extra_tags=["audio", "asr"], index=index)


def _synthesis_source(
    results: list[PipelineResult],
    *,
    title: str,
    keyword: str,
    roots: list[Path],
) -> IngestedSource:
    blocks: list[str] = [
        f"# {title}",
        f"Keyword: {keyword}",
        "Roots:",
        *[f"- {root}" for root in roots],
        "",
        "Compress these source cards into ONE integrated methodology atlas.",
        "Preserve shared framework, named methods, and contradictions across sources.",
        "Do not invent content that no card supports.",
        "",
    ]
    for result in results:
        unit = result.unit
        src = result.source.path or result.source.title
        blocks.extend(
            [
                f"## {unit.title}",
                f"Source path: {src}",
                f"Summary: {unit.summary}",
                "Concepts: " + "; ".join(unit.concepts),
                "Key points:",
                *[f"- {point}" for point in unit.key_points],
                "Relationships:",
                *[f"- {rel}" for rel in unit.relationships],
                "Unknowns:",
                *[f"- {unk}" for unk in unit.unknowns],
                "",
            ]
        )
    return IngestedSource(
        source_type="notes",
        title=title,
        text="\n".join(blocks),
        metadata={
            "kind": "synthesis",
            "keyword": keyword,
            "member_count": len(results),
            "read_only_source": True,
            "member_paths": [r.source.path for r in results if r.source.path],
        },
    )


def run_search(
    roots: list[str | Path],
    *,
    keyword: str,
    dest_subdir: str | None = None,
    synthesize: bool = True,
    synthesis_title: str | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    index: bool | None = None,
) -> SearchBatchResult:
    """Search fixed folders by keyword, compress matches into KnowledgeForge only.

    External roots are read-only data sources and are never modified.
    """
    hits = search_files(roots, keyword=keyword)
    if limit is not None:
        hits = hits[: max(0, limit)]

    batch = SearchBatchResult(hits=hits)
    if dry_run:
        return batch

    dest_dir = None
    if dest_subdir:
        dest_dir = config.KNOWLEDGE_DIR / dest_subdir
        dest_dir.mkdir(parents=True, exist_ok=True)

    tag = keyword.strip().lower().replace(" ", "-")
    total = len(hits)
    for index_i, hit in enumerate(hits, start=1):
        print(f"[search] ({index_i}/{total}) {hit.path}", flush=True)
        try:
            result = run_file(
                hit.path,
                dest_dir=dest_dir,
                extra_tags=["folder-search", tag, "read-only-source"],
                index=index,
            )
            batch.results.append(result)
            print(f"[ok] {result.markdown_path}", flush=True)
        except (FileIngestError, CompressParseError, Exception) as exc:  # noqa: BLE001
            batch.skipped.append((hit.path, str(exc)))
            print(f"[skip] {hit.path}: {exc}", flush=True)

    if synthesize and batch.results:
        title = synthesis_title or f"Integrated Knowledge — {keyword}"
        synth_source = _synthesis_source(
            batch.results,
            title=title,
            keyword=keyword,
            roots=[Path(r).resolve() for r in roots],
        )
        batch.synthesis = _finalize(
            synth_source,
            dest_dir=dest_dir,
            extra_tags=["folder-search", tag, "synthesis", "read-only-source"],
            index=index,
        )
    return batch


__all__ = [
    "AudioIngestError",
    "BilibiliIngestError",
    "FileIngestError",
    "ImageIngestError",
    "PipelineResult",
    "SearchBatchResult",
    "TwitterIngestError",
    "YouTubeIngestError",
    "run_audio",
    "run_bilibili",
    "run_file",
    "run_image",
    "run_search",
    "run_twitter",
    "run_twitter_timeline",
    "run_youtube",
]
