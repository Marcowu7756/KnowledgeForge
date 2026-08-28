from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app import config
from app.compression.llm import complete_json
from app.compression.parse import extract_json_object
from app.compose.models import ComposeResultMeta, ComposeSourceHit
from app.compose.prompt import (
    LECTURE_SYSTEM,
    PAPER_SYSTEM,
    build_compose_user_prompt,
)
from app.compose.render import render_lecture, render_paper
from app.compose.validate import ComposePayloadError, validate_compose_payload
from app.knowledge.access import is_compose_eligible, resolve_policy
from app.knowledge.parse import load_unit_from_markdown
from app.knowledge.path_access import resolve_access_for_path
from app.retrieve import run_query
from app.retrieve.models import RetrieveHit


@dataclass
class ComposeResult:
    kind: str
    query: str
    output_dir: Path
    draft_path: Path
    meta_path: Path
    retrieve_path: Path | None
    meta: ComposeResultMeta
    payload: dict


def _load_card_text(path: str) -> str:
    if not path:
        return ""
    p = Path(path)
    if not p.is_file():
        alt = config.ROOT / path
        p = alt if alt.is_file() else p
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8", errors="ignore")


def _resolve_card_path(raw: str) -> Path:
    p = Path(raw)
    if not p.is_absolute():
        p = (config.ROOT / p).resolve()
    else:
        p = p.resolve()
    if not p.is_file():
        raise FileNotFoundError(f"card not found: {raw}")
    try:
        p.relative_to(config.DATA_DIR.resolve())
    except ValueError as exc:
        raise PermissionError(f"compose sources must stay under data/: {raw}") from exc
    return p


def _hits_from_paths(paths: list[str]) -> list[RetrieveHit]:
    hits: list[RetrieveHit] = []
    for i, raw in enumerate(paths):
        path = _resolve_card_path(raw)
        unit = load_unit_from_markdown(path)
        access = resolve_access_for_path(path)
        policy = access.resolved_policy().model_dump()
        try:
            rel = str(path.relative_to(config.ROOT.resolve()))
        except ValueError:
            rel = str(path)
        hits.append(
            RetrieveHit(
                ko_id=f"ko_{unit.id}" if not str(unit.id).startswith("ko_") else str(unit.id),
                title=unit.title,
                score=1.0 - (i * 0.01),
                semantic_score=1.0 - (i * 0.01),
                path=rel,
                concepts=list(unit.concepts[:12]),
                tags=list(unit.tags[:8]),
                summary=unit.summary or "",
                why=["h1b_selected_source"],
                classification=access.classification,
                access_policy=policy,
            )
        )
    return hits


def _filter_compose_hits(
    hits: list[RetrieveHit],
    *,
    query: str,
    access_lane: str | None,
) -> list[RetrieveHit]:
    provider = config.LLM_PROVIDER
    eligible_hits = [
        h
        for h in hits
        if is_compose_eligible(
            h.classification,
            llm_provider=provider,
            policy=resolve_policy(h.classification, h.access_policy),
        )
    ]
    blocked = [h for h in hits if h not in eligible_hits]
    try:
        from app.knowledge.access_audit import record_compose_filter

        record_compose_filter(
            query=query,
            lane=access_lane,
            llm_provider=provider,
            allowed_ids=[h.ko_id for h in eligible_hits],
            blocked=[(h.ko_id, h.classification) for h in blocked],
        )
    except Exception:
        pass
    if blocked:
        labels = ", ".join(f"{h.ko_id}({h.classification})" for h in blocked[:5])
        print(f"[compose] access filter blocked {len(blocked)} KO(s): {labels}", flush=True)
    if not eligible_hits:
        raise RuntimeError(
            f"no compose-eligible KnowledgeObjects for provider={provider} "
            "(secret never allowed; restricted blocked for cloud LLM)"
        )
    return eligible_hits


