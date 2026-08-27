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
from app.knowledge.access import is_compose_eligible
from app.retrieve import run_query


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


def compose_from_query(
    query: str,
    *,
    kind: str = "paper",
    top_k: int = 5,
    graph_path: str | None = None,
    graph_weight: float = 0.35,
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
    )
    hits = retrieved.result.hits
    if not hits:
        raise RuntimeError("retrieve returned no KnowledgeObjects")

    provider = config.LLM_PROVIDER
    eligible_hits = [
        h for h in hits if is_compose_eligible(h.classification, llm_provider=provider)
    ]
    blocked = [h for h in hits if h not in eligible_hits]
    if blocked:
        labels = ", ".join(f"{h.ko_id}({h.classification})" for h in blocked[:5])
        print(f"[compose] access filter blocked {len(blocked)} KO(s): {labels}", flush=True)
    hits = eligible_hits
    if not hits:
        raise RuntimeError(
            f"no compose-eligible KnowledgeObjects for provider={provider} "
            "(secret never allowed; restricted blocked for cloud LLM)"
        )

    packs: list[dict] = []
    sources: list[ComposeSourceHit] = []
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
            )
        )

    system = PAPER_SYSTEM if kind == "paper" else LECTURE_SYSTEM
    user = build_compose_user_prompt(kind=kind, query=query, packs=packs)
    print(f"[compose] llm provider={config.LLM_PROVIDER} kind={kind}", flush=True)
    raw = complete_json(system, user)
    payload = extract_json_object(raw)

    meta = ComposeResultMeta(
        kind=kind,  # type: ignore[arg-type]
        query=query,
        sources=sources,
        llm_provider=config.LLM_PROVIDER,
        retrieve_mode=retrieved.result.mode,
        evidence={
            "pipeline": "compose_v0.1",
            "retrieve_version": retrieved.result.retrieve_version,
            "graph_id": retrieved.result.evidence.get("graph_id"),
            "top_k": top_k,
            "hit_count": len(hits),
            "unit": "knowledge_object",
        },
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
        retrieve_path=retrieved.result_path,
        meta=meta,
        payload=payload,
    )
