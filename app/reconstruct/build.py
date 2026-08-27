from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone

from app.knowledge.object import KnowledgeObject
from app.reconstruct.models import (
    RECONSTRUCT_VERSION,
    ConceptGraph,
    GraphEdge,
    GraphNode,
    RelationLayer,
)
from app.reconstruct.rules import (
    RULES_VERSION,
    confidence_for,
    infer_relation_type,
    make_evidence,
    merge_confidence,
)


def _norm_concept(text: str) -> str:
    t = text.strip()
    t = re.sub(r"\s+", " ", t)
    return t


def _concept_id(label: str) -> str:
    key = _norm_concept(label).lower()
    key = re.sub(r"[^\w\u4e00-\u9fff]+", "_", key, flags=re.UNICODE).strip("_")
    if not key:
        # Deterministic fallback (no random uuid)
        digest = hashlib.sha1(label.encode("utf-8")).hexdigest()[:8]
        return f"c_{digest}"
    return f"c_{key[:64]}"


def _ko_node_id(ko_id: str) -> str:
    return f"ko_{ko_id}" if not ko_id.startswith("ko_") else ko_id


def _edge_id(frm: str, to: str, kind: str, label: str = "") -> str:
    raw = f"{kind}|{frm}|{to}|{label}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"e_{kind}_{digest}"


