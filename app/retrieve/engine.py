from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app import config
from app.retrieve.embed_writeback import EmbeddingWritebackReport
from app.retrieve.index_build import build_ko_index
from app.retrieve.models import IndexManifest, RetrieveResult
from app.retrieve.query import retrieve_kos
from app.retrieve.store import retrieve_dir


@dataclass
class IndexBuildResult:
    manifest: IndexManifest
    index_dir: Path
    count: int
    writeback: EmbeddingWritebackReport | None = None


@dataclass
class QueryRunResult:
    result: RetrieveResult
    output_dir: Path | None
    result_path: Path | None


def run_index(
    *,
    paths: list[str] | None = None,
    from_index: bool = False,
    from_packages: bool = False,
    subdir: str | None = None,
    tag: str | None = None,
    taxonomy_prefix: str | None = None,
    limit: int | None = None,
    write_back_packages: bool = True,
    write_back_dry_run: bool = False,
) -> IndexBuildResult:
    dest = retrieve_dir()
    manifest, kos, writeback = build_ko_index(
        paths=paths,
        from_index=from_index,
        from_packages=from_packages,
        subdir=subdir,
        tag=tag,
        taxonomy_prefix=taxonomy_prefix,
        limit=limit,
        dest=dest,
        write_back_packages=write_back_packages,
        write_back_dry_run=write_back_dry_run,
    )
    return IndexBuildResult(
        manifest=manifest,
        index_dir=dest,
        count=len(kos),
        writeback=writeback,
    )


def run_query(
    query: str,
    *,
    top_k: int = 5,
    graph_path: str | None = None,
    graph_weight: float = 0.35,
    save: bool = True,
    access_lane: str | None = None,
    max_level: str | None = None,
) -> QueryRunResult:
    result = retrieve_kos(
        query,
        top_k=top_k,
        graph_path=graph_path,
        graph_weight=graph_weight,
        access_lane=access_lane,
        max_level=max_level,
    )
    out: Path | None = None
    path: Path | None = None
    if save:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = config.RETRIEVE_DIR / "queries" / f"{stamp}_{uuid4().hex[:6]}"
        out.mkdir(parents=True, exist_ok=True)
        path = out / "result.json"
        path.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
        (out / "QUERY.md").write_text(
            _render_md(result),
            encoding="utf-8",
        )
    return QueryRunResult(result=result, output_dir=out, result_path=path)


def _render_md(result: RetrieveResult) -> str:
    lines = [
        f"# Retrieve — {result.query}",
        "",
        "```yaml",
        f"mode: {result.mode}",
        f"top_k: {result.top_k}",
        f"unit: knowledge_object",
        f"graph_id: {result.evidence.get('graph_id')}",
        "```",
        "",
        "## Hits",
        "",
    ]
    for i, hit in enumerate(result.hits, start=1):
        lines.append(f"### {i}. {hit.title}")
        lines.append("")
        lines.append(f"- ko_id: `{hit.ko_id}`")
        lines.append(f"- score: {hit.score:.4f} (semantic={hit.semantic_score:.4f}, graph={hit.graph_score:.4f})")
        lines.append(f"- path: `{hit.path}`")
        if hit.concepts:
            lines.append(f"- concepts: {', '.join(hit.concepts[:8])}")
        for w in hit.why:
            lines.append(f"- why: {w}")
        if hit.summary:
            lines.append("")
            lines.append(hit.summary[:280])
        lines.append("")
    return "\n".join(lines)
