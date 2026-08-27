"""Cross-KO explicit contrast (`vs`) linking and clustering — A8 deep."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

from app.knowledge.object import KnowledgeObject

AddEdgeFn = Callable[..., None]


@dataclass(frozen=True)
class ContrastLink:
    ko_a: str
    ko_b: str
    label: str
    source_ko_id: str
    left: str
    right: str


_CONTRAST_SEPARATORS = (
    " vs ",
    " VS ",
    " versus ",
    " Versus ",
    " 对比 ",
    " 相对于 ",
    " 区别于 ",
    " 不同于 ",
    " 对照 ",
    " 相较 ",
)


def _norm(text: str) -> str:
    return " ".join(str(text or "").strip().split())


def _ko_node_id(ko_id: str) -> str:
    return f"ko_{ko_id}" if not ko_id.startswith("ko_") else ko_id


def parse_contrast_line(line: str) -> tuple[str, str, str] | None:
    """Parse ``A vs B`` style lines → (left, right, separator label)."""
    raw = line.strip().lstrip("- ").strip()
    if not raw:
        return None
    for sep in _CONTRAST_SEPARATORS:
        if sep in raw:
            left, right = raw.split(sep, 1)
            left, right = left.strip(), right.strip()
            if left and right:
                return left, right, sep.strip()
    return None


def match_ko_ids_for_label(
    label: str,
    *,
    kos: list[KnowledgeObject],
    title_index: dict[str, str],
    concept_index: dict[str, set[str]],
    exclude: str | None = None,
) -> set[str]:
    key = _norm(label).lower()
    if not key:
        return set()
    found: set[str] = set()
    if key in title_index:
        found.add(title_index[key])
    for title_key, tid in title_index.items():
        if len(key) >= 2 and (key in title_key or title_key in key):
            found.add(tid)
    if key in concept_index:
        found |= concept_index[key]
    for concept_key, kids in concept_index.items():
        if len(key) >= 2 and (key in concept_key or concept_key in key):
            found |= kids
    for obj in kos:
        blob = " ".join([obj.content.title, *obj.content.atomic_concepts[:16]]).lower()
        if len(key) >= 2 and key in blob:
            found.add(obj.id)
    if exclude:
        found.discard(exclude)
    return found


def _side_belongs_to_ko(obj: KnowledgeObject, side: str) -> bool:
    key = _norm(side).lower()
    if not key:
        return False
    if key in _norm(obj.content.title).lower():
        return True
    return any(
        key in _norm(c).lower() or _norm(c).lower() in key
        for c in obj.content.atomic_concepts
    )


def collect_contrast_links(
    kos: list[KnowledgeObject],
    *,
    title_index: dict[str, str],
    concept_index: dict[str, set[str]],
) -> list[ContrastLink]:
    """Resolve explicit ``contrasts`` relation pairs to inter-KO links."""
    links: list[ContrastLink] = []
    seen: set[tuple[str, str, str]] = set()

    for obj in kos:
        for edge in obj.relations:
            if edge.type != "contrasts":
                continue
            left, right = edge.from_node, edge.to_node
            label = edge.label or f"{left} vs {right}"
            left_ids = match_ko_ids_for_label(
                left,
                kos=kos,
                title_index=title_index,
                concept_index=concept_index,
            )
            right_ids = match_ko_ids_for_label(
                right,
                kos=kos,
                title_index=title_index,
                concept_index=concept_index,
            )

            pairs: list[tuple[str, str]] = []
            if _side_belongs_to_ko(obj, left) and not _side_belongs_to_ko(obj, right):
                for rid in sorted(right_ids):
                    if rid != obj.id:
                        pairs.append((obj.id, rid))
            elif _side_belongs_to_ko(obj, right) and not _side_belongs_to_ko(obj, left):
                for lid in sorted(left_ids):
                    if lid != obj.id:
                        pairs.append((lid, obj.id))
            else:
                if obj.id in left_ids and obj.id not in right_ids:
                    for rid in sorted(right_ids):
                        if rid != obj.id:
                            pairs.append((obj.id, rid))
                elif obj.id in right_ids and obj.id not in left_ids:
                    for lid in sorted(left_ids):
                        if lid != obj.id:
                            pairs.append((lid, obj.id))
                else:
                    for lid in sorted(left_ids):
                        for rid in sorted(right_ids):
                            if lid != rid:
                                pairs.append((lid, rid))

            for a, b in pairs:
                ka, kb = sorted((a, b))
                dedupe = (ka, kb, label)
                if dedupe in seen:
                    continue
                seen.add(dedupe)
                links.append(
                    ContrastLink(
                        ko_a=ka,
                        ko_b=kb,
                        label=label,
                        source_ko_id=obj.id,
                        left=left,
                        right=right,
                    )
                )
    return links


def apply_contrast_links(links: list[ContrastLink], add_edge: AddEdgeFn) -> int:
    count = 0
    for link in links:
        support = sorted({link.ko_a, link.ko_b, link.source_ko_id})
        add_edge(
            frm=_ko_node_id(link.ko_a),
            to=_ko_node_id(link.ko_b),
            type_="contrasts",
            kind="contrast_cross_ko",
            label=link.label,
            source_ko_ids=support,
            rule_id="contrast_cross_ko",
            weight=1.0,
            detail=f"{link.left} vs {link.right}",
        )
        count += 1
    return count


def contrast_clusters_from_edges(
    edges: list,
    *,
    ko_ids: set[str],
) -> dict[str, set[str]]:
    """Union-find clusters over contrast_cross_ko edges."""
    parent = {kid: kid for kid in ko_ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for edge in edges:
        if getattr(edge, "kind", "") != "contrast_cross_ko":
            continue
        members = [kid for kid in edge.source_ko_ids if kid in ko_ids]
        for i, a in enumerate(members):
            for b in members[i + 1 :]:
                union(a, b)
        for node_id in (edge.from_node, edge.to_node):
            if not str(node_id).startswith("ko_"):
                continue
            kid = str(node_id)[3:]
            if kid not in ko_ids:
                continue
            for other in members:
                if other != kid:
                    union(kid, other)

    clusters: dict[str, set[str]] = defaultdict(set)
    for kid in ko_ids:
        clusters[find(kid)].add(kid)
    return dict(clusters)
