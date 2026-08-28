# Integration Re-run Audit — 2026-08-28 (post–Web UI / HOLD nails)

```yaml
audit_id: KF-INTEG-RERUN-20260828
as_of: 2026-08-28T09:38:53Z
head: f206a0a (origin/main at run start; local evidence polish after)
command: KF_RUN_SLOW=1 pytest tests/integration -v --tb=short
duration: 65.75s
result: 19 passed · 0 failed · 0 skipped
matrix_evidence: INTEGRATION_SOURCE_MATRIX_20260828.md (+ .json)
log: data/_integ_rerun_20260828.log (local · not required in git)
```

## Verdict

\[
\boxed{19/19\ \mathrm{PASS}}
\qquad
\boxed{\mathrm{matrix\ 13/13}}
\qquad
\boxed{\mathrm{slow\ 5/5}}
\]

**No new blocking defects.** Re-run after Web UI pivot + H4/SCOPE/renderer posture nails confirms settle→express wiring and local-model smokes still green.

---

## 1. Suite breakdown

| Bucket | Tests | Result | Notes |
|--------|-------|--------|-------|
| Source settle→express matrix | 1 aggregate + 13 isolated rows = **14** | ✅ | Non-Cartesian · mocked net/LLM/OCR/ASR/TTS |
| Slow smoke (`KF_RUN_SLOW=1`) | **5** | ✅ | Real BGE embed/retrieve · Whisper transcribe/ingest |
| **Total** | **19** | ✅ | |

### Slow smoke rows

| Test | Result |
|------|--------|
| `test_slow_local_models_ready` | pass |
| `test_slow_bge_embed_one_sentence` | pass |
| `test_slow_bge_retrieve_roundtrip` | pass |
| `test_slow_whisper_transcribe_smoke_wav` | pass |
| `test_slow_whisper_ingest_audio_pipeline` | pass |

### Matrix rows (13/13)

| Source | Status | Express path |
|--------|--------|--------------|
| txt | pass | animate_fast (pillow) |
| md | pass | ko_animate |
| pdf | pass | ko_animate |
| docx | pass | animate_fast (pillow) |
| image | pass | animate_fast (pillow) |
| audio | pass | ko_narrate (mock TTS) |
| youtube | pass | animate_fast |
| bilibili | pass | ko_animate |
| twitter | pass | animate_fast |
| search | pass | animate_fast |
| ecosystem | pass | animate_fast |
| setv_snapshot | pass | compile + animate_fast (live AAPL cite) |
| setv_family | pass | family_view (members=3) |

Machine detail paths redacted → `<pytest_tmp>/` in evidence JSON/MD.

---

## 2. Problems log

### 2.1 This re-run — new failures

| ID | Severity | Status | Note |
|----|----------|--------|------|
| — | — | **None** | No assert failures · no matrix row fails |

### 2.2 This re-run — observations (non-blocking)

| ID | Class | Symptom | Assessment | Action |
|----|-------|---------|------------|--------|
| OBS-1 | Warning | `torch.jit.script` DeprecationWarning ×16 (slow smoke) | Upstream torch / embedding stack; does not fail tests | **Record only** · no KF slice · revisit if torch upgrade breaks BGE |
| OBS-2 | Hygiene | Matrix `write_evidence` previously wrote absolute `C:\Users\…\pytest-of-…` into git evidence | Local path leak in audit artifacts | **Fixed** · `_scrub_tmp_paths` in `source_matrix_lib.py` · re-scrubbed JSON |
| OBS-3 | Hygiene | Auto evidence overwrite dropped prior “Problems found → fixed” narrative | History risk on every matrix run | **Fixed** · historical table restored in writer template + this audit |

### 2.3 Prior fix loop (still closed · do not reopen)

| # | Symptom | Root cause | Fix | Regression |
|---|---------|------------|-----|------------|
| 1 | youtube/bilibili/twitter finalize crash | `IngestedSource` no `.source` | `path or url or title` | `tests/acquire/test_pipeline_finalize_paths.py` |
| 2 | Off-root upsert crash | hard `relative_to(ROOT)` | catch → absolute posix | same |
| 3 | Audio narrate reject | mock wav &lt; 500 B | mock ≥ 500 B | matrix audio row |
| 4 | Search empty | filename keyword + kwargs | ASCII hit name + `keyword=` | matrix search row |

Initial matrix campaign: 2/13 → 11/13 → 12/13 → **13/13** (documented earlier).

---

## 3. What was *not* exercised (intentional)

| Gap | Why | Gate |
|-----|-----|------|
| Live YouTube / Bilibili / Twitter network ingest | Mocked at boundary | Manual / Owner smoke when credentials allow |
| Real Ollama / cloud LLM compress | Mocked | Optional local smoke |
| Real TTS | Mocked in matrix | `KF_RUN_SLOW` does not cover TTS |
| H4 chunk retrieve | Doctrine HOLD | [`HOLD_CHUNK_RAG_H4_NAIL_20260828.md`](HOLD_CHUNK_RAG_H4_NAIL_20260828.md) |
| SETV scope expansion | Owner HOLD | `OWNER_INTERPRET_20260828_HOLD_SETV_SCOPE.md` |

---

## 4. Audit conclusions

1. **Doable integration surface remains green** after Web UI v0.6 and posture nails.  
2. **No new product defects** to open on REQ_VS_LANDED.  
3. Only follow-ups are **hygiene** (path scrub — done) and **upstream warning** OBS-1 (hold).  
4. Next value remains **consume SETV archive** · not more matrix expansion.

---

## 5. Re-run commands

```powershell
cd D:\KnowledgeForge
$env:KF_RUN_SLOW="1"
.\.venv\Scripts\python.exe -m pytest tests/integration -v --tb=short
# matrix-only:
.\.venv\Scripts\python.exe -m pytest tests/integration/test_source_settle_express_matrix.py::test_source_settle_express_matrix_non_cartesian -q
```

Cross-links: matrix [`INTEGRATION_SOURCE_MATRIX_20260828.md`](INTEGRATION_SOURCE_MATRIX_20260828.md) · REQ [`REQ_VS_LANDED_20260828.md`](REQ_VS_LANDED_20260828.md) · H4 nail [`HOLD_CHUNK_RAG_H4_NAIL_20260828.md`](HOLD_CHUNK_RAG_H4_NAIL_20260828.md)
