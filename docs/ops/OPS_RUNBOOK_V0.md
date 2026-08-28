# Ops Runbook v0 — Ingest → Index → Audit → Encrypt

```yaml
status: LANDED
audience: KF operator (local Windows)
setv_root_example: D:\fxtrading
python: .\.venv\Scripts\python.exe
```

Thin checklist for proprietary content fill. Doctrine unchanged: **SETV → Artifact → KF cite-only**; no KF-invented `SETV-INST-*`.

Detail specs: [`ACCESS_AUDIT_V0.md`](../audit/ACCESS_AUDIT_V0.md) · [`ENCRYPTED_EXPORT_V0.md`](../audit/ENCRYPTED_EXPORT_V0.md) · [`SETV_OPEN_KF_INGEST_V0.md`](../interop/SETV_OPEN_KF_INGEST_V0.md)

---

## 0. Preconditions

| Check | Notes |
|-------|-------|
| venv active | `.\.venv\Scripts\python.exe` |
| SETV root readable | cite-only; KF never writes into fxtrading |
| Export key (when exporting) | `KF_EXPORT_KEY` **or** `KF_EXPORT_PASSPHRASE` |
| Access audit | ON by default · `KF_ACCESS_AUDIT=0` to disable |

```powershell
cd D:\KnowledgeForge
$env:KF_EXPORT_KEY = .\.venv\Scripts\python.exe -c "from app.knowledge.encrypted_export import generate_export_key; print(generate_export_key())"
# store the printed key securely; do not commit
```

---

## 1. Ingest (prefer `--no-index` during bulk)

Rebuild indexes once at the end — nested restricted cards need a full pass (Class B fix).

### 1a · SETV OPEN KF INGEST (preferred)

```powershell
.\.venv\Scripts\python.exe main.py setv ingest --setv-root D:\fxtrading --no-index
```

Uses `methodology/SETV/export/manifest_v0.jsonl` → sidecars. Dest: `data/knowledge/restricted/setv/{snapshots,families,evolutions,...}/`

### 1b · SETV AE-2 remainder (when not in manifest)

```powershell
.\.venv\Scripts\python.exe main.py setv measurement <paths...> --setv-root D:\fxtrading --no-index
.\.venv\Scripts\python.exe main.py setv experiment  <paths...> --setv-root D:\fxtrading --no-index
.\.venv\Scripts\python.exe main.py setv uncertainty <paths...> --setv-root D:\fxtrading --no-index
```

### 1c · Ecosystem (LLM compile · conclusions only)

```powershell
.\.venv\Scripts\python.exe main.py ecosystem ingest factorlib "D:\fxtrading\FactorLibDLL" --limit 5 --no-index
.\.venv\Scripts\python.exe main.py ecosystem ingest asharelib "D:\fxtrading\docs\design" --limit 8 --no-index
# dry-run first if unsure:
.\.venv\Scripts\python.exe main.py ecosystem ingest factorlib "D:\fxtrading\FactorLibDLL" --dry-run
```

**Skip / escalate:** AAPL CARD without `SETV-INST-*` → Class **A** · see [`PRODUCER_GAP_AAPL_INST_SIDECAR_V0.md`](../interop/PRODUCER_GAP_AAPL_INST_SIDECAR_V0.md). Do not invent ids.

---

## 2. Index rebuild + retrieve vectors

Always use recursive rebuild for restricted trees:

```powershell
.\.venv\Scripts\python.exe main.py index rebuild --subdir restricted
.\.venv\Scripts\python.exe main.py index rebuild
.\.venv\Scripts\python.exe main.py retrieve index --from-index --no-write-back-packages
```

Sanity:

| Expect | Typical after content fill |
|--------|----------------------------|
| Global units | ~100+ (incl. SETV nested) |
| Restricted SETV vectors | tens (taxonomy filter if used) |

Empty proprietary retrieve → try `--lane proprietary` (default); general lane correctly excludes restricted.

