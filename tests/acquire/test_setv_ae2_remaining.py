"""AE-2 measurement / experiment / uncertainty cite-only adapters."""

from __future__ import annotations

from pathlib import Path

from app.ingest.setv_artifact import (
    parse_experiment_artifact,
    parse_measurement_artifact,
    parse_uncertainty_artifact,
    unit_from_artifact,
)

SAMPLE_EXP = """# SETV Experiment · DEMO H4 2024 · T1 V0

**Experiment id:** `SETV-EXP-DEMO-H4-2024-T1-V0`
**Status:** Evidence Pack COMPLETE · Experiment CLOSED · ≠ Runtime
**Instance:** `SETV-INST-DEMO-H4-2024-2026`

## Declaration (FROZEN)

| Tag | Value |
|-----|-------|
| `N_context` | 20 |

## Headline metrics (LOO NLL bits)

| B0 | B1 |
|----|----|
| 4.2 | 1.6 |
"""

SAMPLE_MEAS = """# SETV State Representation · Minimal Invariant Set v1.0 (CONTRACT)

**Status:** **CONTRACT v1.0 FROZEN** · ≠ Signal

C1–C5 closed. No Contract C6.
"""

SAMPLE_UNC = """# DESIGN · SETV Uncertainty Language V0

**Status:** **ISSUED / SIGNED** · ≠ Runtime

## 0. What this round issues

Uncertainty Language. Not a risk map. Named ignorances only.
"""


def test_parse_measurement(tmp_path: Path):
    path = tmp_path / "SETV_STATE_CONTRACT_MINIMAL_INVARIANT_V1.md"
    path.write_text(SAMPLE_MEAS, encoding="utf-8")
    parsed = parse_measurement_artifact(path)
    assert parsed.asset_class == "measurement"
    assert "STATE_CONTRACT" in parsed.artifact_id
    unit = unit_from_artifact(parsed)
    assert unit.taxonomy.path[2] == "Measurement Knowledge"


def test_parse_experiment(tmp_path: Path):
    path = tmp_path / "SETV_EXP_DEMO_H4_2024_T1_V0.md"
    path.write_text(SAMPLE_EXP, encoding="utf-8")
    parsed = parse_experiment_artifact(path)
    assert parsed.artifact_id == "SETV-EXP-DEMO-H4-2024-T1-V0"
    assert parsed.symbol == "DEMO"


def test_parse_uncertainty(tmp_path: Path):
    path = tmp_path / "DESIGN_SETV_UNCERTAINTY_LANGUAGE_V0.md"
    path.write_text(SAMPLE_UNC, encoding="utf-8")
    parsed = parse_uncertainty_artifact(path)
    assert parsed.asset_class == "uncertainty"
    assert "UNCERTAINTY" in parsed.artifact_id
