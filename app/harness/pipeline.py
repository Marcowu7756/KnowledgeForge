from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app import config
from app.expression.from_ko import animate_from_ko, narrate_from_ko
from app.expression.objects import AudioExpression, VisualExpression
from app.harness.artifact import Artifact, copy_into, write_json
from app.harness.evidence import capture_model_versions, file_hash
from app.harness.manifest import load_manifest, write_manifest
from app.harness.registry import require_for_steps, tool_readiness
from app.harness.task import TaskRun
from app.harness.validator import validate_artifact
from app.knowledge.object import (
    AudioRef,
    EmbeddingRef,
    EvidenceBlock,
    KnowledgeObject,
    SourceRef,
    VisualRef,
    from_knowledge_unit,
)
from app.knowledge.parse import load_unit_from_markdown, write_knowledge_object
from app.pipeline import (
    PipelineResult,
    run_audio,
    run_bilibili,
    run_file,
    run_image,
    run_twitter,
    run_youtube,
)

_URL_RE = re.compile(r"^https?://", re.I)
_YT_RE = re.compile(r"(youtube\.com|youtu\.be)", re.I)
_BILI_RE = re.compile(r"bilibili\.com", re.I)
_TW_RE = re.compile(r"(twitter\.com|x\.com)", re.I)
_IMAGE_SUFFIX = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
_FILE_SUFFIX = {".pdf", ".md", ".txt", ".docx", ".markdown"}
_AUDIO_SUFFIX = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}
_RERUN_STEPS = {"animation", "expression", "manifest"}


class HarnessError(RuntimeError):
    """Deterministic compile pipeline failed."""


@dataclass
class CompileResult:
    run: TaskRun
    package_dir: Path
    manifest_path: Path
    knowledge_object_path: Path | None
    knowledge_md: Path | None
    animation_gif: Path | None
    narration_wav: Path | None


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _package_dir(run_id: str) -> Path:
    dest = config.PACKAGES_DIR / run_id
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def _is_knowledge_card(path: Path) -> bool:
    if path.suffix.lower() != ".md":
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")[:2000]
    return "## Core Idea" in text or "```yaml" in text


def _ingest(source: str, *, index: bool | None) -> PipelineResult:
    raw = source.strip()
    if _URL_RE.match(raw):
        if _YT_RE.search(raw):
            return run_youtube(raw, index=index)
        if _BILI_RE.search(raw):
            return run_bilibili(raw, index=index)
        if _TW_RE.search(raw):
            return run_twitter(raw, index=index)
        raise HarnessError(f"unsupported URL for compile: {raw}")

    path = Path(raw).expanduser().resolve()
    if not path.is_file():
        raise HarnessError(f"source not found: {path}")

    suffix = path.suffix.lower()
    if suffix in _IMAGE_SUFFIX:
        return run_image(path, index=index)
    if suffix in _AUDIO_SUFFIX:
        return run_audio(path, index=index)
    if suffix in _FILE_SUFFIX:
        return run_file(path, index=index)
    raise HarnessError(f"unsupported source type: {suffix}")


def _record(
    artifacts: list[Artifact],
    *,
    kind: str,
    path: Path,
    meta: dict | None = None,
) -> Artifact:
    # Replace prior artifact of same kind (important for rerun).
    artifacts[:] = [a for a in artifacts if a.kind != kind]
    art = validate_artifact(Artifact.from_path(kind, path, meta=meta))  # type: ignore[arg-type]
    artifacts.append(art)
    return art


def _build_object_from_card(
    card_path: Path,
    *,
    package: Path,
    models: Any,
    run: TaskRun,
) -> KnowledgeObject:
    unit = load_unit_from_markdown(card_path)
    obj = from_knowledge_unit(
        unit,
        source=SourceRef(
            type=unit.type,
            origin=card_path.as_posix(),
            path=card_path.as_posix(),
            url=unit.url,
            hash=file_hash(card_path),
            mode="from_card",
        ),
        knowledge_md=(package / "knowledge.md").as_posix(),
    )
    obj.evidence = EvidenceBlock(
        pipeline=models.harness,
        package_id=run.id,
        models=models,
    )
    obj.embedding = EmbeddingRef(model=models.embed, status="pending")
    return obj


