"""H3 · offline GNN-style propagation on frozen ConceptGraph (numpy + networkx).

H3a: evaluate / write shadow scores (never default retrieve path)
H3b: shadow JSON artifact for inspection
H3c: optional blend only when KF_GNN_BOOST=1 (caller / retrieve)

Does not replace rule edges or invent producer IDs.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np

from app.reconstruct.evolve import load_graph
from app.reconstruct.models import ConceptGraph

GNN_VERSION = "gnn_offline_v0"
SHADOW_NAME = "gnn_shadow_scores.json"


def gnn_boost_enabled() -> bool:
    return (os.environ.get("KF_GNN_BOOST") or "").strip() in {"1", "true", "TRUE", "yes", "on"}


@dataclass
class GnnEvalResult:
    graph_id: str
    method: str
    seeds: list[str]
    scores: dict[str, float]  # ko_id → score
    output_path: Path | None
    stats: dict[str, Any]


def _ko_id_from_node(node_id: str, ko_ids: list[str]) -> str | None:
    if node_id.startswith("ko_"):
        return node_id[3:] if len(node_id) > 3 else None
    if ko_ids:
        return ko_ids[0]
    return None


def concept_graph_to_nx(graph: ConceptGraph) -> tuple[nx.Graph, dict[str, str]]:
    """Build undirected KO↔KO graph; map node_id → ko_id for KO nodes."""
    g = nx.Graph()
    node_to_ko: dict[str, str] = {}
    for node in graph.nodes:
        if node.kind != "knowledge_object":
            continue
        kid = _ko_id_from_node(node.id, node.ko_ids)
        if not kid:
            continue
        node_to_ko[node.id] = kid
        g.add_node(kid, label=node.label)

    for edge in graph.relations.edges:
        members = set(edge.source_ko_ids or [])
        for nid in (edge.from_node, edge.to_node):
            if nid in node_to_ko:
                members.add(node_to_ko[nid])
            elif nid.startswith("ko_") and len(nid) > 3:
                members.add(nid[3:])
        ordered = sorted(members)
        if len(ordered) < 2:
            continue
        w = float(edge.confidence or 0.5) * float(edge.weight or 1.0)
        w = max(0.05, min(2.0, w))
        for i, a in enumerate(ordered):
            if a not in g:
                g.add_node(a)
            for b in ordered[i + 1 :]:
                if b not in g:
                    g.add_node(b)
                if g.has_edge(a, b):
                    g[a][b]["weight"] = max(g[a][b].get("weight", 0.0), w)
                else:
                    g.add_edge(a, b, weight=w, kind=edge.kind)
    return g, node_to_ko


def _normalized_adjacency(g: nx.Graph, nodes: list[str]) -> np.ndarray:
    n = len(nodes)
    idx = {k: i for i, k in enumerate(nodes)}
    a = np.zeros((n, n), dtype=np.float64)
    for u, v, data in g.edges(data=True):
        if u not in idx or v not in idx:
            continue
        w = float(data.get("weight") or 1.0)
        i, j = idx[u], idx[v]
        a[i, j] = w
        a[j, i] = w
    deg = a.sum(axis=1)
    deg_safe = np.where(deg > 0, deg, 1.0)
    # Symmetric normalized: D^{-1/2} A D^{-1/2}
    d_inv_sqrt = 1.0 / np.sqrt(deg_safe)
    return (d_inv_sqrt[:, None] * a) * d_inv_sqrt[None, :]


def propagate_scores(
    g: nx.Graph,
    seeds: list[str],
    *,
    steps: int = 8,
    alpha: float = 0.85,
) -> dict[str, float]:
    """Simple GCN-style / personalized diffusion on KO graph (H3a offline)."""
    if g.number_of_nodes() == 0:
        return {}
    nodes = sorted(g.nodes())
    idx = {k: i for i, k in enumerate(nodes)}
    seed_set = [s for s in seeds if s in idx]
    if not seed_set:
        # If no seed in graph, use highest-degree nodes as weak seeds
        deg = sorted(g.degree(), key=lambda x: -x[1])
        seed_set = [n for n, _ in deg[: max(1, min(3, len(deg)))]]

    a_hat = _normalized_adjacency(g, nodes)
    x0 = np.zeros(len(nodes), dtype=np.float64)
    for s in seed_set:
        x0[idx[s]] = 1.0
    if x0.sum() > 0:
        x0 = x0 / x0.sum()

    x = x0.copy()
    for _ in range(max(1, steps)):
        x = alpha * (a_hat @ x) + (1.0 - alpha) * x0

    # Zero out exact seeds for neighbor ranking convenience (optional keep)
    scores = {nodes[i]: float(x[i]) for i in range(len(nodes))}
    # Normalize to max=1 for readability
    m = max(scores.values()) if scores else 0.0
    if m > 0:
        scores = {k: v / m for k, v in scores.items()}
    return scores


def run_offline_gnn(
    graph: ConceptGraph | str | Path,
    *,
    seeds: list[str] | None = None,
    steps: int = 8,
    alpha: float = 0.85,
    out_path: Path | None = None,
    write_beside_graph: bool = True,
) -> GnnEvalResult:
    """H3a/H3b: offline propagation → optional shadow JSON."""
    if not isinstance(graph, ConceptGraph):
        graph = load_graph(graph)
    g, _ = concept_graph_to_nx(graph)
    seed_list = list(seeds or [])
    if not seed_list:
        seed_list = list(graph.source_ko_ids[:3]) if graph.source_ko_ids else []

    scores = propagate_scores(g, seed_list, steps=steps, alpha=alpha)
    ranked = sorted(scores.items(), key=lambda x: -x[1])

    payload = {
        "schema": "kf_gnn_shadow_v0",
        "gnn_version": GNN_VERSION,
        "h3": "H3a+H3b",
        "created": datetime.now(timezone.utc).isoformat(),
        "graph_id": graph.id,
        "method": "symmetric_normalized_diffusion",
        "params": {"steps": steps, "alpha": alpha},
        "seeds": seed_list,
        "stats": {
            "ko_nodes": g.number_of_nodes(),
            "ko_edges": g.number_of_edges(),
            "scored": len(scores),
        },
        "scores": {k: round(v, 6) for k, v in ranked},
        "top": [{"ko_id": k, "score": round(v, 6)} for k, v in ranked[:20]],
        "note": "Shadow only — retrieve blend requires KF_GNN_BOOST=1 (H3c)",
    }

    written: Path | None = None
    if out_path is not None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written = out_path
    elif write_beside_graph:
        # Prefer reconstruct dir if evidence has path — caller usually passes out_path
        pass

    return GnnEvalResult(
        graph_id=graph.id,
        method=payload["method"],
        seeds=seed_list,
        scores=scores,
        output_path=written,
        stats=payload["stats"],
    )


def load_shadow_scores(path: str | Path) -> dict[str, float]:
    p = Path(path)
    if p.is_dir():
        p = p / SHADOW_NAME
    data = json.loads(p.read_text(encoding="utf-8"))
    raw = data.get("scores") or {}
    return {str(k): float(v) for k, v in raw.items()}


def resolve_shadow_path(graph_path: str | Path | None) -> Path | None:
    if not graph_path:
        return None
    p = Path(graph_path)
    if p.is_dir():
        cand = p / SHADOW_NAME
        return cand if cand.is_file() else None
    if p.name == "concept_graph.json":
        cand = p.parent / SHADOW_NAME
        return cand if cand.is_file() else None
    return None
