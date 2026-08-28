# Integration Source Matrix — settle → express (non-Cartesian)

```yaml
as_of: 2026-08-28
rule: one express path per signal source (no Cartesian product)
runner: tests/integration/test_source_settle_express_matrix.py
pass_after_fix: 13/13
```

## Verdict

**13/13 PASS** after fix loop (initial run was 2/13 → 11/13 → 12/13 → 13/13).

## Matrix

| Source | Acquire | Settle | Express | Status |
|--------|---------|--------|---------|--------|
| `txt` | ingest_file | run_file→card | animate_fast(pillow) | **pass** |
| `md` | ingest_file | run_file→card | ko_animate | **pass** |
| `pdf` | ingest_file/pdf | run_file→card | ko_animate | **pass** |
| `docx` | ingest_file/docx | run_file→card | animate_fast(pillow) | **pass** |
| `image` | ingest_image (mock OCR) | run_image→card | animate_fast(pillow) | **pass** |
| `audio` | ingest_audio (mock ASR) | run_audio→card | ko_narrate (mock TTS) | **pass** |
| `youtube` | run_youtube (mock ingest) | card | animate_fast | **pass** |
| `bilibili` | run_bilibili (mock ingest) | card | ko_animate | **pass** |
| `twitter` | run_twitter (mock ingest) | card | animate_fast | **pass** |
| `search` | search_files (name keyword) + hit | run_file→card | animate_fast | **pass** |
| `ecosystem` | discover + dry_run + design doc | run_file→card | animate_fast | **pass** |
| `setv_snapshot` | live AAPL cite card | compile --from-card | animate_fast | **pass** |
| `setv_family` | family resolve | read-only multi-card | family_view | **pass** |

## Problems found → fixed

| # | Symptom | Root cause | Fix |
|---|---------|------------|-----|
| 1 | URL youtube/bilibili/twitter finalize crash | `_finalize` used `source.source` but `IngestedSource` has no such field | `source.path or source.url or source.title` in `app/pipeline.py` |
| 2 | Local dest_dir outside repo crashed upsert path | `md_path.relative_to(ROOT)` hard-required | catch `ValueError` → store absolute posix; same for ecosystem |
| 3 | Audio narrate harness reject | mock wav < 500 bytes | mock wav ≥ 500 bytes |
| 4 | Search assert empty | keyword must match **filename** (not body); wrong kwarg style | `search_files(roots, keyword=…)` + ASCII name `hit_gold_note.txt` |

Regression tests: `tests/acquire/test_pipeline_finalize_paths.py`

## Notes

- Not a Cartesian product: each source gets **one** express path.
- Network / LLM / OCR / ASR / TTS mocked at boundaries; SETV rows use live restricted cites.
- Real Whisper/BGE/Ollama remain behind `KF_RUN_SLOW=1` (`tests/integration/test_slow_smoke.py`).

## Re-run

```powershell
.\.venv\Scripts\python.exe -m pytest tests/integration/test_source_settle_express_matrix.py::test_source_settle_express_matrix_non_cartesian -q
```
