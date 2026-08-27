from __future__ import annotations

"""Relation quality rules: confidence, typed edges, evidence."""

from dataclasses import dataclass

from app.reconstruct.models import EdgeEvidence


@dataclass(frozen=True)
class RelationRule:
    rule_id: str
    kind: str
    base_confidence: float
    reason: str


RULES: dict[str, RelationRule] = {
    "intra_ko_explicit": RelationRule(
        rule_id="intra_ko_explicit",
        kind="intra_ko",
        base_confidence=0.92,
        reason="Explicit relation/mechanism edge declared inside a KnowledgeObject",
    ),
    "prerequisite_declared": RelationRule(
        rule_id="prerequisite_declared",
        kind="prerequisite",
        base_confidence=0.78,
        reason="Prerequisite field on KO mapped to depends_on edge",
    ),
    "prerequisite_inter_ko": RelationRule(
        rule_id="prerequisite_inter_ko",
        kind="prerequisite",
        base_confidence=0.72,
        reason="Prerequisite text matched another KO title/concept (inter-KO depends_on)",
    ),
    "ko_mentions_concept": RelationRule(
        rule_id="ko_mentions_concept",
        kind="ko_mentions",
        base_confidence=0.55,
        reason="KO lists concept in atomic_concepts",
    ),
    "shared_concept_cross_ko": RelationRule(
        rule_id="shared_concept_cross_ko",
        kind="shared_concept",
        base_confidence=0.70,
        reason="Same concept appears in ≥2 KnowledgeObjects",
    ),
    "shared_tag_cross_ko": RelationRule(
        rule_id="shared_tag_cross_ko",
        kind="shared_tag",
        base_confidence=0.45,
        reason="Same tag shared by ≥2 KnowledgeObjects (soft link)",
    ),
    "taxonomy_part_of": RelationRule(
        rule_id="taxonomy_part_of",
        kind="intra_ko",
        base_confidence=0.95,
        reason="Taxonomy parent → child part_of chain (纲举目张)",
    ),
    "taxonomy_ko_leaf": RelationRule(
        rule_id="taxonomy_ko_leaf",
        kind="intra_ko",
        base_confidence=0.93,
        reason="Taxonomy leaf node classifies a KnowledgeObject",
    ),
    "contrast_cross_ko": RelationRule(
        rule_id="contrast_cross_ko",
        kind="contrast_cross_ko",
        base_confidence=0.84,
        reason="Explicit vs/contrast relation resolved across ≥2 KnowledgeObjects",
    ),
}

RULES_VERSION = "rq_v0.3"

# Confidence floors / caps
MIN_CONFIDENCE = 0.05
MAX_CONFIDENCE = 0.99


def infer_relation_type(label: str, declared: str = "related") -> str:
    """Map free-text / declared type to a stable RelationType-like string."""
    declared = (declared or "related").strip().lower()
    if declared in {
        "controls",
        "causes",
        "depends_on",
        "contrasts",
        "part_of",
        "related",
        "defines",
    }:
        # Prefer declared when not the generic default from parser
        if declared != "causes" or not label:
            pass
    text = f"{label} {declared}".lower()
    if any(k in text for k in ("control", "控制", "主导")):
        return "controls"
    if any(k in text for k in ("cause", "导致", "引起", "→", "->", "because")):
        return "causes"
    if any(k in text for k in ("depend", "依赖", "基于", "prerequisite", "前置", "先修")):
        return "depends_on"
    if any(
        k in text
        for k in (
            "vs",
            "versus",
            "对比",
            "相对",
            "contrast",
            "对照",
            "区别于",
            "不同于",
            "对比于",
        )
    ):
        return "contrasts"
    if any(k in text for k in ("part", "组成", "属于", "包含")):
        return "part_of"
    if any(k in text for k in ("define", "定义", "即")):
        return "defines"
    if declared in {
        "controls",
        "causes",
        "depends_on",
        "contrasts",
        "part_of",
        "related",
        "defines",
    }:
        return declared
    return "related"


def confidence_for(
    rule_id: str,
    *,
    support_count: int = 1,
    weight: float = 1.0,
) -> float:
    rule = RULES[rule_id]
    # More supporting KOs / higher weight → slight boost, capped
    boost = min(0.15, 0.03 * max(0, support_count - 1) + 0.01 * max(0.0, weight - 1.0))
    score = rule.base_confidence + boost
    return round(max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, score)), 4)


def make_evidence(
    rule_id: str,
    *,
    sources: list[str],
    detail: str = "",
) -> EdgeEvidence:
    rule = RULES[rule_id]
    reason = rule.reason if not detail else f"{rule.reason}; {detail}"
    return EdgeEvidence(
        rule_id=rule.rule_id,
        reason=reason,
        sources=sorted(set(sources)),
    )


def merge_confidence(existing: float, incoming: float, *, support_count: int) -> float:
    """Combine confidences when the same edge is observed again."""
    blended = max(existing, incoming) + 0.02 * max(0, support_count - 1)
    return round(max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, blended)), 4)
