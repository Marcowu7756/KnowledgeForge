from __future__ import annotations

"""Relation Gap (Class C): drop ultra-generic shared labels / clique fan-out."""

# Labels that appear on nearly every SETV / ecosystem card — clique noise, not signal.
GENERIC_SHARED_LABELS: frozenset[str] = frozenset(
    {
        "setv",
        "state",
        "snapshot",
        "state snapshot",
        "state family",
        "evolution",
        "family",
        "measurement",
        "experiment",
        "uncertainty",
        "knowledge",
        "cite-only",
        "cite only",
        "memory-state",
        "memory state",
        "ecosystem-ingest",
        "restricted-setv",
        "restricted",
        "local_only",
        "local-only",
        "(none)",
        "none",
        "n/a",
        "na",
        "null",
        "shared",
        # bare timeframe / bookkeeping tokens
        "h4",
        "h1",
        "m15",
        "m5",
        "d",
        "w",
        "tf",
        "timeframe",
    }
)

# Cap complete pairwise cliques: concept shared by too many KOs is not a useful edge.
MAX_SHARED_CONCEPT_FANOUT = 8
MAX_SHARED_TAG_FANOUT = 12
MIN_LABEL_LEN = 2


def normalize_shared_label(label: str) -> str:
    return " ".join((label or "").strip().lower().split())


def is_informative_shared_label(label: str) -> bool:
    """True when a shared_concept / shared_tag label is worth an inter-KO edge."""
    norm = normalize_shared_label(label)
    if len(norm) < MIN_LABEL_LEN:
        return False
    if norm in GENERIC_SHARED_LABELS:
        return False
    # Artifact / export bookkeeping masquerading as concepts
    if norm.startswith("setv-") and ("inst-" in norm or "fam-" in norm or "evo-" in norm):
        return False
    if norm.startswith("export_contract") or norm.endswith("_v0"):
        return False
    return True


def allow_shared_fanout(count: int, *, kind: str) -> bool:
    """Reject ultra-common co-ownership that would form dense soft cliques."""
    if count < 2:
        return False
    if kind == "shared_tag":
        return count <= MAX_SHARED_TAG_FANOUT
    return count <= MAX_SHARED_CONCEPT_FANOUT
