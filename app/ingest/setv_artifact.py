"""SETV Artifact adapters — AE-2 six classes (Export Contract v0).

Cite-only · no LLM · no SETV mutation · no invented IDs.
Prefers OPEN SCHEMA sidecars / manifest when present.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from app import config
from app.knowledge.access import AccessBlock, default_policy_for
from app.knowledge.memory import EXPORT_CONTRACT_VERSION, SetvArtifactRef
from app.knowledge.taxonomy import TaxonomyBlock
from app.models import IngestedSource, KnowledgeUnit
from app.pipeline import PipelineResult
from app.storage.index import upsert_index
from app.storage.markdown import write_knowledge_unit

AssetClass = Literal[
    "snapshot",
    "evolution",
    "family",
    "measurement",
    "experiment",
    "uncertainty",
]

_FORBIDDEN = re.compile(
    r"\b(predict|forecast|alpha|buy|sell|entry|exit|ranking|promotion)\b",
    re.I,
)

_INST_ID_RE = re.compile(
    r"(?:Primary Instance id|Instance id|artifact_id)\s*:\s*(SETV-INST-[A-Z0-9_-]+)",
    re.I,
)
_FAM_ID_RE = re.compile(
    r"(?:Family\s*ID|artifact_id)\s*[:*]*\s*`?(SETV-FAM-[A-Z0-9_-]+)`?",
    re.I,
)
_FAM_ANY_RE = re.compile(r"\b(SETV-FAM-[A-Z0-9_-]+)\b", re.I)
_FAM_FROM_STEM = re.compile(r"^(SETV[_-]FAM[_-][A-Z0-9_-]+)", re.I)
_EDGE_ID_RE = re.compile(
    r"(?:^#\s*Edge\s*·\s*|Edge ID\s*:\s*|^\*\*ID:\*\*\s*)(L-(?:XS|SA|KP|KR|SF)-[A-Z0-9_-]+)",
    re.I | re.M,
)
_EDGE_FROM_NAME = re.compile(r"(L-(?:XS|SA|KP|KR|SF)-[A-Z0-9_-]+)", re.I)
_LINK_IDS_RE = re.compile(r"\b(SETV-(?:INST|FAM)-[A-Z0-9_-]+|L-(?:XS|SA|KP|KR|SF)-[A-Z0-9_-]+)\b")
_SYMBOL_RE = re.compile(r"Symbol\s*:\s*([A-Z0-9./]+)(?:\s*·\s*\S+)?", re.I)
_SYMBOL_TABLE_RE = re.compile(r"\|\s*Symbol\s*\|\s*\**([A-Z0-9./]+)\**", re.I)
_TF_RE = re.compile(r"Timeframe\s*:\s*([A-Za-z0-9]+)", re.I)
_WINDOW_RE = re.compile(r"Window\s*:\s*(.+)")
_STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*(.+)$", re.M)
_TYPE_RE = re.compile(r"^\*\*Type:\*\*\s*(.+)$", re.M)
_EVIDENCE_MD = re.compile(
    r"(?:methodology/|evidence/|[\w./-]*evidence/)?[\w./-]*EVIDENCE_[\w./-]+\.md",
    re.I,
)
_METHOD_PATH = re.compile(r"(methodology/[\w./-]+\.md)")


@dataclass
class ArtifactParse:
    artifact_id: str
    evidence_pointer: str
    asset_class: AssetClass
    symbol: str = ""
    timeframe: str = ""
    window: str = ""
    status: str = ""
    edge_type: str = ""
    evidence_paths: list[str] = field(default_factory=list)
    identity_lines: list[str] = field(default_factory=list)
    descriptive_points: list[str] = field(default_factory=list)
    link_ids: list[str] = field(default_factory=list)
    source_path: str = ""
    title_hint: str = ""


@dataclass
class ArtifactBatchResult:
    hits: list[Path] = field(default_factory=list)
    results: list[PipelineResult] = field(default_factory=list)
    skipped: list[tuple[Path, str]] = field(default_factory=list)


def _methodology_pointer(path: Path, setv_root: Path | None) -> str:
    posix = path.as_posix()
    if "methodology/" in posix:
        return posix[posix.index("methodology/") :]
    if setv_root is not None:
        try:
            rel = path.resolve().relative_to(setv_root.resolve()).as_posix()
            if "methodology/" in rel:
                return rel[rel.index("methodology/") :]
            return rel
        except ValueError:
            pass
    return posix


def _section_body(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"(?m)^{re.escape(heading)}\s*\n-+\n(.*?)(?=^[A-Za-z].*\n-+|\Z)",
        re.S,
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


def _md_section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"(?ms)^##\s+{re.escape(heading)}\s*\n(.*?)(?=^##\s+|\Z)",
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


def _clean_descriptive(lines: list[str]) -> list[str]:
    out: list[str] = []
    for raw in lines:
        line = raw.strip().lstrip("-*").strip()
        if not line or line.startswith("→") or line.startswith("Source:"):
            continue
        if line.startswith("[") and "](" in line:
            # keep link text lightly
            line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
        if _FORBIDDEN.search(line):
            continue
        if line.startswith("#"):
            continue
        out.append(line)
    return out


def _collect_evidence_paths(text: str) -> list[str]:
    found: list[str] = []
    for m in _METHOD_PATH.findall(text):
        if m not in found:
            found.append(m)
    for m in _EVIDENCE_MD.findall(text):
        norm = m
        if "methodology/" not in norm and "evidence/" in norm.lower():
            # leave as-is; often relative
            pass
        if norm not in found:
            found.append(norm)
    return found[:24]


# ----- Snapshot (Instance CARD) -------------------------------------------------

def discover_instance_cards(root: str | Path) -> list[Path]:
    root_p = Path(root).expanduser().resolve()
    if not root_p.is_dir():
        raise NotADirectoryError(f"not a directory: {root_p}")
    return sorted(root_p.rglob("CARD.md"))


def parse_instance_card(path: Path, *, setv_root: Path | None = None) -> ArtifactParse:
    text = path.read_text(encoding="utf-8", errors="replace")
    aid_m = _INST_ID_RE.search(text)
    if not aid_m:
        raise ValueError(f"no Primary Instance id / SETV-INST-* in {path}")
    artifact_id = aid_m.group(1).upper().replace("_", "-")
    family_ptr = ""
    for line in text.splitlines():
        if "Family / Inst card:" in line or "families/" in line.lower():
            m = re.search(r"(methodology/evidence/families/[\w./-]+\.md)", line)
            if m:
                family_ptr = m.group(1)
                break
    card_ptr = _methodology_pointer(path, setv_root)
    evidence_pointer = family_ptr or card_ptr

    identity = _section_body(text, "Identity")
    current = _section_body(text, "Current")
    residence = _section_body(text, "Residence")
    transition = _section_body(text, "Transition")
    status_sec = _section_body(text, "Status")
    status_m = _STATUS_RE.search(text)
    symbol_m = _SYMBOL_RE.search(text)
    tf_m = _TF_RE.search(text)
    window_m = _WINDOW_RE.search(text)

    evidence_paths = _collect_evidence_paths(text)
    if family_ptr and family_ptr not in evidence_paths:
        evidence_paths.insert(0, family_ptr)

    descriptive = _clean_descriptive(
        (current + "\n" + residence + "\n" + transition + "\n" + status_sec).splitlines()
    )
    return ArtifactParse(
        artifact_id=artifact_id,
        evidence_pointer=evidence_pointer,
        asset_class="snapshot",
        symbol=(symbol_m.group(1) if symbol_m else "").split("·")[0].strip(),
        timeframe=tf_m.group(1) if tf_m else "",
        window=window_m.group(1).strip() if window_m else "",
        status=(status_m.group(1).strip() if status_m else status_sec[:80]),
        evidence_paths=evidence_paths,
        identity_lines=_clean_descriptive(identity.splitlines())[:16],
        descriptive_points=descriptive[:24],
        link_ids=list(dict.fromkeys(_LINK_IDS_RE.findall(text)))[:16],
        source_path=str(path),
        title_hint=f"Snapshot · {artifact_id}",
    )


# ----- Family (SETV-FAM / L-XS / L-SF) ------------------------------------------

_FAMILY_EDGE_PREFIXES = ("L-XS-", "L-SF-")
_FAMILY_NAME_GLOB = ("SETV_FAM_*.md", "SETV-FAM-*.md")


def discover_family_artifacts(root: str | Path) -> list[Path]:
    root_p = Path(root).expanduser().resolve()
    if not root_p.is_dir():
        raise NotADirectoryError(f"not a directory: {root_p}")
    hits: list[Path] = []
    for pattern in _FAMILY_NAME_GLOB:
        hits.extend(root_p.rglob(pattern))
    for edge in root_p.rglob("L-*.md"):
        name = edge.name.upper()
        if name.startswith(_FAMILY_EDGE_PREFIXES) or name.startswith("L-XS-") or name.startswith("L-SF-"):
            hits.append(edge)
    # de-dupe
    seen: set[str] = set()
    out: list[Path] = []
    for p in sorted(hits):
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def parse_family_artifact(path: Path, *, setv_root: Path | None = None) -> ArtifactParse:
    text = path.read_text(encoding="utf-8", errors="replace")
    ptr = _methodology_pointer(path, setv_root)

    fam_m = _FAM_ID_RE.search(text) or _FAM_ANY_RE.search(text)
    edge_m = _EDGE_ID_RE.search(text) or _EDGE_FROM_NAME.search(path.name)
    stem_m = _FAM_FROM_STEM.search(path.stem)
    if fam_m:
        artifact_id = fam_m.group(1).upper().replace("_", "-")
    elif edge_m:
        artifact_id = edge_m.group(1).upper()
    elif stem_m:
        artifact_id = stem_m.group(1).upper().replace("_", "-")
    else:
        raise ValueError(f"no SETV-FAM-* / L-XS-* / L-SF-* id in {path}")

    type_m = _TYPE_RE.search(text)
    status_m = _STATUS_RE.search(text)
    symbol_m = _SYMBOL_RE.search(text) or _SYMBOL_TABLE_RE.search(text)
    window_m = _WINDOW_RE.search(text) or re.search(
        r"\|\s*Window\s*\|\s*(.+?)\s*\|", text, re.I
    )

    obs = _md_section(text, "Observation (not forecast)") or _md_section(text, "Observation")
    connects = _md_section(text, "Connects")
    question = _md_section(text, "Question")
    independent = _md_section(text, "Independent instances")
    underlying = _md_section(text, "Underlying identity (registry key)")

    descriptive = _clean_descriptive(
        (obs + "\n" + question + "\n" + independent + "\n" + underlying).splitlines()
    )[:24]
    identity = _clean_descriptive((connects + "\n" + underlying).splitlines())[:16]

    return ArtifactParse(
        artifact_id=artifact_id,
        evidence_pointer=ptr,
        asset_class="family",
        symbol=(symbol_m.group(1) if symbol_m else "").split("·")[0].strip(),
        window=window_m.group(1).strip() if window_m else "",
        status=(status_m.group(1).strip() if status_m else "")[:120],
        edge_type=(type_m.group(1).strip() if type_m else ""),
        evidence_paths=_collect_evidence_paths(text),
        identity_lines=identity,
        descriptive_points=descriptive,
        link_ids=list(dict.fromkeys(_LINK_IDS_RE.findall(text)))[:16],
        source_path=str(path),
        title_hint=f"Family · {artifact_id}",
    )


# ----- Evolution (L-SA / L-KP / L-KR / kernel Evidence) -------------------------

_EVOLUTION_EDGE_PREFIXES = ("L-SA-", "L-KP-", "L-KR-")
_EVOLUTION_EVIDENCE_TOKENS = ("KERNEL_PERSISTENCE", "KERNEL_STABILITY", "KERNEL_ROW_PERSISTENCE")


def discover_evolution_artifacts(root: str | Path) -> list[Path]:
    root_p = Path(root).expanduser().resolve()
    if not root_p.is_dir():
        raise NotADirectoryError(f"not a directory: {root_p}")
    hits: list[Path] = []
    for edge in root_p.rglob("L-*.md"):
        name = edge.name.upper()
        if any(name.startswith(p) for p in _EVOLUTION_EDGE_PREFIXES):
            hits.append(edge)
    for ev in root_p.rglob("EVIDENCE_*.md"):
        upper = ev.name.upper()
        if any(tok in upper for tok in _EVOLUTION_EVIDENCE_TOKENS):
            hits.append(ev)
    seen: set[str] = set()
    out: list[Path] = []
    for p in sorted(hits):
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def parse_evolution_artifact(path: Path, *, setv_root: Path | None = None) -> ArtifactParse:
    text = path.read_text(encoding="utf-8", errors="replace")
    ptr = _methodology_pointer(path, setv_root)

    edge_m = _EDGE_ID_RE.search(text) or _EDGE_FROM_NAME.search(path.name)
    inst_m = _INST_ID_RE.search(text)
    # Prefer edge id; else first INST id; else stem-based evidence id
    if edge_m:
        artifact_id = edge_m.group(1).upper()
    elif inst_m:
        artifact_id = inst_m.group(1).upper().replace("_", "-")
    else:
        stem = path.stem.upper()
        if stem.startswith("EVIDENCE_"):
            artifact_id = stem  # e.g. EVIDENCE_20260820_KERNEL_PERSISTENCE_OBSERVE
        else:
            raise ValueError(f"no evolution id (L-SA/KP/KR or SETV-INST or EVIDENCE_*) in {path}")

    type_m = _TYPE_RE.search(text)
    status_m = _STATUS_RE.search(text)
    symbol_m = _SYMBOL_RE.search(text)

    obs = _md_section(text, "Observation") or _md_section(text, "Observation (not forecast)")
    connects = _md_section(text, "Connects")
    question = _md_section(text, "Question")
    # Kernel evidence often uses numbered sections — grab first descriptive paragraphs
    if not obs:
        # take lines after first boxed/Question block lightly
        body = text.split("---", 2)[-1] if text.count("---") >= 2 else text
        obs = "\n".join(body.splitlines()[:40])

    descriptive = _clean_descriptive((obs + "\n" + question).splitlines())[:24]
    identity = _clean_descriptive(connects.splitlines())[:16]

    return ArtifactParse(
        artifact_id=artifact_id,
        evidence_pointer=ptr,
        asset_class="evolution",
        symbol=(symbol_m.group(1) if symbol_m else "").split("·")[0].strip(),
        status=(status_m.group(1).strip() if status_m else "")[:120],
        edge_type=(type_m.group(1).strip() if type_m else ""),
        evidence_paths=_collect_evidence_paths(text),
        identity_lines=identity,
        descriptive_points=descriptive,
        link_ids=list(dict.fromkeys(_LINK_IDS_RE.findall(text)))[:16],
        source_path=str(path),
        title_hint=f"Evolution · {artifact_id}",
    )


# ----- Measurement / Experiment / Uncertainty ---------------------------------

_EXP_ID_RE = re.compile(
    r"(?:Experiment\s*id|artifact_id)\s*[:*]*\s*`?(SETV-EXP-[A-Z0-9_-]+)`?",
    re.I,
)
_EXP_ANY_RE = re.compile(r"\b(SETV-EXP-[A-Z0-9_-]+)\b", re.I)
_MEASURE_STEM = re.compile(
    r"^(SETV_STATE_CONTRACT[A-Z0-9_-]*|DESIGN_SETV_STATE_CONTRACT[A-Z0-9_-]*|"
    r"SETV_STATE_REPRESENTATION[A-Z0-9_-]*)$",
    re.I,
)
_UNCERT_STEM = re.compile(
    r"^(DESIGN_SETV_UNCERTAINTY[A-Z0-9_-]*|OWNER_CONFIRM_[0-9]+_UNCERTAINTY[A-Z0-9_-]*)$",
    re.I,
)


def discover_measurement_artifacts(root: str | Path) -> list[Path]:
    root_p = Path(root).expanduser().resolve()
    hits: list[Path] = []
    for path in sorted(root_p.rglob("*.md")):
        name = path.name.upper()
        if "STATE_CONTRACT" in name or name.startswith("SETV_STATE_REPRESENTATION"):
            hits.append(path)
    return hits


def parse_measurement_artifact(
    path: Path, *, setv_root: Path | None = None
) -> ArtifactParse:
    text = path.read_text(encoding="utf-8", errors="replace")
    ptr = _methodology_pointer(path, setv_root)
    stem = path.stem
    if _MEASURE_STEM.match(stem) or "STATE_CONTRACT" in stem.upper():
        artifact_id = stem.upper().replace("-", "_")
    else:
        raise ValueError(f"no measurement contract id in {path}")
    status_m = _STATUS_RE.search(text)
    body = "\n".join(text.splitlines()[:50])
    descriptive = _clean_descriptive(body.splitlines())[:24]
    return ArtifactParse(
        artifact_id=artifact_id,
        evidence_pointer=ptr,
        asset_class="measurement",
        status=(status_m.group(1).strip() if status_m else "")[:120],
        evidence_paths=_collect_evidence_paths(text),
        identity_lines=[f"stem: {stem}"],
        descriptive_points=descriptive,
        source_path=str(path),
        title_hint=f"Measurement · {artifact_id}",
    )


def discover_experiment_artifacts(root: str | Path) -> list[Path]:
    root_p = Path(root).expanduser().resolve()
    hits: list[Path] = []
    for path in sorted(root_p.rglob("SETV_EXP_*.md")):
        if "DECLARATION_FROZEN" in path.name.upper():
            continue
        hits.append(path)
    return hits


def parse_experiment_artifact(
    path: Path, *, setv_root: Path | None = None
) -> ArtifactParse:
    text = path.read_text(encoding="utf-8", errors="replace")
    ptr = _methodology_pointer(path, setv_root)
    exp_m = _EXP_ID_RE.search(text) or _EXP_ANY_RE.search(text)
    if exp_m:
        artifact_id = exp_m.group(1).upper().replace("_", "-")
    else:
        stem = path.stem.upper().replace("_", "-")
        if not stem.startswith("SETV-EXP-"):
            raise ValueError(f"no SETV-EXP-* id in {path}")
        artifact_id = stem
    status_m = _STATUS_RE.search(text)
    symbol_m = _SYMBOL_RE.search(text) or re.search(
        r"SETV-EXP-([A-Z0-9]+)-", artifact_id, re.I
    )
    symbol = ""
    if symbol_m:
        symbol = symbol_m.group(1) if symbol_m.lastindex else ""
        # from Experiment id capture group of symbol
        m2 = re.match(r"SETV-EXP-([A-Z0-9]+)-", artifact_id, re.I)
        if m2:
            symbol = m2.group(1)
    decl = _md_section(text, "Declaration (FROZEN)") or _md_section(text, "Declaration")
    headline = _md_section(text, "Headline metrics (LOO NLL bits)")
    descriptive = _clean_descriptive((decl + "\n" + headline).splitlines())[:24]
    return ArtifactParse(
        artifact_id=artifact_id,
        evidence_pointer=ptr,
        asset_class="experiment",
        symbol=symbol,
        status=(status_m.group(1).strip() if status_m else "")[:120],
        evidence_paths=_collect_evidence_paths(text),
        identity_lines=_clean_descriptive(decl.splitlines())[:8],
        descriptive_points=descriptive,
        link_ids=list(dict.fromkeys(_LINK_IDS_RE.findall(text)))[:16],
        source_path=str(path),
        title_hint=f"Experiment · {artifact_id}",
    )


def discover_uncertainty_artifacts(root: str | Path) -> list[Path]:
    root_p = Path(root).expanduser().resolve()
    hits: list[Path] = []
    for path in sorted(root_p.rglob("*.md")):
        name = path.name.upper()
        if "UNCERTAINTY" in name and (
            name.startswith("DESIGN_")
            or name.startswith("OWNER_CONFIRM_")
            or name.startswith("EVIDENCE_")
        ):
            hits.append(path)
    return hits


def parse_uncertainty_artifact(
    path: Path, *, setv_root: Path | None = None
) -> ArtifactParse:
    text = path.read_text(encoding="utf-8", errors="replace")
    ptr = _methodology_pointer(path, setv_root)
    stem = path.stem
    if _UNCERT_STEM.match(stem) or "UNCERTAINTY" in stem.upper():
        artifact_id = stem.upper().replace("-", "_")
    else:
        raise ValueError(f"no uncertainty document id in {path}")
    status_m = _STATUS_RE.search(text)
    issued = _md_section(text, "0. What this round issues") or "\n".join(
        text.splitlines()[:40]
    )
    descriptive = _clean_descriptive(issued.splitlines())[:24]
    return ArtifactParse(
        artifact_id=artifact_id,
        evidence_pointer=ptr,
        asset_class="uncertainty",
        status=(status_m.group(1).strip() if status_m else "")[:120],
        evidence_paths=_collect_evidence_paths(text),
        identity_lines=[f"stem: {stem}"],
        descriptive_points=descriptive,
        source_path=str(path),
        title_hint=f"Uncertainty · {artifact_id}",
    )


# ----- Shared unit builder ------------------------------------------------------

_CLASS_LABEL = {
    "snapshot": "State Snapshot",
    "evolution": "State Evolution",
    "family": "State Family",
    "measurement": "Measurement Knowledge",
    "experiment": "Experiment Evidence",
    "uncertainty": "Uncertainty Knowledge",
}

_DEST_LEAF = {
    "snapshot": "snapshots",
    "evolution": "evolutions",
    "family": "families",
    "measurement": "measurements",
    "experiment": "experiments",
    "uncertainty": "uncertainties",
}


def unit_from_artifact(
    parsed: ArtifactParse,
    *,
    setv_root: str | Path | None = None,
) -> KnowledgeUnit:
    label = _CLASS_LABEL[parsed.asset_class]
    title = f"SETV {label} · {parsed.artifact_id}"
    if parsed.symbol:
        title = f"SETV {label} · {parsed.symbol} · {parsed.artifact_id}"

    summary_parts = [
        f"{label} cite of {parsed.artifact_id} (observed / archival).",
    ]
    if parsed.window:
        summary_parts.append(f"Window: {parsed.window}.")
    if parsed.status:
        summary_parts.append(f"Status: {parsed.status}.")
    if parsed.edge_type:
        summary_parts.append(f"Type: {parsed.edge_type}.")
    summary_parts.append(
        "Consumer cite-only under setv_artifact_export_v0 — does not mutate SETV."
    )

    concepts = [
        c
        for c in [
            parsed.symbol,
            parsed.timeframe,
            label,
            "SETV",
            parsed.artifact_id,
            parsed.edge_type,
        ]
        if c
    ]
    key_points = list(parsed.identity_lines[:8]) + list(parsed.descriptive_points[:12])
    claims = [
        f"[observed] {p}"
        for p in parsed.descriptive_points[:10]
        if not _FORBIDDEN.search(p)
    ]
    evidence = list(parsed.evidence_paths) or [parsed.evidence_pointer]
    relationships = [f"Atlas link {lid}" for lid in parsed.link_ids[:8]]

    tax_path = ["专有知识", "SETV", label]
    if parsed.symbol:
        tax_path.append(parsed.symbol)
    if parsed.timeframe:
        tax_path.append(parsed.timeframe)

    digest = hashlib.sha1(
        f"{parsed.asset_class}:{parsed.artifact_id}".encode("utf-8")
    ).hexdigest()[:12]

    tag_class = parsed.asset_class.replace("_", "-")
    return KnowledgeUnit(
        id=digest,
        title=title,
        source=parsed.source_path,
        type="md",
        summary=" ".join(summary_parts),
        concepts=concepts,
        key_points=key_points,
        claims=claims,
        evidence=evidence,
        relationships=relationships,
        unknowns=[
            "KF must not reinterpret State axes or invent Forecast claims from this cite.",
        ],
        tags=[
            "setv",
            f"state-{tag_class}",
            "memory-state",
            "ecosystem-ingest",
            "cite-only",
            "restricted-setv",
            parsed.artifact_id.lower(),
        ],
        access=AccessBlock(
            classification="restricted",
            source_project="setv",
            export_policy="local_only",
            policy=default_policy_for("restricted"),
        ),
        taxonomy=TaxonomyBlock(path=tax_path),
        memory_kind="state",
        setv_artifact=SetvArtifactRef(
            artifact_id=parsed.artifact_id,
            evidence_pointer=parsed.evidence_pointer,
            export_contract_version=EXPORT_CONTRACT_VERSION,
            asset_class=parsed.asset_class,  # type: ignore[arg-type]
            setv_root=str(setv_root or ""),
        ),
    )


def _parse_for_class(
    path: Path,
    asset_class: AssetClass,
    *,
    setv_root: Path | None,
) -> ArtifactParse:
    if asset_class == "snapshot":
        return parse_instance_card(path, setv_root=setv_root)
    if asset_class == "family":
        return parse_family_artifact(path, setv_root=setv_root)
    if asset_class == "evolution":
        return parse_evolution_artifact(path, setv_root=setv_root)
    if asset_class == "measurement":
        return parse_measurement_artifact(path, setv_root=setv_root)
    if asset_class == "experiment":
        return parse_experiment_artifact(path, setv_root=setv_root)
    if asset_class == "uncertainty":
        return parse_uncertainty_artifact(path, setv_root=setv_root)
    raise ValueError(f"unsupported asset_class {asset_class!r}")


def _discover_for_class(root: Path, asset_class: AssetClass) -> list[Path]:
    """Prefer OPEN KF INGEST sidecars when present; else markdown scrape sources."""
    sidecars: list[Path] = []
    if asset_class == "snapshot":
        sidecars.extend(sorted(root.rglob("export.json")))
        if sidecars:
            return sidecars
        return discover_instance_cards(root)
    if asset_class == "family":
        sidecars.extend(sorted(root.rglob("export_family.json")))
        for p in sorted(root.rglob("L-*.export.json")):
            try:
                parsed = parse_export_sidecar(p)
            except Exception:  # noqa: BLE001
                continue
            if parsed.asset_class == "family":
                sidecars.append(p)
        if sidecars:
            seen: set[str] = set()
            out: list[Path] = []
            for p in sidecars:
                k = str(p)
                if k in seen:
                    continue
                seen.add(k)
                out.append(p)
            return out
        return discover_family_artifacts(root)
    if asset_class == "evolution":
        sidecars.extend(sorted(root.rglob("export_evolution.json")))
        for p in sorted(root.rglob("L-*.export.json")):
            try:
                parsed = parse_export_sidecar(p)
            except Exception:  # noqa: BLE001
                continue
            if parsed.asset_class == "evolution":
                sidecars.append(p)
        if sidecars:
            seen = set()
            out = []
            for p in sidecars:
                k = str(p)
                if k in seen:
                    continue
                seen.add(k)
                out.append(p)
            return out
        return discover_evolution_artifacts(root)
    if asset_class == "measurement":
        return discover_measurement_artifacts(root)
    if asset_class == "experiment":
        return discover_experiment_artifacts(root)
    if asset_class == "uncertainty":
        return discover_uncertainty_artifacts(root)
    return []


def ingest_artifact(
    path: str | Path,
    *,
    asset_class: AssetClass | None = None,
    setv_root: str | Path | None = None,
    dest_dir: Path | None = None,
    index: bool | None = None,
    dry_run: bool = False,
    parsed: ArtifactParse | None = None,
) -> PipelineResult | ArtifactParse:
    path_p = Path(path).expanduser().resolve()
    if not path_p.is_file():
        raise FileNotFoundError(path_p)
    root = Path(setv_root).expanduser().resolve() if setv_root else None
    if parsed is None:
        if is_export_sidecar(path_p):
            parsed = parse_export_sidecar(path_p, setv_root=root)
        else:
            if asset_class is None:
                raise ValueError(
                    f"asset_class required for non-sidecar ingest: {path_p}"
                )
            parsed = _parse_for_class(path_p, asset_class, setv_root=root)
    use_class: AssetClass = parsed.asset_class
    if asset_class is not None and asset_class != use_class and not is_export_sidecar(path_p):
        # explicit class wins for markdown scrape path
        parsed = _parse_for_class(path_p, asset_class, setv_root=root)
        use_class = asset_class
    if dry_run:
        return parsed
    unit = unit_from_artifact(parsed, setv_root=root)
    dest = dest_dir or (
        config.KNOWLEDGE_DIR / "restricted" / "setv" / _DEST_LEAF[use_class]
    )
    stem = f"{use_class}_{parsed.artifact_id.lower().replace('-', '_')}"
    md_path = write_knowledge_unit(unit, dest_dir=dest, filename_stem=stem)
    do_index = config.INDEX_ENABLED if index is None else index
    if do_index:
        upsert_index(unit, str(md_path), source_path=str(path_p))
    source = IngestedSource(
        source_type="md",
        title=unit.title,
        text=path_p.read_text(encoding="utf-8", errors="replace")[:4000],
        path=str(path_p),
        metadata={
            "artifact_id": parsed.artifact_id,
            "memory_kind": "state",
            "asset_class": use_class,
            "ingest_via": "sidecar" if is_export_sidecar(path_p) else "markdown",
        },
    )
    return PipelineResult(
        source=source,
        unit=unit,
        markdown_path=md_path,
        raw_path=path_p,
        truncated=False,
    )


def run_artifact_ingest(
    paths: list[str | Path],
    *,
    asset_class: AssetClass,
    setv_root: str | Path | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    index: bool | None = None,
) -> ArtifactBatchResult:
    batch = ArtifactBatchResult()
    files: list[Path] = []
    for raw in paths:
        p = Path(raw).expanduser().resolve()
        if p.is_dir():
            files.extend(_discover_for_class(p, asset_class))
        elif p.is_file():
            files.append(p)
        else:
            batch.skipped.append((p, "missing"))
    seen: set[str] = set()
    uniq: list[Path] = []
    for f in files:
        key = str(f)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(f)
    if limit is not None:
        uniq = uniq[: max(0, limit)]
    batch.hits = list(uniq)
    if dry_run:
        return batch
    for path in uniq:
        try:
            result = ingest_artifact(
                path,
                asset_class=asset_class,
                setv_root=setv_root,
                index=index,
                dry_run=False,
            )
            assert isinstance(result, PipelineResult)
            batch.results.append(result)
        except Exception as exc:  # noqa: BLE001
            batch.skipped.append((path, str(exc)))
    return batch


# Backward-compatible aliases used by snapshot CLI / tests
SnapshotParse = ArtifactParse
SnapshotBatchResult = ArtifactBatchResult


def unit_from_snapshot(parsed: ArtifactParse, *, setv_root: str | Path | None = None) -> KnowledgeUnit:
    return unit_from_artifact(parsed, setv_root=setv_root)


def ingest_snapshot_card(
    path: str | Path,
    *,
    setv_root: str | Path | None = None,
    dest_dir: Path | None = None,
    index: bool | None = None,
    dry_run: bool = False,
) -> PipelineResult | ArtifactParse:
    return ingest_artifact(
        path,
        asset_class="snapshot",
        setv_root=setv_root,
        dest_dir=dest_dir,
        index=index,
        dry_run=dry_run,
    )


def run_snapshot_ingest(
    paths: list[str | Path],
    *,
    setv_root: str | Path | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    index: bool | None = None,
) -> ArtifactBatchResult:
    return run_artifact_ingest(
        paths,
        asset_class="snapshot",
        setv_root=setv_root,
        limit=limit,
        dry_run=dry_run,
        index=index,
    )


# ----- OPEN KF INGEST · sidecar / manifest -------------------------------------

_SIDECAR_NAMES = {
    "export.json": "snapshot",
    "export_family.json": "family",
    "export_evolution.json": "evolution",
}
_SIDECAR_REQUIRED = (
    "artifact_id",
    "evidence_pointer",
    "export_contract_version",
    "asset_class",
)


def is_export_sidecar(path: Path) -> bool:
    name = path.name
    if name in _SIDECAR_NAMES:
        return True
    return name.endswith(".export.json") and name.startswith("L-")


def parse_export_sidecar(path: Path, *, setv_root: Path | None = None) -> ArtifactParse:
    """Parse SETV export sidecar JSON (preferred under OPEN KF INGEST)."""
    import json

    path_p = Path(path).expanduser().resolve()
    data = json.loads(path_p.read_text(encoding="utf-8"))
    for key in _SIDECAR_REQUIRED:
        if key not in data:
            raise ValueError(f"sidecar missing {key}: {path_p}")
    asset_class = str(data["asset_class"]).strip().lower()
    if asset_class not in _DEST_LEAF:
        raise ValueError(f"unsupported asset_class {asset_class!r} in {path_p}")
    artifact_id = str(data["artifact_id"]).strip()
    evidence_pointer = str(data["evidence_pointer"]).strip()
    evidence_paths = [str(p) for p in (data.get("evidence_paths") or []) if p]
    if evidence_pointer and evidence_pointer not in evidence_paths:
        evidence_paths.insert(0, evidence_pointer)
    identity = []
    for label, key in (
        ("Symbol", "symbol"),
        ("Timeframe", "timeframe"),
        ("Window", "window"),
        ("Status", "status"),
        ("Card", "card_path"),
    ):
        val = data.get(key)
        if val:
            identity.append(f"{label}: {val}")
    return ArtifactParse(
        artifact_id=artifact_id,
        evidence_pointer=evidence_pointer,
        asset_class=asset_class,  # type: ignore[arg-type]
        symbol=str(data.get("symbol") or ""),
        timeframe=str(data.get("timeframe") or ""),
        window=str(data.get("window") or ""),
        status=str(data.get("status") or "")[:160],
        evidence_paths=evidence_paths[:24],
        identity_lines=identity[:16],
        descriptive_points=[
            f"Export sidecar cite · contract {data.get('export_contract_version')}",
            f"Prefer sidecar under OPEN KF INGEST · source {path_p.name}",
        ],
        link_ids=[],
        source_path=str(path_p),
        title_hint=f"{asset_class} · {artifact_id}",
    )


def load_manifest_entries(
    manifest_path: str | Path,
    *,
    asset_class: AssetClass | None = None,
) -> list[dict]:
    import json

    path = Path(manifest_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    entries: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if asset_class and row.get("asset_class") != asset_class:
            continue
        entries.append(row)
    return entries


def resolve_manifest_sidecar(
    entry: dict,
    *,
    setv_root: Path,
) -> Path:
    rel = entry.get("sidecar_path") or ""
    if not rel:
        raise ValueError(f"manifest entry missing sidecar_path: {entry!r}")
    path = (setv_root / rel).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def ingest_export_sidecar(
    path: str | Path,
    *,
    setv_root: str | Path | None = None,
    dest_dir: Path | None = None,
    index: bool | None = None,
    dry_run: bool = False,
) -> PipelineResult | ArtifactParse:
    path_p = Path(path).expanduser().resolve()
    root = Path(setv_root).expanduser().resolve() if setv_root else None
    parsed = parse_export_sidecar(path_p, setv_root=root)
    if dry_run:
        return parsed
    return ingest_artifact(
        path_p,
        asset_class=parsed.asset_class,
        setv_root=setv_root,
        dest_dir=dest_dir,
        index=index,
        dry_run=False,
        parsed=parsed,
    )


def run_manifest_ingest(
    *,
    setv_root: str | Path,
    manifest: str | Path | None = None,
    asset_class: AssetClass | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    index: bool | None = None,
) -> ArtifactBatchResult:
    """OPEN KF INGEST · preferred path via SETV manifest_v0.jsonl → sidecars."""
    root = Path(setv_root).expanduser().resolve()
    man = (
        Path(manifest).expanduser().resolve()
        if manifest
        else root / "methodology" / "SETV" / "export" / "manifest_v0.jsonl"
    )
    batch = ArtifactBatchResult()
    entries = load_manifest_entries(man, asset_class=asset_class)
    if limit is not None:
        entries = entries[: max(0, limit)]
    files: list[Path] = []
    for entry in entries:
        try:
            files.append(resolve_manifest_sidecar(entry, setv_root=root))
        except (FileNotFoundError, ValueError) as exc:
            batch.skipped.append((Path(str(entry.get("sidecar_path"))), str(exc)))
    batch.hits = list(files)
    if dry_run:
        return batch
    for path in files:
        try:
            result = ingest_export_sidecar(
                path,
                setv_root=root,
                index=index,
                dry_run=False,
            )
            assert isinstance(result, PipelineResult)
            batch.results.append(result)
        except Exception as exc:  # noqa: BLE001
            batch.skipped.append((path, str(exc)))
    return batch