def _build_object_from_ingest(
    result: PipelineResult,
    *,
    package: Path,
    models: Any,
    run: TaskRun,
) -> KnowledgeObject:
    src_path = Path(result.source.path) if result.source.path else None
    obj = from_knowledge_unit(
        result.unit,
        source=SourceRef(
            type=result.source.source_type,
            origin=result.source.path or result.source.url or result.source.title,
            path=result.source.path,
            url=result.source.url,
            hash=file_hash(src_path),
            mode="ingest",
        ),
        knowledge_md=(package / "knowledge.md").as_posix(),
    )
    obj.evidence = EvidenceBlock(
        pipeline=models.harness,
        package_id=run.id,
        models=models,
    )
    obj.embedding = EmbeddingRef(model=models.embed, status="pending")
    return obj


def _attach_visual(
    obj: KnowledgeObject,
    *,
    gif: Path,
    schema: Path,
    compile_source: str,
    anim_type: str,
    expression: VisualExpression | None = None,
) -> None:
    obj.visual = VisualRef(
        type="gif",
        artifact=gif.name,
        expression=expression.id if expression else "",
        schema_id=schema.name if expression is None else "visual_expression.json",
        animation_type=anim_type,
        compile_source=compile_source,
        intent=expression.intent if expression else "",
        renderer=expression.renderer if expression else "",
    )
    obj.touch(status="compiled")


def _attach_audio(
    obj: KnowledgeObject,
    *,
    wav: Path | None,
    voice: str,
    engine: str,
    expression: AudioExpression | None = None,
) -> None:
    if wav is None and expression is None:
        return
    obj.audio = AudioRef(
        type="tts" if wav is not None else "none",
        voice=voice or (expression.voice if expression else ""),
        artifact=wav.name if wav is not None else "",
        expression=expression.id if expression else "",
        engine=engine,
        language=expression.language if expression else "",
        compile_source=expression.evidence.compile_source if expression else "",
    )
    obj.touch(status="compiled")


def _sync_evidence(obj: KnowledgeObject, *, run: TaskRun, artifacts: list[Artifact], models: Any) -> None:
    obj.evidence = EvidenceBlock(
        pipeline=models.harness,
        package_id=run.id,
        models=models,
        steps=[step.model_dump(mode="json") for step in run.steps],
        artifacts=[art.model_dump(mode="json") for art in artifacts],
    )


def _write_object(obj: KnowledgeObject, package: Path, artifacts: list[Artifact]) -> Path:
    path = write_knowledge_object(obj, package / "knowledge_object.json")
    _record(artifacts, kind="knowledge_object", path=path)
    return path


def _run_animation(
    *,
    card_path: Path,
    package: Path,
    fast: bool,
    artifacts: list[Artifact],
    obj: KnowledgeObject,
) -> Path:
    """P1-A: prefer KO → VisualExpression → GIF; fall back to card path."""
    # Always derive from KO when available (object-driven expression).
    visual = animate_from_ko(obj, dest_dir=package / "expression")
    gif = copy_into(visual.gif_path, package / "animation.gif")
    expr_path = copy_into(visual.expression_path, package / "visual_expression.json")
    # Keep animation.json as renderer-compatible snapshot of the expression.
    schema = write_json(
        package / "animation.json",
        visual.expression.to_animation_schema_payload(),
    )
    _record(
        artifacts,
        kind="visual_expression",
        path=expr_path,
        meta={
            "source_ko": obj.id,
            "intent": visual.expression.intent,
            "expression_version": visual.expression.evidence.expression_version,
            "renderer": visual.expression.renderer,
            "compile_source": visual.expression.evidence.compile_source,
            "fast_requested": fast,
        },
    )
    _record(
        artifacts,
        kind="animation_schema",
        path=schema,
        meta={"source": "ko_structure", "type": visual.expression.animation.type},
    )
    _record(artifacts, kind="animation_gif", path=gif)
    _attach_visual(
        obj,
        gif=gif,
        schema=expr_path,
        compile_source=visual.expression.evidence.compile_source,
        anim_type=visual.expression.animation.type,
        expression=visual.expression,
    )
    # card_path retained for API compatibility / future LLM fallback
    _ = card_path
    return gif


