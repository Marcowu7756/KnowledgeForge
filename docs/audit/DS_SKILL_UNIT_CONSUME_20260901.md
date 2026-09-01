# KF · Digital Self Skill unit consume — 2026-09-01

```yaml
doc_id: KF-AUDIT-DS-SKILL-UNIT-20260901
as_of: 2026-09-01
updated: 2026-09-01T20:10+08
surface: KF consume only (main.py ds / app.interop.digital_self)
producer: D:\DigitalSelf
verdict: UNIT_FAST = PASS · S02_LIVE = PASS · DS-I1/I2 = FIXED
```

## Scope

按 catalog 暴露 Skills 在 KF 端逐一测（S00 / S02 / S06 YouTube·Browser / S15 / S16）。

不测：Playwright 真开页 · MT5 真下单 · 在 KF 内改 DS Runtime。

---

## Results (after fix)

| Suite | Result |
|-------|--------|
| KF `tests/interop/test_digital_self_skills.py` (fast) | **pass** (deposit/transfer deny · DS_INVOKE_USAGE) |
| KF S02 live `KF_RUN_SLOW=1` | **2 passed** (~85s · earlier same day) |
| DS `tests.test_s15_research` + `test_cli_smoke` + `test_s06_browser` | **14 OK** |

CLI:

```text
ds invoke S15 … --action deposit  → L4_NO_AUTHORIZABLE_PATH
ds invoke S15 … --action transfer → L4_NO_AUTHORIZABLE_PATH
ds invoke S06                     → DS_INVOKE_USAGE (JSON on stdout)
ds invoke S06 --intent "打开 YouTube…" --url https://www.youtube.com → ok plan
```

---

## Issues

| ID | Was | Fix | Status |
|----|-----|-----|--------|
| **DS-I1** | `deposit`/`transfer` returned ok plan | DS `authority.L4_ACTIONS` + aliases | **FIXED** |
| **DS-I2** | argparse empty stdout | DS `_lib/cli.JsonArgumentParser` → `DS_INVOKE_USAGE` JSON | **FIXED** |
| **DS-I3** | YouTube plan-only | by design | N/A |
| **KF-I1** | empty stdout → exception | KF still maps empty stdout → `DS_INVOKE_EMPTY_STDOUT` as belt | kept |

### Producer files touched (Digital Self)

- `skills/_lib/authority.py`
- `skills/_lib/cli.py` (new)
- `skills/S02_ReadAloud/invoke.py`
- `skills/S06_Browser/invoke.py`
- `skills/S15_ResearchOp/invoke.py`
- `skills/S16_Compose/invoke.py`
- `tests/test_s15_research.py` · `tests/test_cli_smoke.py`

### Consumer files touched (KnowledgeForge)

- `tests/interop/test_digital_self_skills.py` — expect deny + `DS_INVOKE_USAGE`
- catalog / protocol notes

---

## Hard stops still hold

```text
KF ↛ Playwright live
KF ↛ MT5 place_order / deposit / transfer (denied)
KF ↛ auto-publish
KF ↛ rewrite DS as second Runtime
```

*KF · DS skill unit consume audit · fixed 2026-09-01*
