# EVIDENCE · KnowledgeForge deep audit · 2026-09-08

```yaml
doc_id: EVIDENCE_20260908_KF_DEEP_AUDIT
as_of: 2026-09-08
status: CLOSED
verdict: PASS_WITH_ISSUES
```

## Results

| Check | Result |
|-------|--------|
| pytest tests | **8 FAILED** (AAPL/SETV proprietary archive missing) · interop slice green · suite otherwise exercises UI/distill/locate |
| interop digital_self_skills | **32 passed, 2 skipped** |
| ds list includes S24/S25 | **PASS** · 14 skills |
| ds invoke S00 | **ok** · useful |
| /api/health ui_version≥0.6.4 | **PASS** · `ui_version=0.6.4` · taxonomy_* features true |
| animate --golden | **PASS** · manim gif + ANIMATE.md |

## Failures (non-blocking for Output Layer)

Missing restricted SETV AAPL snapshots / family artifact:

- `test_distill_audio_expression_script_from_ko`
- `test_source_settle_express_matrix*` (audio / setv_family)
- `test_multi_card_h1a*` (AAPL family / compose paths)

Known gap without proprietary KO archive (~114 KO). ≠ Output Layer / S24/S25 consume failure.

## Non-claims

≠ Owner ACCEPT KF business UAT · ≠ fill proprietary archive this audit