def _run_expression(
    *,
    card_path: Path,
    package: Path,
    voice_name: str | None,
    artifacts: list[Artifact],
    obj: KnowledgeObject,
) -> tuple[Path | None, Path | None]:
    """P1-A+B: KO → VisualExpression + AudioExpression → artifacts."""
    _ = card_path
    gif = _run_animation(
        card_path=package / "knowledge.md",
        package=package,
        fast=True,
        artifacts=artifacts,
        obj=obj,
    )
    audio = narrate_from_ko(
        obj,
        dest_dir=package / "expression",
        voice_name=voice_name,
    )
    expr_path = copy_into(audio.expression_path, package / "audio_expression.json")
    _record(
        artifacts,
        kind="audio_expression",
        path=expr_path,
        meta={
            "source_ko": obj.id,
            "expression_version": audio.expression.evidence.expression_version,
            "voice_model": audio.expression.evidence.voice_model,
            "compile_source": audio.expression.evidence.compile_source,
            "chars": len(audio.expression.script),
        },
    )
    wav: Path | None = None
    if audio.wav_path and audio.wav_path.is_file():
        wav = copy_into(audio.wav_path, package / "narration.wav")
        _record(artifacts, kind="narration_wav", path=wav)
    _attach_audio(
        obj,
        wav=wav,
        voice=voice_name or audio.expression.voice or config.TTS_VOICE_NAME,
        engine=config.TTS_ENGINE,
        expression=audio.expression,
    )
    return gif, wav


