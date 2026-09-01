# KF consumes Digital Self Skills · 2026-09-01

```yaml
doc_id: KF-EVIDENCE-20260901-DS-SKILL-CONSUME
verdict: CONSUME_SURFACE = LANDED · PYTEST 8 PASSED · S02_LIVE_FROM_KF = PASS
```

Owner: pass DS Skill parameters/docs into KF, then test from KF.

## Landed in KF

| Path | Role |
|---|---|
| `docs/interop/DIGITAL_SELF_SKILLS_V0.md` | consume protocol + full flags |
| `docs/interop/digital_self_catalog_v0.yaml` | machine snapshot of params |
| `app/interop/digital_self.py` | subprocess to DS `skills/invoke.py` |
| `python main.py ds list \| invoke` | KF CLI |
| `tests/interop/test_digital_self_skills.py` | KF-side tests |

## Tests (KF venv · 2026-09-01)

```text
.\.venv\Scripts\python.exe -m pytest tests/interop/test_digital_self_skills.py -v
8 passed
```

CLI: `ds list` · S00 useful · S06 `--live` deny · S15 `place_order` → `L4_NO_AUTHORIZABLE_PATH` · S16 `--publish` deny.

S02 live from KF:

```text
python main.py ds invoke S02 --text "核心观点先读出来。" --language zh -o data\expression\_ds_s02_kf_consume.wav
ok · voice=me · duration_sec=3.296 · engine=neighbor_kf_f5 · identity=D:\DigitalSelf\data\identity\voice
```

KF does not copy Skill executors. L4 / live browser / publish stay denied.

**Posture update:** KF = Skill **consumer** only. Native `voice speak` / express TTS / UI narrate remain **legacy** and will phase out toward `ds invoke` after docs/SOP migrate. Map: [`../ops/KF_SKILL_CONSUME_PHASEOUT_V0.md`](../ops/KF_SKILL_CONSUME_PHASEOUT_V0.md).

Producer SoT remains `D:\DigitalSelf`.
