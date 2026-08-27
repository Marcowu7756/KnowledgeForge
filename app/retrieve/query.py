from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from app.knowledge.access import is_compose_eligible, is_retrievable, resolve_policy
from app.reconstruct.evolve import load_graph
from app.reconstruct.models import ConceptGraph
from app.retrieve.embedder import embed_query
from app.retrieve.models import IndexRecord, RetrieveHit, RetrieveResult
from app.retrieve.store import cosine_top_k, load_manifest, load_records, load_vectors

_TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text or "") if len(t) > 1}


def _query_overlap(query: str, rec: IndexRecord) -> float:
    """Fraction of query tokens that appear in title/concepts/tags (0..1)."""
    q = _tokens(query)
    if not q:
        return 0.0
    bag: set[str] = set()
    bag |= _tokens(rec.title)
    for c in rec.concepts:
        bag |= _tokens(c)
    for t in rec.tags:
        bag |= _tokens(t)
    if not bag:
        return 0.0
    return len(q & bag) / len(q)


def _graph_neighbor_scores(
    graph: ConceptGraph,
    seed_ko_ids: list[str],
    *,
    min_confidence: float = 0.5,
    allowed: set[str] | None = None,
) -> dict[str, tuple[float, str]]:
    """Boost KOs linked to semantic seeds via shared_concept / shared_tag edges.

    When ``allowed`` is set, only members inside that set receive boost
    (tightens noise: no out-of-pool graph expansion).
    """
    seeds = set(seed_ko_ids)
    scores: dict[str, tuple[float, str]] = {}

    def consider(kid: str, boost: float, reason: str) -> None:
        if not kid or kid in seeds:
            return
        if allowed is not None and kid not in allowed:
            return
        prev = scores.get(kid)
        if prev is None or boost > prev[0]:
            scores[kid] = (boost, reason)

    for edge in graph.relations.edges:
        if edge.confidence < min_confidence:
            continue
        if edge.kind not in {"shared_concept", "shared_tag", "contrast_cross_ko"}:
            continue
        members = set(edge.source_ko_ids)
        for node_id in (edge.from_node, edge.to_node):
            if node_id.startswith("ko_"):
                members.add(node_id[3:])
        if not (members & seeds):
            continue
        if edge.kind == "shared_concept":
            weight = 1.0
        elif edge.kind == "contrast_cross_ko":
            weight = 0.8
        else:
            weight = 0.55
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
    max_level: str | None = None,
    access_lane: str | None = None,
) -> RetrieveResult:
    """
    Graph-aware KO retrieval:
      semantic embed(query) → top pool
      + ConceptGraph neighbor boost (within pool only)
      → re-rank KnowledgeObjects (never document chunks)
    """
    from app.knowledge.access import lane_retrieve_ceiling

    query = query.strip()
    if not query:
        raise ValueError("empty query")

    ceiling = max_level
    if ceiling is None and access_lane:
        ceiling = lane_retrieve_ceiling(access_lane)

    manifest = load_manifest(index_dir)
    all_records = load_records(index_dir)
    all_matrix = load_vectors(index_dir)
    pairs = [
        (i, rec)
        for i, rec in enumerate(all_records)
        if is_retrievable(
            rec.classification,
            max_level=ceiling,  # type: ignore[arg-type]
            policy=resolve_policy(rec.classification, rec.access_policy),
        )
    ]
    records = [rec for _, rec in pairs]
    if pairs and all_matrix.size:
        row_idx = [i for i, _ in pairs]
        matrix = all_matrix[row_idx]
    else:
        matrix = all_matrix
    if not records or matrix.size == 0:
        raise FileNotFoundError(
            "empty retrieve index — run: python main.py retrieve index --from-index"
        )

    qvec = embed_query(query)
    pool = semantic_pool or max(top_k * 4, 12)
    pool = min(pool, len(records))
    ranked = cosine_top_k(qvec, matrix, top_k=pool)

    by_id = {r.ko_id: (i, r) for i, r in enumerate(records)}
    semantic: dict[str, float] = {}
    for idx, score in ranked:
        semantic[records[idx].ko_id] = float(score)

    # Candidates = semantic pool only (F-P1-01: no out-of-pool graph noise)
    candidates = set(semantic.keys())

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
            g,
            seeds,
            min_confidence=min_graph_confidence,
            allowed=candidates,
        )
        mode = "graph_aware"

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
        overlap = _query_overlap(query, rec)
        # Query-token overlap scales graph boost; soft-gate near-zero semantic
        overlap_factor = 0.25 + 0.75 * overlap if gscore > 0 else 1.0
        gated = gscore * overlap_factor
        if sem < 0.15:
            gated *= 0.25
        final = alpha * sem + beta * gated
        why = [f"semantic={sem:.4f}"]
        if greason:
            why.append(
                f"graph_boost={gated:.4f} ({greason}; overlap={overlap:.2f})"
                + ("" if sem >= 0.15 else "; gated_low_semantic")
            )
        if top_sem > 0 and sem >= top_sem * 0.98:
            if any(records[i].ko_id == kid for i, _ in ranked[: max(3, top_k)]):
                why.append("semantic_seed")
        hits.append(
            RetrieveHit(
                ko_id=kid,
                title=rec.title,
                score=round(final, 6),
                semantic_score=round(sem, 6),
                graph_score=round(gated, 6),
                path=rec.path,
                concepts=list(rec.concepts[:12]),
                tags=list(rec.tags[:8]),
                summary=rec.summary,
                why=why,
                vector_id=rec.vector_id,
                classification=rec.classification,
                access_policy=dict(rec.access_policy or {}),
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
            "model": manifest.model,
            "graph_id": g.id if g is not None else None,
            "semantic_pool": pool,
            "graph_weight": graph_weight if mode == "graph_aware" else 0.0,
            "candidates": len(candidates),
            "graph_boost_in_pool_only": True,
        },
    )
