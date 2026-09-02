# KF consumes Digital Self Skills · 2026-09-01

```yaml
doc_id: KF-EVIDENCE-20260901-DS-SKILL-CONSUME
verdict: CONSUME_SURFACE = LANDED · PYTEST 32 PASSED / 2 SKIPPED · S02_LIVE_FROM_KF = PASS
as_of_refresh: 2026-09-02
```

Owner: pass DS Skill parameters/docs into KF, then test from KF.

## Landed in KF

| Path | Role |
|---|---|
| `docs/interop/DIGITAL_SELF_SKILLS_V0.md` | consume protocol + full flags |
| `docs/interop/digital_self_catalog_v0.yaml` | machine snapshot of params |
| `docs/interop/DS_PRODUCER_CONSUMPTION_V0.md` | pointer · SoT on DS |
| `app/interop/digital_self.py` | subprocess to DS `skills/invoke.py` |
| `python main.py ds list \| invoke` | KF CLI |
| `tests/interop/test_digital_self_skills.py` | KF-side tests |

## Tests (KF venv · 2026-09-02)

```text
.\.venv\Scripts\python.exe -m pytest tests/interop/test_digital_self_skills.py -v
32 passed, 2 skipped
```

（2 skipped = S02 live；`$env:KF_RUN_SLOW="1"` 可开。）

CLI smoke covered: `ds list` · S00 · S06 `--live` deny · S15 L4 deny · S15 SETV live-read · S16 `--publish` deny.

S02 live from KF (earlier):

```text
python main.py ds invoke S02 --text "核心观点先读出来。" --language zh -o data\expression\_ds_s02_kf_consume.wav
ok · voice=me · duration_sec=3.296 · engine=neighbor_kf_f5 · identity=D:\DigitalSelf\data\identity\voice
```

## Seal alignment (consume docs only)

```text
AUTHORIZE DS · S15 Producer live-read · SETV · export+Card+Evidence = OPEN
FactorLib / AShareLib live = WAITING
S03 invoke = DENY · not in catalog
```

KF does not copy Skill executors. Does not expand Producer WAITING → OPEN.

**Posture:** KF = Skill **consumer** only. Native `voice speak` / express TTS / UI narrate = **legacy**. Map: [`../ops/KF_SKILL_CONSUME_PHASEOUT_V0.md`](../ops/KF_SKILL_CONSUME_PHASEOUT_V0.md).

DS mirror evidence: `D:\DigitalSelf\docs\audit\ARCH_20260901_KF_CONSUME.md`  
Producer SoT remains `D:\DigitalSelf`.