def compile_knowledge(
    source: str,
    *,
    from_card: bool = False,
    animate: bool = False,
    narrate: bool = False,
    fast: bool = False,
    voice_name: str | None = None,
    index: bool | None = False,
    package_id: str | None = None,
) -> CompileResult:
    """Deterministic Source → KnowledgeObject package orchestrator."""
    run_id = package_id or f"{_stamp()}_{uuid4().hex[:8]}"
    package = _package_dir(run_id)
    run = TaskRun(id=run_id, source=source, package_dir=package.as_posix())
    run.mark_running()
    artifacts: list[Artifact] = []
    models = capture_model_versions()
    options = {
        "from_card": from_card,
        "animate": animate,
        "narrate": narrate,
        "fast": fast,
        "voice_name": voice_name,
    }

    needs_ocr = (not from_card) and Path(source).suffix.lower() in _IMAGE_SUFFIX
    blocking = require_for_steps(narrate=narrate, ocr=needs_ocr)
    if blocking:
        raise HarnessError("local assets not ready:\n  - " + "\n  - ".join(blocking))

    obj: KnowledgeObject | None = None
    animation_gif: Path | None = None
    narration_wav: Path | None = None
    ko_path: Path | None = None

    try:
        ready_step = run.step("registry")
        ready_step.mark_running()
        ready_path = write_json(
            package / "registry.json",
            {"tools": tool_readiness(), "models": models.model_dump()},
        )
        ready_step.mark_ok(artifacts=[ready_path.as_posix()], meta={"harness": models.harness})

        know_step = run.step("knowledge")
        know_step.mark_running()
        card_candidate = Path(source).expanduser()
        use_card = from_card or (
            card_candidate.is_file() and _is_knowledge_card(card_candidate)
        )

        if use_card:
            card_path = card_candidate.resolve()
            if not card_path.is_file():
                raise HarnessError(f"knowledge card not found: {card_path}")
            packaged_md = copy_into(card_path, package / "knowledge.md")
            source_json = write_json(
                package / "source.json",
                {
                    "mode": "from_card",
                    "path": card_path.as_posix(),
                    "title": card_path.stem,
                    "hash": file_hash(card_path),
                },
            )
            obj = _build_object_from_card(card_path, package=package, models=models, run=run)
            ko_path = _write_object(obj, package, artifacts)
            know_step.mark_ok(
                artifacts=[
                    _record(artifacts, kind="source", path=source_json).path,
                    _record(artifacts, kind="knowledge_md", path=packaged_md).path,
                    ko_path.as_posix(),
                ],
                meta={"mode": "from_card", "ko_id": obj.id},
            )
        else:
            result = _ingest(source, index=index)
            card_path = result.markdown_path
            packaged_md = copy_into(card_path, package / "knowledge.md")
            unit_json = write_json(package / "unit.json", result.unit)
            source_json = write_json(
                package / "source.json",
                {
                    "mode": "ingest",
                    "source_type": result.source.source_type,
                    "title": result.source.title,
                    "url": result.source.url,
                    "path": result.source.path,
                    "raw_path": result.raw_path.as_posix(),
                    "truncated": result.truncated,
                    "hash": file_hash(Path(result.source.path) if result.source.path else None),
                    "metadata": result.source.metadata,
                },
            )
            text_path = write_json(
                package / "transcript.json",
                {
                    "title": result.source.title,
                    "text": result.source.text[:50000],
                    "chars": len(result.source.text),
                },
            )
            obj = _build_object_from_ingest(result, package=package, models=models, run=run)
            ko_path = _write_object(obj, package, artifacts)
            know_step.mark_ok(
                artifacts=[
                    _record(artifacts, kind="source", path=source_json).path,
                    _record(artifacts, kind="transcript", path=text_path).path,
                    _record(artifacts, kind="knowledge_md", path=packaged_md).path,
                    _record(artifacts, kind="knowledge_json", path=unit_json).path,
                    ko_path.as_posix(),
                ],
                meta={"unit_id": result.unit.id, "ko_id": obj.id, "title": result.unit.title},
            )

        assert obj is not None

        anim_step = run.step("animation")
        if animate and not narrate:
            anim_step.mark_running()
            animation_gif = _run_animation(
                card_path=card_path,
                package=package,
                fast=fast,
                artifacts=artifacts,
                obj=obj,
            )
            anim_step.mark_ok(
                artifacts=[a.path for a in artifacts if a.kind.startswith("animation")],
                meta={"source": obj.visual.compile_source},
            )
        elif not animate and not narrate:
            anim_step.mark_skipped("not requested")
        else:
            anim_step.mark_skipped("handled by expression step")

        expr_step = run.step("expression")
        if narrate:
            expr_step.mark_running()
            animation_gif, narration_wav = _run_expression(
                card_path=card_path,
                package=package,
                voice_name=voice_name,
                artifacts=artifacts,
                obj=obj,
            )
            if narration_wav is None:
                expr_step.meta["audio"] = "skipped"
            expr_step.mark_ok(
                artifacts=[
                    a.path
                    for a in artifacts
                    if a.kind in {"express_schema", "animation_gif", "narration_wav"}
                ]
            )
        else:
            expr_step.mark_skipped("not requested")

        man_step = run.step("manifest")
        man_step.mark_running()
        run.mark_ok()
        _sync_evidence(obj, run=run, artifacts=artifacts, models=models)
        ko_path = _write_object(obj, package, artifacts)
        manifest_path = write_manifest(
            package,
            run=run,
            models=models,
            artifacts=artifacts,
            options=options,
            obj=obj,
        )
        man_art = _record(artifacts, kind="manifest", path=manifest_path)
        # Rewrite with final artifact list (includes manifest itself)
        _sync_evidence(obj, run=run, artifacts=artifacts, models=models)
        _write_object(obj, package, artifacts)
        write_manifest(
            package,
            run=run,
            models=models,
            artifacts=artifacts,
            options=options,
            obj=obj,
        )
        man_step.mark_ok(artifacts=[man_art.path])

        return CompileResult(
            run=run,
            package_dir=package,
            manifest_path=manifest_path,
            knowledge_object_path=ko_path,
            knowledge_md=package / "knowledge.md",
            animation_gif=animation_gif,
            narration_wav=narration_wav,
        )
    except Exception as exc:  # noqa: BLE001
        run.mark_fail(str(exc))
        try:
            write_manifest(
                package,
                run=run,
                models=models,
                artifacts=artifacts,
                options=options,
                obj=obj,
                error=str(exc),
            )
        except Exception:  # noqa: BLE001
            pass
        if package.exists() and not any(package.iterdir()):
            shutil.rmtree(package, ignore_errors=True)
        raise HarnessError(str(exc)) from exc


