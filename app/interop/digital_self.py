"""Consume Digital Self exported Skills. Subprocess only — not a Skill Runtime."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from app import config

INVOKE_REL = Path("skills") / "invoke.py"


class DigitalSelfError(RuntimeError):
    """Catalog missing, invoke failed to parse, or neighbor returned an error object."""


def digital_self_root() -> Path:
    return Path(config.DIGITAL_SELF_ROOT).expanduser().resolve()


def invoke_path() -> Path:
    path = digital_self_root() / INVOKE_REL
    if not path.is_file():
        raise DigitalSelfError(f"Digital Self invoke missing: {path}")
    return path


def run_ds(*argv: str, timeout: float | None = 60.0) -> dict[str, Any]:
    """Run ``skills/invoke.py`` with this interpreter. Stdout must be one JSON object."""
    cmd = [sys.executable, str(invoke_path()), *argv]
    env = dict(os.environ)
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    proc = subprocess.run(
        cmd,
        cwd=str(digital_self_root()),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=env,
        check=False,
    )
    stdout = (proc.stdout or "").strip()
    if not stdout:
        raise DigitalSelfError(
            f"empty stdout from Digital Self (code={proc.returncode}): {(proc.stderr or '')[:500]}"
        )
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise DigitalSelfError(f"Digital Self stdout is not JSON: {stdout[:500]}") from exc
    if not isinstance(payload, dict):
        raise DigitalSelfError("Digital Self JSON must be an object")
    payload["_returncode"] = proc.returncode
    payload["_stderr"] = proc.stderr or ""
    return payload


def list_skills() -> dict[str, Any]:
    return run_ds("--list", timeout=30.0)


def invoke(skill: str, *flags: str, timeout: float | None = 60.0) -> dict[str, Any]:
    return run_ds(skill, *flags, timeout=timeout)