---

## 3. Use / verify (optional but recommended)

```powershell
# Lane fence
.\.venv\Scripts\python.exe main.py retrieve query "GOLD H4 State Snapshot" --lane proprietary --top 5
.\.venv\Scripts\python.exe main.py retrieve query "GOLD H4 State Snapshot" --lane general --top 5

# Graph-aware (after reconstruct)
.\.venv\Scripts\python.exe main.py reconstruct --from-index --taxonomy-prefix "专有知识/SETV" --view taxonomy --limit 40
# note output dir under data/reconstruct/<stamp>/
.\.venv\Scripts\python.exe main.py retrieve query "USDJPY" --lane proprietary --top 3 --graph data/reconstruct/<stamp>
```

Relation quality defaults: reconstruct `--min-confidence` **0.5**; soft graph boost needs informative affinity (Class C).

Evidence templates: [`USAGE_EVIDENCE_B_20260828.md`](../audit/USAGE_EVIDENCE_B_20260828.md) · [`USAGE_EVIDENCE_C_20260828.md`](../audit/USAGE_EVIDENCE_C_20260828.md)

---

## 4. Access audit

Trail: `data/audit/access/YYYYMMDD.jsonl` (gitignored / local).

```powershell
Get-Content data\audit\access\$(Get-Date -Format yyyyMMdd).jsonl | Select-Object -Last 30
.\.venv\Scripts\python.exe -c "from app.knowledge.access_audit import read_access_events; print(len(read_access_events()))"
```

Expect lines on retrieve filter / compose deny / export encrypted. Not a SIEM.

---

## 5. Encrypted export (leave restricted)

Plaintext external export of `local_only` / encrypted-policy cards is **blocked**. Use `.kfexport`:

```powershell
.\.venv\Scripts\python.exe main.py export encrypted data\knowledge\restricted\setv\snapshots\<card>.md
.\.venv\Scripts\python.exe main.py export decrypt data\exports\<stem>.kfexport -o data\exports\<stem>.md
```

HTTP: `GET /api/export/encrypted?path=...`  
Secret / deny → always blocked.

---

## 6. One-shot bulk sequence (copy/paste)

```powershell
cd D:\KnowledgeForge
$SETV = "D:\fxtrading"

.\.venv\Scripts\python.exe main.py setv ingest --setv-root $SETV --no-index
# optional AE-2 / ecosystem batches with --no-index …

.\.venv\Scripts\python.exe main.py index rebuild --subdir restricted
.\.venv\Scripts\python.exe main.py index rebuild
.\.venv\Scripts\python.exe main.py retrieve index --from-index --no-write-back-packages

.\.venv\Scripts\python.exe main.py retrieve query "GOLD H4 State Snapshot" --lane proprietary --top 5
Get-Content data\audit\access\$(Get-Date -Format yyyyMMdd).jsonl | Select-Object -Last 10

# when leaving the machine with a restricted card:
# $env:KF_EXPORT_KEY = "..."
# .\.venv\Scripts\python.exe main.py export encrypted <path-to-md>
```

---

## 7. Failure map (quick)

| Symptom | Class | Action |
|---------|-------|--------|
| CARD skipped · no `SETV-INST-*` | **A** Producer | Packet SETV; do not invent |
| Nested restricted missing from `units.jsonl` | **B** | `index rebuild` (rglob) + `retrieve index` |
| Soft boost / SETV clique edges | **C** | Already gated · rebuild reconstruct with default min-conf |
| `no KOs pass access filter` on general lane | Expected | Use `--lane proprietary` |
| `export blocked` plaintext | Policy | Use `export encrypted` + key |
| FactorLib matched `CMakeLists.txt` | Ops | md-only discover (already fixed) |

---

## Out of scope

- Pushing restricted cards to GitHub
- Mutating SETV / inventing producer ids
- HOLD: 一源多卡 / Manim / GNN / chunk-RAG
