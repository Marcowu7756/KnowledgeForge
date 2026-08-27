from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from app.knowledge.object import KnowledgeObject
from app.reconstruct.load import (
    ReconstructLoadError,
    collect_from_index,
    collect_from_packages_with_sources,
    collect_from_paths_with_sources,
)
from app.retrieve.embed_writeback import (
    EmbeddingWritebackReport,
    write_embedding_refs_to_packages,
)
from app.retrieve.embedder import EmbedderError, embed_texts, model_path_str
from app.retrieve.models import IndexManifest, IndexRecord
from app.retrieve.store import retrieve_dir, save_index
from app.retrieve.text import ko_embed_text, text_hash, vector_id_for


def _collect_with_sources(
    *,
    paths: list[str] | None,
    from_index: bool,
    from_packages: bool,
    subdir: str | None,
    tag: str | None,
    taxonomy_prefix: str | None,
    limit: int | None,
) -> tuple[list[KnowledgeObject], dict[str, Path]]:
    if paths:
        return collect_from_paths_with_sources(paths)
    if from_packages:
        return collect_from_packages_with_sources()
    if from_index:
        kos = collect_from_index(
            subdir=subdir,
            tag=tag,
            limit=limit,
            taxonomy_prefix=taxonomy_prefix,
        )
        return kos, {}
    raise ReconstructLoadError("specify paths, --from-index, or --from-packages")


def build_ko_index(
    *,
    paths: list[str] | None = None,
    from_index: bool = False,
    from_packages: bool = False,
    subdir: str | None = None,
    tag: str | None = None,
    taxonomy_prefix: str | None = None,
    limit: int | None = None,
    dest: Path | None = None,
    write_back_packages: bool = True,
    write_back_dry_run: bool = False,
) -> tuple[IndexManifest, list[KnowledgeObject], EmbeddingWritebackReport | None]:
    """Embed whole KnowledgeObjects into a local vector index (not doc chunks)."""
    kos, source_paths = _collect_with_sources(
        paths=paths,
        from_index=from_index,
        from_packages=from_packages,
        subdir=subdir,
        tag=tag,
        taxonomy_prefix=taxonomy_prefix,
        limit=limit,
    )
    kos = sorted({o.id: o for o in kos}.values(), key=lambda o: o.id)
    if not kos:
        raise ReconstructLoadError("no KnowledgeObjects to index")

    model = model_path_str()
    texts = [ko_embed_text(o) for o in kos]
    try:
        vectors = embed_texts(texts, normalize=True)
    except EmbedderError:
        raise

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    records: list[IndexRecord] = []
    for obj, text in zip(kos, texts, strict=True):
        vid = vector_id_for(obj.id, model)
        records.append(
            IndexRecord(
                ko_id=obj.id,
                vector_id=vid,
                title=obj.content.title,
                path=obj.knowledge_md or "",
                concepts=list(obj.content.atomic_concepts[:24]),
                tags=list(obj.content.tags[:16]),
                summary=(obj.content.summary or "")[:400],
                text_hash=text_hash(text),
                indexed_at=stamp,
                classification=obj.access.classification,
                source_project=obj.access.source_project,
                export_policy=obj.access.export_policy,
                taxonomy_path=list(obj.taxonomy.path),
            )
        )
        # Mark embedding status on in-memory object; optional package write-back below
        obj.embedding.model = model
        obj.embedding.vector_id = vid
        obj.embedding.status = "ready"

    root = dest or retrieve_dir()
    manifest = save_index(
        records=records,
        vectors=np.asarray(vectors, dtype=np.float32),
        model=model,
        evidence={
            "pipeline": "retrieve_v0.1",
            "unit": "knowledge_object",
            "chunking": "none",
            "ko_count": len(kos),
            "write_back_packages": write_back_packages,
        },
        root=root,
    )
    writeback: EmbeddingWritebackReport | None = None
    if write_back_packages:
        writeback = write_embedding_refs_to_packages(
            kos,
            source_paths=source_paths,
            dry_run=write_back_dry_run,
        )
    return manifest, kos, writeback
