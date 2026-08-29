# Audit · Taxonomy / Access orthogonal split — 2026-08-29

```yaml
audit_id: KF-AUDIT-TAXONOMY-ACCESS-20260829
as_of: 2026-08-29
scope: generic capture taxonomy + docs orthogonality
freeze: H4 HOLD · SETV Scope HOLD · no access-from-taxonomy derivation
sot: docs/audit/TAXONOMY_VS_ACCESS_V0.md
```

## 1. Change summary

| Area | Change |
|------|--------|
| Registry | `capture` root: `公开媒体 > 捕获` + `by_source_type` |
| API | `default_taxonomy_for_capture` · `clamp_taxonomy_path` (max 5) |
| Pipeline | `_finalize` fills empty `taxonomy.path` only; `default_access_for_ingest` unchanged |
| Docs | SoT + SOP/UAT/HANDOFF/OPS/POSTURE pointers; lane language by **classification** |
| Backfill | 3 Owner public video KOs (YouTube×2 · Bilibili×1) — local data, not committed |
| Tests | `tests/acquire/test_capture_taxonomy.py` |

**Not changed:** access matrix · retrieve lane ceilings · UI editor · LLM compress schema · SETV/ecosystem taxonomy builders.

## 2. Orthogonality checks

| Claim | Evidence |
|-------|----------|
| Taxonomy empty → capture path assigned | unit + finalize tests |
| Existing taxonomy not overwritten | `test_finalize_does_not_overwrite_existing_taxonomy` |
| Generic capture stays `public` | finalize asserts `classification == public` |
| No derive access from path root | no code path; SoT §5 Forbidden |

## 3. Test evidence (this audit run)

Filled after pytest in the same session — see §3b.

### 3a · Commands

```powershell
cd D:\KnowledgeForge
.\.venv\Scripts\python.exe -m pytest tests -q --tb=line
.\.venv\Scripts\python.exe -m pytest tests/integration -q --tb=line
```

### 3b · Results

| Suite | Result | Notes |
|-------|--------|-------|
| Unit (`tests` ignore integration) | **166 passed** | `data/_tax_unit_20260829.log` · deprecation warning pydub only |
| Integration `tests/integration` | **14 passed · 5 skipped** | skip = `@pytest.mark.slow` without `KF_RUN_SLOW` · matrix green |

Slow optional (not required for this delta): `KF_RUN_SLOW=1 pytest tests/integration/test_slow_smoke.py`

## 4. Residual / observe

| Item | Class | Note |
|------|-------|------|
| Long YouTube ASR progress stuck at 35% | UX friction | Owner feedback; not Archive FAIL |
| Twitter / TTS | Ops ISSUE | Prior Consume UAT |
| Historical public KOs without taxonomy | Observe | Only 3 backfilled; others optional |
| `created` not parsed on KO reload | B minor | Backfill restored timestamps manually |

## 5. Disposition

```text
Engineering delta: PASS (orthogonal taxonomy fill)
Archive:           unchanged PASS
Ops:               ISSUE residual (Twitter/TTS)
Pushed:            main @ 86e8086
Unit:              166 passed (ignore integration)
Integration:       14 passed · 5 slow skipped
NEXT:              Owner UAT smoke T1–T5 — UAT_SESSION_LOG_20260829.md
Forbidden:         Matrix expand · THAW H4 · SETV scope from this change
```