def stable_graph_id(ko_ids: list[str]) -> str:
    payload = json.dumps(
        {"kos": sorted(ko_ids), "v": RECONSTRUCT_VERSION, "rules": RULES_VERSION},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
    return f"cg_{digest}"


def build_graph(
    kos: list[KnowledgeObject],
    *,
    min_confidence: float = 0.0,
    base: ConceptGraph | None = None,
) -> ConceptGraph:
    """Union intra-KO relations + cross-KO links with relation quality metadata."""
    if len(kos) < 1:
        raise ValueError("build_graph requires at least 1 KnowledgeObject")

    # Deterministic KO order
    kos = sorted(kos, key=lambda o: o.id)
    nodes: dict[str, GraphNode] = {}
    edges: dict[str, GraphEdge] = {}
    concept_to_kos: dict[str, set[str]] = defaultdict(set)
    tag_to_kos: dict[str, set[str]] = defaultdict(set)

    def upsert_concept(label: str, ko_id: str) -> str:
        label = _norm_concept(label)
        if not label:
            return ""
        nid = _concept_id(label)
        node = nodes.get(nid)
        if node is None:
            nodes[nid] = GraphNode(id=nid, kind="concept", label=label, ko_ids=[ko_id])
        else:
            if ko_id not in node.ko_ids:
                node.ko_ids.append(ko_id)
                node.ko_ids.sort()
        concept_to_kos[nid].add(ko_id)
        return nid

    def add_edge(
        *,
        frm: str,
        to: str,
        type_: str,
        kind: str,
        label: str,
        source_ko_ids: list[str],
        rule_id: str,
        weight: float = 1.0,
        detail: str = "",
    ) -> None:
        if not frm or not to or frm == to:
            return
        eid = _edge_id(frm, to, kind, label)
        support = sorted(set(source_ko_ids))
        conf = confidence_for(rule_id, support_count=len(support), weight=weight)
        evidence = make_evidence(rule_id, sources=support, detail=detail)
        existing = edges.get(eid)
        if existing is None:
            edges[eid] = GraphEdge.model_validate(
                {
                    "id": eid,
                    "from": frm,
                    "to": to,
                    "type": type_,
                    "kind": kind,
                    "label": label,
                    "weight": weight,
                    "confidence": conf,
                    "source_ko_ids": support,
                    "evidence": evidence.model_dump(mode="json"),
                }
            )
        else:
            for kid in support:
                if kid not in existing.source_ko_ids:
                    existing.source_ko_ids.append(kid)
            existing.source_ko_ids.sort()
            existing.weight = max(existing.weight, weight)
            existing.confidence = merge_confidence(
                existing.confidence,
                conf,
                support_count=len(existing.source_ko_ids),
            )
            # Merge evidence sources
            merged_sources = sorted(
                set(existing.evidence.sources) | set(evidence.sources)
            )
            existing.evidence.sources = merged_sources
            if detail and detail not in existing.evidence.reason:
                existing.evidence.reason = f"{existing.evidence.reason}; {detail}"

    for obj in kos:
        kid = obj.id
        knid = _ko_node_id(kid)
        tags = sorted(_norm_concept(t) for t in obj.content.tags if _norm_concept(t))
        nodes[knid] = GraphNode(
            id=knid,
            kind="knowledge_object",
            label=obj.content.title,
            ko_ids=[kid],
            meta={"unit_id": obj.unit_id, "tags": tags},
        )

        for concept in sorted(obj.content.atomic_concepts, key=lambda c: c.lower()):
            cid = upsert_concept(concept, kid)
            if cid:
                add_edge(
                    frm=knid,
                    to=cid,
                    type_="related",
                    kind="ko_mentions",
                    label="mentions",
                    source_ko_ids=[kid],
                    rule_id="ko_mentions_concept",
                    weight=0.5,
                    detail=f"concept={concept}",
                )

        for tag in tags:
            tag_to_kos[tag].add(kid)

        for edge in obj.relations:
            a = upsert_concept(edge.from_node, kid)
            b = upsert_concept(edge.to_node, kid)
            rel_type = infer_relation_type(edge.label, edge.type)
            add_edge(
                frm=a,
                to=b,
                type_=rel_type,
                kind="intra_ko",
                label=edge.label or rel_type,
                source_ko_ids=[kid],
                rule_id="intra_ko_explicit",
                weight=1.0,
                detail=f"{edge.from_node}→{edge.to_node}",
            )

        for pre in sorted(obj.content.prerequisites, key=lambda s: s.lower()):
            cid = upsert_concept(pre[:40], kid)
            if cid:
                add_edge(
                    frm=cid,
                    to=knid,
                    type_="depends_on",
                    kind="prerequisite",
                    label="prerequisite",
                    source_ko_ids=[kid],
                    rule_id="prerequisite_declared",
                    weight=0.8,
                    detail=pre[:80],
                )

    for cid, ko_set in sorted(concept_to_kos.items()):
        if len(ko_set) < 2:
            continue
        ordered = sorted(ko_set)
        concept_label = nodes[cid].label if cid in nodes else "shared"
        for i, a in enumerate(ordered):
            for b in ordered[i + 1 :]:
                add_edge(
                    frm=_ko_node_id(a),
                    to=_ko_node_id(b),
                    type_="related",
                    kind="shared_concept",
                    label=concept_label,
                    source_ko_ids=[a, b],
                    rule_id="shared_concept_cross_ko",
                    weight=float(len(ko_set)),
                    detail=f"shared_concept={concept_label}",
                )

    for tag, ko_set in sorted(tag_to_kos.items()):
        if len(ko_set) < 2:
            continue
        ordered = sorted(ko_set)
        for i, a in enumerate(ordered):
            for b in ordered[i + 1 :]:
                add_edge(
                    frm=_ko_node_id(a),
                    to=_ko_node_id(b),
                    type_="related",
                    kind="shared_tag",
                    label=tag,
                    source_ko_ids=[a, b],
                    rule_id="shared_tag_cross_ko",
                    weight=0.6,
                    detail=f"shared_tag={tag}",
                )

    # Inter-KO prerequisite: match prerequisite text → other KO title / concept
    title_index: dict[str, str] = {
        _norm_concept(o.content.title).lower(): o.id
        for o in kos
        if _norm_concept(o.content.title)
    }
    concept_label_index: dict[str, set[str]] = defaultdict(set)
    for cid, ko_set in concept_to_kos.items():
        label = nodes[cid].label.lower() if cid in nodes else ""
        if label:
            concept_label_index[label] |= set(ko_set)

    for obj in kos:
        for pre in obj.content.prerequisites:
            key = _norm_concept(pre).lower()
            if not key:
                continue
            targets: set[str] = set()
            if key in title_index:
                targets.add(title_index[key])
            # substring / containment soft match on titles
            for title_key, tid in title_index.items():
                if key in title_key or title_key in key:
                    targets.add(tid)
            if key in concept_label_index:
                targets |= concept_label_index[key]
            targets.discard(obj.id)
            for tid in sorted(targets):
                add_edge(
                    frm=_ko_node_id(tid),
                    to=_ko_node_id(obj.id),
                    type_="depends_on",
                    kind="prerequisite",
                    label="prerequisite",
                    source_ko_ids=[obj.id, tid],
                    rule_id="prerequisite_inter_ko",
                    weight=0.85,
                    detail=f"prereq_match={pre[:80]}",
                )

    # Filter + stable sort
    kept = [e for e in edges.values() if e.confidence >= min_confidence]
    kept.sort(key=lambda e: (e.kind, -e.confidence, e.id))
    node_list = sorted(nodes.values(), key=lambda n: (n.kind, n.id))
    for n in node_list:
        n.ko_ids = sorted(set(n.ko_ids))

    kind_counts: dict[str, int] = defaultdict(int)
    conf_buckets = {"high(>=0.8)": 0, "mid(0.5-0.8)": 0, "low(<0.5)": 0}
    for e in kept:
        kind_counts[e.kind] += 1
        if e.confidence >= 0.8:
            conf_buckets["high(>=0.8)"] += 1
        elif e.confidence >= 0.5:
            conf_buckets["mid(0.5-0.8)"] += 1
        else:
            conf_buckets["low(<0.5)"] += 1

    ko_ids = [o.id for o in kos]
    now = datetime.now(timezone.utc)
    generation = 1
    created = now
    if base is not None:
        generation = base.generation + 1
        created = base.created
        # Keep stable id only if KO set identical; else recompute
        if sorted(base.source_ko_ids) == ko_ids:
            gid = base.id or stable_graph_id(ko_ids)
        else:
            gid = stable_graph_id(ko_ids)
    else:
        gid = stable_graph_id(ko_ids)

    return ConceptGraph(
        id=gid,
        created=created,
        updated=now,
        generation=generation,
        source_ko_ids=ko_ids,
        nodes=node_list,
        relations=RelationLayer(
            edges=kept,
            rules_version=RULES_VERSION,
            stats={
                "nodes": len(node_list),
                "edges": len(kept),
                "kos": len(kos),
                "min_confidence": min_confidence,
                "confidence_buckets": conf_buckets,
                **{f"edges_{k}": v for k, v in sorted(kind_counts.items())},
            },
        ),
        evidence={
            "reconstruct_version": RECONSTRUCT_VERSION,
            "pipeline": "reconstruct_v0.2",
            "method": "rules+union_intra_ko+shared_concept+shared_tag",
            "rules_version": RULES_VERSION,
            "ko_count": len(kos),
            "stable_id": True,
            "evolved_from": base.id if base else None,
            "generation": generation,
        },
    )
