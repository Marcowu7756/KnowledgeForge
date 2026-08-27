"""FastAPI app: Windows local workshop UI for KnowledgeForge / PAILE."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import config
from app.local_models import status_rows

STATIC_DIR = Path(__file__).resolve().parent / "static"


class CaptureBody(BaseModel):
    kind: Literal["youtube", "bilibili", "file", "audio", "image"] = "file"
    target: str = Field(..., description="URL or local path")


class CompileBody(BaseModel):
    path: str
    from_card: bool = True
    animate: bool = False
    narrate: bool = False
    fast: bool = True


class ReconstructBody(BaseModel):
    from_index: bool = True
    view: Literal["theme", "concept", "learning_path"] = "theme"
    evolve_dir: str | None = None


class RetrieveBody(BaseModel):
    query: str
    top_k: int = 5
    graph_path: str | None = None


class ComposeBody(BaseModel):
    query: str
    kind: Literal["paper", "lecture"] = "lecture"
    top_k: int = 5
    graph_path: str | None = None


def create_app() -> FastAPI:
    app = FastAPI(title="KnowledgeForge UI", version="0.1.0", docs_url="/api/docs")

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {
            "ok": True,
            "product": "KnowledgeForge",
            "engine": "PAILE",
            "root": str(config.ROOT),
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
        """Compose drafts + expression media (read-only links)."""
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
                media.append({"path": str(f), "name": f.name, "suffix": f.suffix})

        return {"compose": compose, "media": media}

    @app.post("/api/capture")
    def capture(body: CaptureBody) -> dict[str, Any]:
        target = body.target.strip()
        if not target:
            raise HTTPException(400, "target required")
        try:
            if body.kind == "youtube":
                from app.pipeline import run_youtube

                result = run_youtube(target)
            elif body.kind == "bilibili":
                from app.pipeline import run_bilibili

                result = run_bilibili(target)
            elif body.kind == "audio":
                from app.pipeline import run_audio

                result = run_audio(target)
            elif body.kind == "image":
                from app.pipeline import run_image

                result = run_image(target)
            else:
                from app.pipeline import run_file

                result = run_file(target)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(400, str(exc)) from exc

        return {
            "ok": True,
            "title": result.unit.title,
            "knowledge": str(result.markdown_path),
            "raw": str(result.raw_path),
            "concepts": len(result.unit.concepts),
        }

    @app.post("/api/compile")
    def compile_card(body: CompileBody) -> dict[str, Any]:
        from app.harness import HarnessError, compile_knowledge

        path = Path(body.path).expanduser()
        if not path.is_file():
            alt = config.ROOT / body.path
            path = alt if alt.is_file() else path
        if not path.is_file():
            raise HTTPException(400, f"card not found: {body.path}")
        try:
            pkg = compile_knowledge(
                str(path),
                from_card=body.from_card,
                animate=body.animate,
                narrate=body.narrate,
                fast=body.fast,
            )
        except HarnessError as exc:
            raise HTTPException(400, str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(500, str(exc)) from exc
        return {
            "ok": True,
            "package": str(getattr(pkg, "package_dir", "")),
            "detail": _safe_pkg_summary(pkg),
        }

    @app.post("/api/reconstruct")
    def reconstruct(body: ReconstructBody) -> dict[str, Any]:
        from app.reconstruct import ReconstructLoadError, run_reconstruct

        try:
            result = run_reconstruct(
                from_index=body.from_index,
                view=body.view,
                evolve_dir=body.evolve_dir,
            )
        except ReconstructLoadError as exc:
            raise HTTPException(400, str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True, "result": _summarize_reconstruct(result)}

    @app.post("/api/retrieve")
    def retrieve(body: RetrieveBody) -> dict[str, Any]:
        from app.retrieve import EmbedderError, run_query

        try:
            run = run_query(
                body.query,
                top_k=body.top_k,
                graph_path=body.graph_path,
                save=True,
            )
        except (EmbedderError, FileNotFoundError, ValueError) as exc:
            raise HTTPException(400, str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(500, str(exc)) from exc
        hits = [
            {
                "ko_id": h.ko_id,
                "title": h.title,
                "score": h.score,
                "semantic_score": h.semantic_score,
                "graph_score": h.graph_score,
                "path": h.path,
                "why": h.why,
            }
            for h in run.result.hits
        ]
        return {
            "ok": True,
            "mode": run.result.mode,
            "hits": hits,
            "result_path": str(run.result_path) if run.result_path else None,
        }

    @app.post("/api/compose")
    def compose(body: ComposeBody) -> dict[str, Any]:
        from app.compose import compose_from_query
        from app.compose.validate import ComposePayloadError

        try:
            result = compose_from_query(
                body.query,
                kind=body.kind,
                top_k=body.top_k,
                graph_path=body.graph_path,
            )
        except ComposePayloadError as exc:
            raise HTTPException(422, str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(400, str(exc)) from exc
        return {
            "ok": True,
            "kind": result.kind,
            "draft": str(result.draft_path),
            "output_dir": str(result.output_dir),
            "sources": [
                {"ko_id": s.ko_id, "title": s.title, "score": s.score}
                for s in result.meta.sources
            ],
        }

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    return app


def serve(*, host: str = "127.0.0.1", port: int = 8765, desktop: bool = False) -> None:
    import uvicorn

    # Ensure common media types
    mimetypes.add_type("text/css", ".css")
    mimetypes.add_type("application/javascript", ".js")

    if desktop:
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


def _safe_pkg_summary(pkg: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in ("package_dir", "manifest_path", "knowledge_object_path", "knowledge_md"):
        val = getattr(pkg, key, None)
        if val is not None:
            out[key] = str(val)
    if hasattr(pkg, "id"):
        out["id"] = str(pkg.id)
    return out


def _summarize_reconstruct(result: Any) -> dict[str, Any]:
    g = getattr(result, "graph", None)
    out: dict[str, Any] = {
        "output_dir": str(getattr(result, "output_dir", "") or ""),
        "graph_path": str(getattr(result, "graph_path", "") or ""),
        "view_path": str(getattr(result, "view_path", "") or ""),
        "report_path": str(getattr(result, "report_path", "") or ""),
        "kos": len(getattr(result, "kos", []) or []),
    }
    if g is not None:
        out["graph_id"] = getattr(g, "id", "")
        stats = getattr(getattr(g, "relations", None), "stats", {}) or {}
        out["nodes"] = stats.get("nodes", len(getattr(g, "nodes", []) or []))
        out["edges"] = stats.get("edges", len(getattr(getattr(g, "relations", None), "edges", []) or []))
    return out
