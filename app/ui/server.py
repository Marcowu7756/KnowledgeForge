"""FastAPI app: Windows local workshop UI for KnowledgeForge / PAILE."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import config
from app.local_models import status_rows
from app.ui import actions
from app.ui.jobs import STORE
from app.ui.preview import preview_payload, resolve_data_path

STATIC_DIR = Path(__file__).resolve().parent / "static"


class CaptureBody(BaseModel):
    kind: Literal["youtube", "bilibili", "file", "audio", "image"] = "file"
    target: str = Field(..., description="URL or local path")
    async_job: bool = True


class CompileBody(BaseModel):
    path: str
    from_card: bool = True
    animate: bool = False
    narrate: bool = False
    fast: bool = True
    async_job: bool = True


class ReconstructBody(BaseModel):
    from_index: bool = True
    view: Literal["theme", "concept", "learning_path", "taxonomy", "contrast"] = "theme"
    evolve_dir: str | None = None
    async_job: bool = True


class RetrieveBody(BaseModel):
    query: str
    top_k: int = 5
    graph_path: str | None = None
    access_lane: Literal["general", "proprietary"] = "general"
    async_job: bool = True


class ComposeBody(BaseModel):
    query: str
    kind: Literal["paper", "lecture"] = "lecture"
    top_k: int = 5
    graph_path: str | None = None
    access_lane: Literal["general", "proprietary"] = "general"
    async_job: bool = True


class JobCreateBody(BaseModel):
    action: Literal["capture", "compile", "reconstruct", "retrieve", "compose"]
    payload: dict[str, Any] = Field(default_factory=dict)


def create_app() -> FastAPI:
    app = FastAPI(title="KnowledgeForge UI", version="0.4.0", docs_url="/api/docs")

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        from app.knowledge.access import (
            CLOUD_LLM_PROVIDERS,
            LOCAL_LLM_PROVIDERS,
            is_local_llm_provider,
            lane_retrieve_ceiling,
        )

        return {
            "ok": True,
            "product": "KnowledgeForge",
            "engine": "PAILE",
            "root": str(config.ROOT),
            "ui_version": "0.4.0",
            "llm": {
                "provider": config.LLM_PROVIDER,
                "track": "local" if is_local_llm_provider(config.LLM_PROVIDER) else "cloud",
                "local_providers": sorted(LOCAL_LLM_PROVIDERS),
                "cloud_providers": sorted(CLOUD_LLM_PROVIDERS),
                "note": "Dual-track: choose local or cloud via LLM_PROVIDER; access filters KO flow",
            },
            "access_lanes": {
                "general": {
                    "label": "通用知识",
                    "ceiling": lane_retrieve_ceiling("general"),
                    "includes": ["public", "internal"],
                },
                "proprietary": {
                    "label": "专有资产",
                    "ceiling": lane_retrieve_ceiling("proprietary"),
                    "includes": ["public", "internal", "restricted"],
                    "projects": ["setv", "factorlib", "asharelib"],
                },
            },
            "stages": [
                "capture",
                "distill",
                "reconstruct",
                "retrieve",
                "compose_express",
            ],
        }

    @app.get("/api/status")
    def status() -> dict[str, Any]:
        models = [
            {"name": name, "path": path, "state": state}
            for name, path, state in status_rows()
        ]
        return {
            "models": models,
            "paths": {
                "knowledge": str(config.KNOWLEDGE_DIR),
                "packages": str(config.PACKAGES_DIR),
                "reconstruct": str(config.RECONSTRUCT_DIR),
                "retrieve": str(config.RETRIEVE_DIR),
                "compose": str(config.COMPOSE_DIR),
                "expression": str(config.EXPRESSION_DIR),
            },
            "counts": {
                "packages": _count_dirs(config.PACKAGES_DIR),
                "knowledge_md": _count_glob(config.KNOWLEDGE_DIR, "**/*.md"),
                "compose": _count_dirs(config.COMPOSE_DIR),
                "graphs": _count_dirs(config.RECONSTRUCT_DIR),
            },
        }

    @app.get("/api/packages")
    def list_packages(limit: int = 24) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        root = config.PACKAGES_DIR
        if root.is_dir():
            dirs = sorted(
                [p for p in root.iterdir() if p.is_dir()],
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            for p in dirs[: max(1, min(limit, 100))]:
                items.append(
                    {
                        "name": p.name,
                        "path": str(p),
                        "has_ko": (p / "knowledge_object.json").is_file(),
                        "has_manifest": (p / "manifest.json").is_file(),
                    }
                )
        return {"items": items}

    @app.get("/api/artifacts")
    def list_artifacts(limit: int = 20) -> dict[str, Any]:
        compose: list[dict[str, str]] = []
        if config.COMPOSE_DIR.is_dir():
            for d in sorted(
                config.COMPOSE_DIR.iterdir(),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            ):
                if not d.is_dir():
                    continue
                for name in ("LECTURE.md", "PAPER.md", "FAILED.md"):
                    f = d / name
                    if f.is_file():
                        compose.append(
                            {
                                "kind": name.replace(".md", "").lower(),
                                "path": str(f),
                                "dir": str(d),
                                "preview_url": f"/api/preview?path={quote(f.as_posix())}",
                            }
                        )
                        break
                if len(compose) >= limit:
                    break

        media: list[dict[str, str]] = []
        if config.EXPRESSION_DIR.is_dir():
            for f in sorted(
                list(config.EXPRESSION_DIR.rglob("*.gif"))
                + list(config.EXPRESSION_DIR.rglob("*.wav")),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )[:limit]:
                media.append(
                    {
                        "path": str(f),
                        "name": f.name,
                        "suffix": f.suffix,
                        "preview_url": f"/api/preview?path={quote(f.as_posix())}",
                    }
                )

        return {"compose": compose, "media": media}

    @app.get("/api/knowledge")
    def list_knowledge(
        lane: Literal["general", "proprietary", "all"] = "all",
        limit: int = Query(40, ge=1, le=200),
    ) -> dict[str, Any]:
        """List knowledge cards split by access lane."""
        from app.knowledge.path_access import resolve_access_for_path

        general: list[dict[str, Any]] = []
        proprietary: list[dict[str, Any]] = []
        root = config.KNOWLEDGE_DIR
        if root.is_dir():
            files = sorted(
                root.rglob("*.md"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            for f in files:
                if f.name.upper() == "INDEX.MD" or f.name.lower() == "readme.md":
                    continue
                access = resolve_access_for_path(f)
                item = {
                    "path": str(f),
                    "name": f.name,
                    "classification": access.classification,
                    "source_project": access.source_project or "",
                    "lane": (
                        "proprietary"
                        if access.classification in {"restricted", "secret"}
                        or bool(access.source_project)
                        else "general"
                    ),
                    "preview_url": f"/api/preview?path={quote(f.as_posix())}",
                }
                if item["lane"] == "proprietary":
                    proprietary.append(item)
                else:
                    general.append(item)
                if len(general) + len(proprietary) >= limit * 2:
                    break
        if lane == "general":
            return {"lane": lane, "items": general[:limit], "general": general[:limit], "proprietary": []}
        if lane == "proprietary":
            return {
                "lane": lane,
                "items": proprietary[:limit],
                "general": [],
                "proprietary": proprietary[:limit],
            }
        return {
            "lane": "all",
            "items": (proprietary[: limit // 2] + general[: limit // 2]),
            "general": general[:limit],
            "proprietary": proprietary[:limit],
        }

    @app.get("/api/export")
    def export_file(path: str = Query(...)) -> FileResponse:
        """External export — blocked for local_only / controlled / secret."""
        from app.knowledge.path_access import gate_export

        try:
            resolved = resolve_data_path(path)
        except FileNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

        access, expr_gate, exp_gate = gate_export(resolved, external=True)
        if not expr_gate.allowed:
            raise HTTPException(
                403,
                f"export blocked (expression={expr_gate.mode}): {expr_gate.reason}",
            )
        if not exp_gate.allowed:
            raise HTTPException(
                403,
                f"export blocked (export={exp_gate.mode}): {exp_gate.reason}",
            )
        media = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
        headers = {
            "X-KF-Classification": access.classification,
            "X-KF-Export-Mode": exp_gate.mode,
        }
        if exp_gate.warning:
            headers["X-KF-Export-Warning"] = exp_gate.warning
        return FileResponse(
            resolved,
            media_type=media,
            filename=resolved.name,
            headers=headers,
        )

    @app.get("/api/preview")
    def preview(path: str = Query(...)) -> dict[str, Any]:
        try:
            resolved = resolve_data_path(path)
            return preview_payload(resolved)
        except FileNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.get("/api/preview/file")
    def preview_file(path: str = Query(...)) -> FileResponse:
        try:
            resolved = resolve_data_path(path)
        except FileNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        media = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
        return FileResponse(resolved, media_type=media, filename=resolved.name)

    @app.post("/api/jobs")
    def create_job(body: JobCreateBody) -> dict[str, Any]:
        action = body.action
        payload = body.payload or {}

        def runner(progress):  # noqa: ANN001
            if action == "capture":
                return actions.run_capture(
                    str(payload.get("kind") or "file"),
                    str(payload.get("target") or ""),
                    progress,
                )
            if action == "compile":
                return actions.run_compile(
                    str(payload.get("path") or ""),
                    from_card=bool(payload.get("from_card", True)),
                    animate=bool(payload.get("animate", False)),
                    narrate=bool(payload.get("narrate", False)),
                    fast=bool(payload.get("fast", True)),
                    progress=progress,
                )
            if action == "reconstruct":
                return actions.run_reconstruct_action(
                    from_index=bool(payload.get("from_index", True)),
                    view=str(payload.get("view") or "theme"),
                    evolve_dir=payload.get("evolve_dir"),
                    progress=progress,
                )
            if action == "retrieve":
                return actions.run_retrieve_action(
                    str(payload.get("query") or ""),
                    top_k=int(payload.get("top_k") or 5),
                    graph_path=payload.get("graph_path"),
                    access_lane=str(payload.get("access_lane") or "general"),
                    progress=progress,
                )
            if action == "compose":
                return actions.run_compose_action(
                    str(payload.get("query") or ""),
                    kind=str(payload.get("kind") or "lecture"),
                    top_k=int(payload.get("top_k") or 5),
                    graph_path=payload.get("graph_path"),
                    access_lane=str(payload.get("access_lane") or "general"),
                    progress=progress,
                )
            raise ValueError(f"unknown action: {action}")

        job = STORE.submit(action, runner)
        return {"ok": True, "job_id": job.id, "status": job.status}

    @app.get("/api/jobs")
    def list_jobs(
        limit: int = Query(50, ge=1, le=200),
        action: str | None = None,
    ) -> dict[str, Any]:
        return {"items": STORE.list_snapshots(limit=limit, action=action)}

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str) -> dict[str, Any]:
        snap = STORE.snapshot(job_id)
        if snap is None:
            raise HTTPException(404, f"job not found: {job_id}")
        return snap

    @app.post("/api/capture")
    def capture(body: CaptureBody) -> dict[str, Any]:
        if body.async_job:
            job = STORE.submit(
                "capture",
                lambda progress: actions.run_capture(body.kind, body.target, progress),
            )
            return {"ok": True, "job_id": job.id, "async": True}
        try:
            return actions.run_capture(body.kind, body.target)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(400, str(exc)) from exc

    @app.post("/api/compile")
    def compile_card(body: CompileBody) -> dict[str, Any]:
        if body.async_job:
            job = STORE.submit(
                "compile",
                lambda progress: actions.run_compile(
                    body.path,
                    from_card=body.from_card,
                    animate=body.animate,
                    narrate=body.narrate,
                    fast=body.fast,
                    progress=progress,
                ),
            )
            return {"ok": True, "job_id": job.id, "async": True}
        try:
            return actions.run_compile(
                body.path,
                from_card=body.from_card,
                animate=body.animate,
                narrate=body.narrate,
                fast=body.fast,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(400, str(exc)) from exc

    @app.post("/api/reconstruct")
    def reconstruct(body: ReconstructBody) -> dict[str, Any]:
        if body.async_job:
            job = STORE.submit(
                "reconstruct",
                lambda progress: actions.run_reconstruct_action(
                    from_index=body.from_index,
                    view=body.view,
                    evolve_dir=body.evolve_dir,
                    progress=progress,
                ),
            )
            return {"ok": True, "job_id": job.id, "async": True}
        try:
            return actions.run_reconstruct_action(
                from_index=body.from_index,
                view=body.view,
                evolve_dir=body.evolve_dir,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(400, str(exc)) from exc

    @app.post("/api/retrieve")
    def retrieve(body: RetrieveBody) -> dict[str, Any]:
        if body.async_job:
            job = STORE.submit(
                "retrieve",
                lambda progress: actions.run_retrieve_action(
                    body.query,
                    top_k=body.top_k,
                    graph_path=body.graph_path,
                    access_lane=body.access_lane,
                    progress=progress,
                ),
            )
            return {"ok": True, "job_id": job.id, "async": True}
        try:
            return actions.run_retrieve_action(
                body.query,
                top_k=body.top_k,
                graph_path=body.graph_path,
                access_lane=body.access_lane,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(400, str(exc)) from exc

    @app.post("/api/compose")
    def compose(body: ComposeBody) -> dict[str, Any]:
        if body.async_job:
            job = STORE.submit(
                "compose",
                lambda progress: actions.run_compose_action(
                    body.query,
                    kind=body.kind,
                    top_k=body.top_k,
                    graph_path=body.graph_path,
                    access_lane=body.access_lane,
                    progress=progress,
                ),
            )
            return {"ok": True, "job_id": job.id, "async": True}
        try:
            return actions.run_compose_action(
                body.query,
                kind=body.kind,
                top_k=body.top_k,
                graph_path=body.graph_path,
                access_lane=body.access_lane,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(400, str(exc)) from exc

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    return app


def serve(*, host: str = "127.0.0.1", port: int = 8765, desktop: bool = True) -> None:
    import uvicorn

    mimetypes.add_type("text/css", ".css")
    mimetypes.add_type("application/javascript", ".js")

    use_desktop = desktop
    if use_desktop:
        try:
            import webview  # noqa: F401
        except ImportError:
            use_desktop = False
            print(
                "[ui] pywebview not installed — using browser. "
                "Install: pip install pywebview",
                flush=True,
            )

    if use_desktop:
        from app.ui.desktop import open_desktop

        open_desktop(host=host, port=port)
        return

    print(f"[ui] KnowledgeForge workshop → http://{host}:{port}", flush=True)
    uvicorn.run(
        "app.ui.server:create_app",
        factory=True,
        host=host,
        port=port,
        log_level="info",
    )


def _count_dirs(root: Path) -> int:
    if not root.is_dir():
        return 0
    return sum(1 for p in root.iterdir() if p.is_dir())


def _count_glob(root: Path, pattern: str) -> int:
    if not root.is_dir():
        return 0
    return sum(1 for _ in root.glob(pattern))
