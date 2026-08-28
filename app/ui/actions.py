"""UI action runners shared by sync endpoints and async jobs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app import config
from app.ui.jobs import ProgressFn, wait_briefly


def run_capture(kind: str, target: str, progress: ProgressFn | None = None) -> dict[str, Any]:
    def p(pct: int, msg: str) -> None:
        if progress:
            progress(pct, msg)

    target = target.strip()
    if not target:
        raise ValueError("target required")
    p(10, "preparing ingest")
    wait_briefly()
    p(35, f"running {kind}")
    if kind == "youtube":
        from app.pipeline import run_youtube

        result = run_youtube(target)
    elif kind == "bilibili":
        from app.pipeline import run_bilibili

        result = run_bilibili(target)
    elif kind == "twitter":
        from app.pipeline import run_twitter

        result = run_twitter(target)
    elif kind == "audio":
        from app.pipeline import run_audio

        result = run_audio(target)
    elif kind == "image":
        from app.pipeline import run_image

        result = run_image(target)
    else:
        from app.pipeline import run_file

        result = run_file(target)
    p(90, "writing knowledge card")
    out = {
        "ok": True,
        "title": result.unit.title,
        "knowledge": str(result.markdown_path),
        "raw": str(result.raw_path),
        "concepts": len(result.unit.concepts),
    }
    p(100, "done")
    return out


def run_compile(
    path: str,
    *,
    from_card: bool = True,
    animate: bool = False,
    narrate: bool = False,
    fast: bool = True,
    progress: ProgressFn | None = None,
) -> dict[str, Any]:
    def p(pct: int, msg: str) -> None:
        if progress:
            progress(pct, msg)

    from app.harness import compile_knowledge

    card = Path(path).expanduser()
    if not card.is_file():
        alt = config.ROOT / path
        card = alt if alt.is_file() else card
    if not card.is_file():
        raise FileNotFoundError(f"card not found: {path}")
    p(10, "compile starting")
    wait_briefly()
    p(30, "distilling KnowledgeObject")
    pkg = compile_knowledge(
        str(card),
        from_card=from_card,
        animate=animate,
        narrate=narrate,
        fast=fast,
    )
    p(90, "writing package")
    detail = {}
    for key in ("package_dir", "manifest_path", "knowledge_object_path", "knowledge_md"):
        val = getattr(pkg, key, None)
        if val is not None:
            detail[key] = str(val)
    out = {"ok": True, "package": str(getattr(pkg, "package_dir", "")), "detail": detail}
    p(100, "done")
    return out


def run_reconstruct_action(
    *,
    from_index: bool = True,
    view: str = "theme",
    evolve_dir: str | None = None,
    progress: ProgressFn | None = None,
) -> dict[str, Any]:
    def p(pct: int, msg: str) -> None:
        if progress:
            progress(pct, msg)

    from app.reconstruct import run_reconstruct

    p(15, "loading KnowledgeObjects")
    wait_briefly()
    p(45, "building concept graph")
    result = run_reconstruct(
        from_index=from_index,
        view=view,
        evolve_dir=evolve_dir,
    )
    p(85, "writing view")
    g = getattr(result, "graph", None)
    out: dict[str, Any] = {
        "ok": True,
        "result": {
            "output_dir": str(getattr(result, "output_dir", "") or ""),
            "graph_path": str(getattr(result, "graph_path", "") or ""),
            "view_path": str(getattr(result, "view_path", "") or ""),
            "report_path": str(getattr(result, "report_path", "") or ""),
            "kos": len(getattr(result, "kos", []) or []),
        },
    }
    if g is not None:
        stats = getattr(getattr(g, "relations", None), "stats", {}) or {}
        out["result"]["graph_id"] = getattr(g, "id", "")
        out["result"]["nodes"] = stats.get("nodes", len(getattr(g, "nodes", []) or []))
        out["result"]["edges"] = stats.get(
            "edges", len(getattr(getattr(g, "relations", None), "edges", []) or [])
        )
    p(100, "done")
    return out


def run_retrieve_action(
    query: str,
    *,
    top_k: int = 5,
    graph_path: str | None = None,
    access_lane: str = "general",
    progress: ProgressFn | None = None,
) -> dict[str, Any]:
    def p(pct: int, msg: str) -> None:
        if progress:
            progress(pct, msg)

    from app.retrieve import run_query

    p(20, "embedding query")
    wait_briefly()
    p(55, f"ranking KnowledgeObjects [{access_lane}]")
    run = run_query(
        query,
        top_k=top_k,
        graph_path=graph_path,
        save=True,
        access_lane=access_lane,
    )
    hits = [
        {
            "ko_id": h.ko_id,
            "title": h.title,
            "score": h.score,
            "semantic_score": h.semantic_score,
            "graph_score": h.graph_score,
            "path": h.path,
            "classification": h.classification,
            "why": h.why,
        }
        for h in run.result.hits
    ]
    out = {
        "ok": True,
        "mode": run.result.mode,
        "access_lane": access_lane,
        "hits": hits,
        "result_path": str(run.result_path) if run.result_path else None,
    }
    p(100, "done")
    return out


def run_compose_action(
    query: str,
    *,
    kind: str = "lecture",
    top_k: int = 5,
    graph_path: str | None = None,
    access_lane: str = "general",
    source_paths: list[str] | None = None,
    progress: ProgressFn | None = None,
) -> dict[str, Any]:
    def p(pct: int, msg: str) -> None:
        if progress:
            progress(pct, msg)

    from app.compose import compose_from_paths, compose_from_query

    if source_paths:
        p(15, f"using {len(source_paths)} selected KO(s) [{access_lane}]")
        wait_briefly()
        p(40, "composing with LLM (H1b)")
        result = compose_from_paths(
            query,
            source_paths,
            kind=kind,
            access_lane=access_lane,
        )
    else:
        p(15, f"retrieving sources [{access_lane}]")
        wait_briefly()
        p(40, "composing with LLM")
        result = compose_from_query(
            query,
            kind=kind,
            top_k=top_k,
            graph_path=graph_path,
            access_lane=access_lane,
        )
    p(90, "writing draft")
    out = {
        "ok": True,
        "kind": result.kind,
        "draft": str(result.draft_path),
        "output_dir": str(result.output_dir),
        "access_lane": access_lane,
        "source_mode": (result.meta.evidence or {}).get("source_mode", "retrieve"),
        "max_source_classification": result.meta.evidence.get(
            "max_source_classification"
        ),
        "sources": [
            {
                "ko_id": s.ko_id,
                "title": s.title,
                "score": s.score,
                "classification": s.classification,
            }
            for s in result.meta.sources
        ],
    }
    p(100, "done")
    return out
