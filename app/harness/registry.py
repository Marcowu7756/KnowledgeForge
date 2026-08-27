from __future__ import annotations

from app.local_models import readiness, verify_local_assets


def tool_readiness() -> dict[str, dict[str, object]]:
    """Snapshot of local intelligence tools Harness may schedule."""
    rows: dict[str, dict[str, object]] = {}
    for name, (path, label, ready) in readiness().items():
        rows[name] = {"path": path, "label": label, "ready": ready}
    return rows


def require_for_steps(*, narrate: bool, ocr: bool) -> list[str]:
    """Return blocking readiness issues for the requested compile steps."""
    issues = verify_local_assets()
    needed: list[str] = []
    for issue in issues:
        if issue.startswith("ollama "):
            needed.append(issue)
        if narrate and issue.startswith(("tts ", "vocos ")):
            needed.append(issue)
        if ocr and issue.startswith("ocr "):
            needed.append(issue)
    return needed
