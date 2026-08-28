"""Resolve access for UI preview / export from path + optional KO frontmatter."""

from __future__ import annotations

import json
from pathlib import Path

from app import config
from app.knowledge.access import AccessBlock, GateResult, check_export_gate, check_expression_gate, default_policy_for
from app.knowledge.parse import load_knowledge_object


def _from_path_hint(path: Path) -> AccessBlock | None:
    norm = path.as_posix().replace("\\", "/").lower()
    if "/restricted/setv" in norm or "\\restricted\\setv" in norm.lower():
        return AccessBlock(
            classification="restricted",
            source_project="setv",
            export_policy="local_only",
            policy=default_policy_for("restricted"),
        )
    if "/restricted/factorlib" in norm:
        return AccessBlock(
            classification="restricted",
            source_project="factorlib",
            export_policy="local_only",
            policy=default_policy_for("restricted"),
        )
    if "/restricted/asharelib" in norm:
        return AccessBlock(
            classification="restricted",
            source_project="asharelib",
            export_policy="local_only",
            policy=default_policy_for("restricted"),
        )
    if "/restricted/" in norm:
        return AccessBlock(
            classification="restricted",
            export_policy="local_only",
            policy=default_policy_for("restricted"),
        )
    return None


def _from_compose_meta(path: Path) -> AccessBlock | None:
    """If exporting a compose draft, inherit max classification from meta.json sources."""
    meta_path = path.parent / "meta.json"
    if not meta_path.is_file():
        return None
    try:
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    lane = str((payload.get("evidence") or {}).get("access_lane") or "")
    max_class = str((payload.get("evidence") or {}).get("max_source_classification") or "")
    if max_class in {"restricted", "secret"}:
        return AccessBlock(
            classification=max_class,  # type: ignore[arg-type]
            export_policy="local_only",
            policy=default_policy_for(max_class),
        )
    if lane == "proprietary":
        return AccessBlock(
            classification="restricted",
            export_policy="local_only",
            policy=default_policy_for("restricted"),
        )
    sources = payload.get("sources") or []
    worst = "public"
    order = {"public": 0, "internal": 1, "restricted": 2, "secret": 3}
    for src in sources:
        c = str(src.get("classification") or "public")
        if order.get(c, 0) > order.get(worst, 0):
            worst = c
    if worst in {"restricted", "secret", "internal"}:
        return AccessBlock(
            classification=worst,  # type: ignore[arg-type]
            policy=default_policy_for(worst),
            export_policy="local_only" if worst in {"restricted", "secret"} else "export_ok",
        )
    return None


def resolve_access_for_path(path: Path) -> AccessBlock:
    path = path.expanduser().resolve()
    # Path layout is authoritative for proprietary trees (even before frontmatter).
    hinted = _from_path_hint(path)
    if hinted is not None:
        if path.suffix.lower() == ".md":
            try:
                obj = load_knowledge_object(path)
                # Prefer explicit KO access when present and non-public.
                if obj.access.classification != "public" or obj.access.source_project:
                    return obj.access
            except Exception:
                pass
        return hinted
    if path.suffix.lower() == ".md":
        try:
            return load_knowledge_object(path).access
        except Exception:
            pass
    if path.suffix.lower() == ".json" and path.name == "knowledge_object.json":
        try:
            return load_knowledge_object(path).access
        except Exception:
            pass
    composed = _from_compose_meta(path)
    if composed is not None:
        return composed
    return AccessBlock()


def gate_preview(path: Path) -> GateResult:
    access = resolve_access_for_path(path)
    result = check_expression_gate(
        access.classification,
        policy=access.resolved_policy(),
        external=False,
    )
    try:
        from app.knowledge.access_audit import record_gate

        record_gate(
            action="expression",
            gate=result,
            path=str(path),
            source_project=access.source_project or "",
            external=False,
        )
    except Exception:
        pass
    return result


def gate_export(
    path: Path,
    *,
    external: bool = True,
    channel: str = "plaintext",
) -> tuple[AccessBlock, GateResult, GateResult]:
    """Return (access, expression_gate, export_gate) for an external or local export."""
    access = resolve_access_for_path(path)
    expr = check_expression_gate(
        access.classification,
        policy=access.resolved_policy(),
        external=external,
        channel=channel,
    )
    exp = check_export_gate(
        access.classification,
        policy=access.resolved_policy(),
        external=external,
        channel=channel,
    )
    try:
        from app.knowledge.access_audit import record_gate

        record_gate(
            action="expression",
            gate=expr,
            path=str(path),
            source_project=access.source_project or "",
            external=external,
        )
        record_gate(
            action="export",
            gate=exp,
            path=str(path),
            source_project=access.source_project or "",
            external=external,
        )
    except Exception:
        pass
    return access, expr, exp


def build_encrypted_export(
    path: Path,
    *,
    dest: Path | None = None,
    passphrase: str | None = None,
) -> tuple[AccessBlock, Path, bytes]:
    """Gate + encrypt → (access, dest_path, envelope_bytes). Raises on deny."""
    from app.knowledge.encrypted_export import (
        EncryptedExportError,
        ENVELOPE_SUFFIX,
        encrypt_file,
    )

    access, expr, exp = gate_export(path, external=True, channel="encrypted")
    if not expr.allowed:
        raise PermissionError(
            f"expression blocked ({expr.mode}): {expr.reason}"
        )
    if not exp.allowed:
        raise PermissionError(f"export blocked ({exp.mode}): {exp.reason}")
    try:
        blob = encrypt_file(
            path,
            classification=access.classification,
            source_project=access.source_project or "",
            passphrase=passphrase,
        )
    except EncryptedExportError:
        raise
    if dest is None:
        from app import config

        stamp = path.stem
        dest = config.DATA_DIR / "exports" / f"{stamp}{ENVELOPE_SUFFIX}"
    else:
        dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(blob)
    try:
        from app.knowledge.access_audit import record_access

        record_access(
            action="export",
            outcome="allow",
            classification=access.classification,
            source_project=access.source_project or "",
            path=str(path),
            mode="encrypted",
            reason="encrypted_channel",
            detail={"dest": str(dest), "bytes": len(blob)},
        )
    except Exception:
        pass
    return access, dest, blob


def proprietary_roots() -> dict[str, Path]:
    base = config.KNOWLEDGE_DIR / "restricted"
    return {
        "setv": base / "setv",
        "factorlib": base / "factorlib",
        "asharelib": base / "asharelib",
    }
