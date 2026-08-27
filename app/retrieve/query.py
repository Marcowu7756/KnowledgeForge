from __future__ import annotations

from pathlib import Path

import numpy as np

from app.reconstruct.evolve import load_graph
from app.reconstruct.models import ConceptGraph
from app.retrieve.embedder import embed_query, model_path_str
from app.retrieve.models import RetrieveHit, RetrieveResult
from app.retrieve.store import cosine_top_k, load_manifest, load_records, load_vectors


def _graph_neighbor_scores(
    graph: ConceptGraph,
    seed_ko_ids: list[str],
    *,
    min_confidence: float = 0.5,
) -> dict[str, tuple[float, str]]:
    """Boost KOs linked to semantic seeds via shared_concept / shared_tag edges."""
    seeds = set(seed_ko_ids)
    scores: dict[str, tuple[float, str]] = {}

    def consider(kid: str, boost: float, reason: str) -> None:
        if not kid or kid in seeds:
            return
        prev = scores.get(kid)
        if prev is None or boost > prev[0]:
            scores[kid] = (boost, reason)

    for edge in graph.relations.edges:
        if edge.confidence < min_confidence:
            continue
        if edge.kind not in {"shared_concept", "shared_tag"}:
            continue
        members = set(edge.source_ko_ids)
        for node_id in (edge.from_node, edge.to_node):
            if node_id.startswith("ko_"):
                members.add(node_id[3:])
        if not (members & seeds):
            continue
        weight = 1.0 if edge.kind == "shared_concept" else 0.55
        boost = float(edge.confidence) * weight
        reason = f"{edge.kind}:{edge.label or edge.evidence.rule_id}@{edge.confidence:.2f}"
        for kid in members:
            consider(kid, boost, reason)
    return scores


def retrieve_kos(
    query: str,
    *,
    top_k: int = 5,
    index_dir: Path | None = None,
    graph: ConceptGraph | None = None,
    graph_path: str | Path | None = None,
    graph_weight: float = 0.35,
    semantic_pool: int | None = None,
    min_graph_confidence: float = 0.5,
) -> RetrieveResult:
    """
    Graph-aware KO retrieval:
      semantic embed(query) → top pool
      + ConceptGraph neighbor boost
      → re-rank KnowledgeObjects (never document chunks)
    """
    query = query.strip()
    if not query:
        raise ValueError("empty query")

    manifest = load_manifest(index_dir)
    records = load_records(index_dir)
    matrix = load_vectors(index_dir)
    if not records or matrix.size == 0:
        raise FileNotFoundError(
            "empty retrieve index — run: python main.py retrieve index --from-index"
        )

    qvec = embed_query(query)
    pool = semantic_pool or max(top_k * 4, 12)
    pool = min(pool, len(records))
    ranked = cosine_top_k(qvec, matrix, top_k=pool)

    by_id = {r.ko_id: (i, r) for i, r in enumerate(records)}
    # Full semantic scores for explainable re-rank (still KO-level, not chunks)
    full_scores = matrix @ qvec.astype(np.float32)
    semantic: dict[str, float] = {}
    for idx, score in ranked:
        semantic[records[idx].ko_id] = float(score)

    g = graph
    if g is None and graph_path:
        g = load_graph(graph_path)

    graph_scores: dict[str, tuple[float, str]] = {}
    mode: str = "semantic"
    if g is not None and semantic:
        seeds = [
            kid for kid, _ in sorted(semantic.items(), key=lambda x: -x[1])[: max(3, top_k)]
        ]
        graph_scores = _graph_neighbor_scores(
            g, seeds, min_confidence=min_graph_confidence
        )
        mode = "graph_aware"
        # Ensure graph neighbors carry their true semantic similarity
        for kid in graph_scores:
            if kid in semantic or kid not in by_id:
                continue
            idx, _ = by_id[kid]
            semantic[kid] = float(full_scores[idx])

    candidates = set(semantic.keys())
    if mode == "graph_aware":
        # Keep semantic pool; add graph neighbors that are in the KO index
        candidates |= {kid for kid in graph_scores if kid in by_id}

    alpha = 1.0 - graph_weight if mode == "graph_aware" else 1.0
    beta = graph_weight if mode == "graph_aware" else 0.0

    hits: list[RetrieveHit] = []
    top_sem = ranked[0][1] if ranked else 0.0
    for kid in candidates:
        pair = by_id.get(kid)
        if pair is None:
            continue
        _, rec = pair
        sem = semantic.get(kid, 0.0)
        gscore, greason = graph_scores.get(kid, (0.0, ""))
        # Soft-gate: graph boost only counts when semantic is not near-zero
        effective_graph = gscore if sem >= 0.15 else gscore * 0.25
        final = alpha * sem + beta * effective_graph
        why = [f"semantic={sem:.4f}"]
        if greason:
            why.append(
                f"graph_boost={effective_graph:.4f} ({greason})"
                + ("" if sem >= 0.15 else "; gated_low_semantic")
            )
        if top_sem > 0 and sem >= top_sem * 0.98 and kid in dict(ranked):
            # mark seeds from initial pool
            if any(records[i].ko_id == kid for i, _ in ranked[: max(3, top_k)]):
                why.append("semantic_seed")
        hits.append(
            RetrieveHit(
                ko_id=kid,
                title=rec.title,
                score=round(final, 6),
                semantic_score=round(sem, 6),
                graph_score=round(effective_graph, 6),
                path=rec.path,
                concepts=list(rec.concepts[:12]),
                tags=list(rec.tags[:8]),
                summary=rec.summary,
                why=why,
                vector_id=rec.vector_id,
            )
        )

    hits.sort(key=lambda h: (-h.score, h.ko_id))
    hits = hits[:top_k]

    return RetrieveResult(
        query=query,
        mode=mode,  # type: ignore[arg-type]
        top_k=top_k,
        hits=hits,
        evidence={
            "pipeline": "retrieve_v0.1",
            "unit": "knowledge_object",
            "embed_model": manifest.model or model_path_str(),
            "index_count": manifest.count,
            "graph_id": g.id if g else None,
            "graph_weight": beta,
            "semantic_pool": pool,
            "min_graph_confidence": min_graph_confidence,
        },
    )
