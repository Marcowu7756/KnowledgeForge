# Integration Source Matrix — settle → express (non-Cartesian)

```yaml
as_of: 2026-08-29T11:03:51Z
rule: one express path per signal source (no Cartesian product)
runner: tests/integration/test_source_settle_express_matrix.py
pass: 13/13
fail: 0
skip: 0
```

## Matrix

| Source | Acquire | Settle | Express | Status | Detail |
|--------|---------|--------|---------|--------|--------|
| `txt` | ingest_file | pipeline.run_file→card | animate_fast(pillow) | **pass** | renderer=pillow_v1 |
| `md` | ingest_file | run_file→card | ko_animate | **pass** | ko=<pytest_tmp>/test_source_settle_express_mat0/packages/matrix_note_md_110339577328/knowledge_object.json |
| `pdf` | ingest_file/pdf | run_file→card | ko_animate | **pass** |  |
| `docx` | ingest_file/docx | run_file→card | animate_fast(pillow) | **pass** |  |
| `image` | ingest_image(mock OCR) | run_image→card | animate_fast(pillow) | **pass** |  |
| `audio` | ingest_audio(mock ASR) | run_audio→card | ko_narrate_mock | **pass** | wav=<pytest_tmp>/test_source_settle_express_mat0/packages/matrix_talk_audio_110344763357/narration.wav |
| `youtube` | run_youtube(mock ingest) | card | animate_fast | **pass** |  |
| `bilibili` | run_bilibili(mock ingest) | card | ko_animate | **pass** |  |
| `twitter` | run_twitter(mock ingest) | card | animate_fast | **pass** |  |
| `search` | search_files dry + one hit settle | run_file on hit | animate_fast(pillow) | **pass** | hits=1 |
| `ecosystem` | discover_design_docs + dry_run gate | run_file on design doc (compress mocked) | animate_fast(pillow) | **pass** | discover_hits=1 dry_hits=1 |
| `setv_snapshot` | existing cite card | compile --from-card | animate_fast(pillow) | **pass** | card=snapshot_setv_inst_aapl_d_2024.md |
| `setv_family` | family_view API resolve | N/A (read-only multi-card) | family_view | **pass** | members=3 |

## Failures (for fix loop)

_None._

## Historical problems → fixed (prior loop)

| # | Symptom | Root cause | Fix |
|---|---------|------------|-----|
| 1 | URL youtube/bilibili/twitter finalize crash | `IngestedSource` had no `.source` | `path or url or title` in `_finalize` |
| 2 | Off-root dest_dir upsert crash | hard `relative_to(ROOT)` | catch `ValueError` → absolute posix |
| 3 | Audio narrate harness reject | mock wav < 500 bytes | mock wav ≥ 500 bytes |
| 4 | Search assert empty | keyword = filename; kwargs | `search_files(..., keyword=)` + ASCII name |

Regression: `tests/acquire/test_pipeline_finalize_paths.py`

## Notes

- Not a Cartesian product: each source gets **one** express path.
- Network ingest (youtube/bilibili/twitter) mocked at ingest boundary.
- LLM compress mocked; OCR/ASR mocked.
- Audio narrate uses mocked TTS wav (real TTS remains behind `KF_RUN_SLOW`).
- SETV snapshot uses live cite card when present.
- Machine temp paths in details are redacted to `<pytest_tmp>/`.

## Re-run

```powershell
.\.venv\Scripts\python.exe -m pytest tests/integration/test_source_settle_express_matrix.py::test_source_settle_express_matrix_non_cartesian -q
$env:KF_RUN_SLOW="1"; .\.venv\Scripts\python.exe -m pytest tests/integration -q
```

Full suite audit: [`INTEGRATION_RERUN_AUDIT_20260828.md`](INTEGRATION_RERUN_AUDIT_20260828.md)