def rerun_step(
    package_dir: str | Path,
    step: str,
    *,
    fast: bool = False,
    voice_name: str | None = None,
) -> CompileResult:
    """Re-run one failed/optional step without rebuilding the whole package."""
    if step not in _RERUN_STEPS:
        raise HarnessError(f"rerun supports only: {', '.join(sorted(_RERUN_STEPS))}")

    package = Path(package_dir).expanduser().resolve()
    if not package.is_dir():
        raise HarnessError(f"package not found: {package}")

    manifest = load_manifest(package)
    models = capture_model_versions()
    ko_path = package / "knowledge_object.json"
    if not ko_path.is_file():
        raise HarnessError("knowledge_object.json missing — compile once before rerun")
    obj = KnowledgeObject.model_validate(json.loads(ko_path.read_text(encoding="utf-8")))
    card_path = package / "knowledge.md"
    if not card_path.is_file():
        raise HarnessError("knowledge.md missing in package")

    artifacts = [
        Artifact.model_validate(item)
        for item in manifest.artifacts
        if item.get("kind") != "manifest"
    ]
    # Drop artifacts that this step owns so they can be replaced.
    drop_kinds = {
        "animation": {
            "animation_gif",
            "animation_schema",
            "visual_expression",
        },
        "expression": {
            "express_schema",
            "animation_gif",
            "animation_schema",
            "narration_wav",
            "visual_expression",
            "audio_expression",
        },
        "manifest": {"manifest"},
    }[step]
    artifacts = [a for a in artifacts if a.kind not in drop_kinds]

    run = TaskRun(
        id=manifest.id,
        source=manifest.source,
        package_dir=package.as_posix(),
        steps=[],
    )
    # Preserve prior step history as frozen evidence, then append rerun.
    for prior in manifest.steps:
        from app.harness.task import TaskStep

        run.steps.append(TaskStep.model_validate(prior))

    run.mark_running()
    animation_gif = package / "animation.gif" if (package / "animation.gif").is_file() else None
    narration_wav = package / "narration.wav" if (package / "narration.wav").is_file() else None
    options = dict(manifest.options)
    if voice_name:
        options["voice_name"] = voice_name
    options["fast"] = fast if step == "animation" else options.get("fast", False)

    try:
        if step == "animation":
            st = run.step("animation_rerun")
            st.mark_running()
            animation_gif = _run_animation(
                card_path=card_path,
                package=package,
                fast=fast,
                artifacts=artifacts,
                obj=obj,
            )
            st.mark_ok(artifacts=[a.path for a in artifacts if a.kind.startswith("animation")])
            options["animate"] = True
        elif step == "expression":
            blocking = require_for_steps(narrate=True, ocr=False)
            if blocking:
                raise HarnessError("local assets not ready:\n  - " + "\n  - ".join(blocking))
            st = run.step("expression_rerun")
            st.mark_running()
            animation_gif, narration_wav = _run_expression(
                card_path=card_path,
                package=package,
                voice_name=voice_name or options.get("voice_name"),
                artifacts=artifacts,
                obj=obj,
            )
            st.mark_ok(
                artifacts=[
                    a.path
                    for a in artifacts
                    if a.kind in {"express_schema", "animation_gif", "narration_wav"}
                ]
            )
            options["narrate"] = True
            options["animate"] = True
        else:
            st = run.step("manifest_rerun")
            st.mark_running()
            st.mark_ok()

        man_step = run.step("manifest")
        man_step.mark_running()
        run.mark_ok()
        _sync_evidence(obj, run=run, artifacts=artifacts, models=models)
        ko_out = _write_object(obj, package, artifacts)
        manifest_path = write_manifest(
            package,
            run=run,
            models=models,
            artifacts=artifacts,
            options=options,
            obj=obj,
        )
        man_art = _record(artifacts, kind="manifest", path=manifest_path)
        _sync_evidence(obj, run=run, artifacts=artifacts, models=models)
        _write_object(obj, package, artifacts)
        write_manifest(
            package,
            run=run,
            models=models,
            artifacts=artifacts,
            options=options,
            obj=obj,
        )
        man_step.mark_ok(artifacts=[man_art.path])

        return CompileResult(
            run=run,
            package_dir=package,
            manifest_path=manifest_path,
            knowledge_object_path=ko_out,
            knowledge_md=card_path,
            animation_gif=Path(animation_gif) if animation_gif else None,
            narration_wav=Path(narration_wav) if narration_wav else None,
        )
    except Exception as exc:  # noqa: BLE001
        run.mark_fail(str(exc))
        write_manifest(
            package,
            run=run,
            models=models,
            artifacts=artifacts,
            options=options,
            obj=obj,
            error=str(exc),
        )
        raise HarnessError(str(exc)) from exc
