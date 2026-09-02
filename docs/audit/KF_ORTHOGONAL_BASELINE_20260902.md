# KF audit · Orthogonal consume + voice baseline · 2026-09-02

```yaml
doc_id: KF-EVIDENCE-20260902-ORTHOGONAL-BASELINE
verdict: DS_CONSUME_ALIGNED · VOICE_ME_EN_SON · PRODUCER_POINTER_OK · PYTEST_32_2SKIP
as_of: 2026-09-02
```

## Producer pointer (unchanged policy ownership)

SoT remains `D:\DigitalSelf\docs\PRODUCER_CONSUMPTION_V0.md`.  
KF note: [`../interop/DS_PRODUCER_CONSUMPTION_V0.md`](../interop/DS_PRODUCER_CONSUMPTION_V0.md)

```text
SETV export+Card+Evidence = OPEN (consume via ds invoke S15)
FactorLib / AShareLib     = WAITING
S03                       = contract only · KF does not dub
```

## Docs refreshed

| Path | Change |
|------|--------|
| `docs/interop/DIGITAL_SELF_SKILLS_V0.md` | sealed authorize name · S03 not consumed · utility |
| `docs/interop/digital_self_catalog_v0.yaml` | `authorize_live` aligned |
| `docs/ops/VOICE_IDENTITY_V0.md` | me_en = son · DEFAULT=me |
| `docs/audit/ME_EN_SON_SEED_20260901.md` | SHA256 integrity |
| `docs/ops/NTW_TO_KF_TRANSFER_V0.md` | seed / S03 posture |
| `docs/ops/OPS_RUNBOOK_V0.md` | SETV live example · voice evidence link |
| `docs/audit/DS_SKILL_CONSUME_20260901.md` | 32/2 pytest |

## Tests (verified 2026-09-02)

```text
.\.venv\Scripts\python.exe -m pytest tests/interop/test_digital_self_skills.py -v
32 passed, 2 skipped
```

DS unit (neighbor): `41 OK`.