def _compose_from_hits(
    query: str,
    hits: list[RetrieveHit],
    *,
    kind: str,
    access_lane: str | None,
    retrieve_mode: str,
    retrieve_path: Path | None,
    evidence_extra: dict | None = None,
) -> ComposeResult:
    packs: list[dict] = []
    sources: list[ComposeSourceHit] = []
    max_class = "public"
    order = {"public": 0, "internal": 1, "restricted": 2, "secret": 3}
    for hit in hits:
        card = _load_card_text(hit.path)
        packs.append(
            {
                "ko_id": hit.ko_id,
                "title": hit.title,
                "score": hit.score,
                "concepts": hit.concepts,
                "summary": hit.summary,
                "card_text": card or hit.summary,
            }
        )
        sources.append(
            ComposeSourceHit(
                ko_id=hit.ko_id,
                title=hit.title,
                score=hit.score,
                path=hit.path,
                classification=hit.classification,
            )
        )
        if order.get(hit.classification, 0) > order.get(max_class, 0):
            max_class = hit.classification

    system = PAPER_SYSTEM if kind == "paper" else LECTURE_SYSTEM
    user = build_compose_user_prompt(kind=kind, query=query, packs=packs)
    print(f"[compose] llm provider={config.LLM_PROVIDER} kind={kind}", flush=True)
    raw = complete_json(system, user)
    payload = extract_json_object(raw)

    evidence = {
        "pipeline": "compose_v0.1",
        "hit_count": len(hits),
        "unit": "knowledge_object",
        "access_lane": access_lane or "general",
        "max_source_classification": max_class,
    }
    if evidence_extra:
        evidence.update(evidence_extra)

    meta = ComposeResultMeta(
        kind=kind,  # type: ignore[arg-type]
        query=query,
        sources=sources,
        llm_provider=config.LLM_PROVIDER,
        retrieve_mode=retrieve_mode,  # type: ignore[arg-type]
        evidence=evidence,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = config.COMPOSE_DIR / f"{stamp}_{uuid4().hex[:8]}"
    out.mkdir(parents=True, exist_ok=True)

    try:
        validate_compose_payload(kind, payload)
    except ComposePayloadError as exc:
        fail_path = out / "FAILED.md"
        fail_body = "\n".join(
            [
                f"# Compose FAILED — {kind}",
                "",
                f"query: {query}",
                "",
                "## Validation errors",
                "",
                *[f"- {line}" for line in str(exc).splitlines()],
                "",
                "## Raw payload",
                "",
                "```json",
                __import__("json").dumps(payload, ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
        fail_path.write_text(fail_body, encoding="utf-8")
        meta.evidence = {**(meta.evidence or {}), "status": "failed", "errors": str(exc)}
        meta_path = out / "compose.json"
        meta_path.write_text(meta.model_dump_json(indent=2) + "\n", encoding="utf-8")
        (out / "payload.json").write_text(
            __import__("json").dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        raise ComposePayloadError(
            f"compose payload invalid — see {fail_path}"
        ) from exc

    draft = render_paper(payload, meta) if kind == "paper" else render_lecture(payload, meta)
    draft_path = out / ("PAPER.md" if kind == "paper" else "LECTURE.md")
    draft_path.write_text(draft, encoding="utf-8")
    meta_path = out / "compose.json"
    meta_path.write_text(meta.model_dump_json(indent=2) + "\n", encoding="utf-8")
    (out / "payload.json").write_text(
        __import__("json").dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return ComposeResult(
        kind=kind,
        query=query,
        output_dir=out,
        draft_path=draft_path,
        meta_path=meta_path,
        retrieve_path=retrieve_path,
        meta=meta,
        payload=payload,
    )


def compose_from_query(
    query: str,
    *,
    kind: str = "paper",
    top_k: int = 5,
    graph_path: str | None = None,
    graph_weight: float = 0.35,
    access_lane: str | None = None,
) -> ComposeResult:
    """P3 application: retrieve KOs → LLM → paper/lecture draft."""
    kind = kind.strip().lower()
    if kind not in {"paper", "lecture"}:
        raise ValueError("kind must be paper|lecture")

    retrieved = run_query(
        query,
        top_k=top_k,
        graph_path=graph_path,
        graph_weight=graph_weight,
        save=True,
        access_lane=access_lane,
    )
    hits = retrieved.result.hits
    if not hits:
        raise RuntimeError("retrieve returned no KnowledgeObjects")

    hits = _filter_compose_hits(hits, query=query, access_lane=access_lane)
    return _compose_from_hits(
        query,
        hits,
        kind=kind,
        access_lane=access_lane,
        retrieve_mode=retrieved.result.mode,
        retrieve_path=retrieved.result_path,
        evidence_extra={
            "retrieve_version": retrieved.result.retrieve_version,
            "graph_id": retrieved.result.evidence.get("graph_id"),
            "top_k": top_k,
            "source_mode": "retrieve",
        },
    )


def compose_from_paths(
    query: str,
    paths: list[str],
    *,
    kind: str = "lecture",
    access_lane: str | None = None,
) -> ComposeResult:
    """H1b: compose from an explicit ordered list of KO card paths (skip retrieve)."""
    kind = kind.strip().lower()
    if kind not in {"paper", "lecture"}:
        raise ValueError("kind must be paper|lecture")
    if not paths:
        raise ValueError("paths required")

    hits = _hits_from_paths(paths)
    hits = _filter_compose_hits(hits, query=query, access_lane=access_lane)
    return _compose_from_hits(
        query,
        hits,
        kind=kind,
        access_lane=access_lane,
        retrieve_mode="semantic",  # schema Literal; evidence.source_mode marks selection
        retrieve_path=None,
        evidence_extra={
            "top_k": len(hits),
            "source_mode": "h1b_selected_paths",
            "selected_paths": list(paths),
        },
    )
