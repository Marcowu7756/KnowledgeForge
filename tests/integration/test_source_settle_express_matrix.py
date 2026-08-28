"""Non-Cartesian integration: each signal source → settle → one express path."""

from __future__ import annotations

from pathlib import Path

import pytest

from app import config
from tests.integration.source_matrix_lib import (
    MATRIX_RUNNERS,
    run_full_matrix,
    write_evidence,
)

EVIDENCE_MD = config.ROOT / "docs" / "audit" / "INTEGRATION_SOURCE_MATRIX_20260828.md"


@pytest.fixture
def matrix_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    raw = tmp_path / "raw"
    packages = tmp_path / "packages"
    expression = tmp_path / "expression"
    for d in (raw, packages, expression):
        d.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(config, "RAW_DIR", raw)
    monkeypatch.setattr(config, "PACKAGES_DIR", packages)
    monkeypatch.setattr(config, "EXPRESSION_DIR", expression)
    return tmp_path


def test_source_settle_express_matrix_non_cartesian(matrix_dirs: Path):
    """One row per source — acquire → settle → express. Record failures for fix loop."""
    results = run_full_matrix(matrix_dirs / "matrix_work")
    evidence = write_evidence(results, EVIDENCE_MD)

    failed = [r for r in results if r.status == "fail"]
    assert len(results) == len(MATRIX_RUNNERS)
    assert evidence.is_file()

    # Soft assertion message lists failures; still fail the test so CI sees them.
    if failed:
        summary = "; ".join(f"{r.source_id}: {r.error}" for r in failed)
        pytest.fail(f"{len(failed)} matrix row(s) failed — see {evidence}: {summary}")


@pytest.mark.parametrize("source_id,runner", MATRIX_RUNNERS, ids=[s for s, _ in MATRIX_RUNNERS])
def test_matrix_row_isolated(source_id: str, runner, matrix_dirs: Path):
    """Optional per-row entry for targeted re-runs after fixes."""
    work = matrix_dirs / "row" / source_id
    packages = matrix_dirs / "packages"
    work.mkdir(parents=True, exist_ok=True)
    result = runner(work, packages)
    if result.status == "skip":
        pytest.skip(result.detail or "skipped")
    if result.status == "fail":
        pytest.fail(f"{source_id}: {result.error}\n{result.traceback}")
