# Ops Runbook v0 — Ingest → Index → Use → Maintain → Audit → Encrypt

```yaml
status: LANDED
as_of: 2026-08-28
audience: KF operator (local Windows)
setv_root_example: D:\fxtrading
python: .\.venv\Scripts\python.exe
head_note: H1–H3 thawed; residual HOLD = H4 chunk-RAG + SETV scope
```

Thin checklist for proprietary content fill and day-2 ops. Doctrine unchanged: **SETV → Artifact → KF cite-only**; no KF-invented `SETV-INST-*`.

| Spec | Path |
|------|------|
| Access audit | [`ACCESS_AUDIT_V0.md`](../audit/ACCESS_AUDIT_V0.md) |
| Encrypted export | [`ENCRYPTED_EXPORT_V0.md`](../audit/ENCRYPTED_EXPORT_V0.md) |
| SETV ingest | [`SETV_OPEN_KF_INGEST_V0.md`](../interop/SETV_OPEN_KF_INGEST_V0.md) |
| **Delete-only maintain** | [`KNOWLEDGE_MAINTAIN_DELETE_V0.md`](KNOWLEDGE_MAINTAIN_DELETE_V0.md) |
| Local Web UI | [`WEB_UI_v0.md`](../ui/WEB_UI_v0.md) · `main.py ui` browser-first |
| **消费 SOP（给使用者）** | [`CONSUME_USER_HANDBOOK_V0.md`](CONSUME_USER_HANDBOOK_V0.md) |
| Source matrix | [`INTEGRATION_SOURCE_MATRIX_20260828.md`](../audit/INTEGRATION_SOURCE_MATRIX_20260828.md) |
| HOLD residual | [`HOLD_THAW_SCHEDULE_V0.md`](../audit/HOLD_THAW_SCHEDULE_V0.md) · H4 + SETV SCOPE Owner Interpret `D:\fxtrading\methodology\evidence\OWNER_INTERPRET_20260828_HOLD_SETV_SCOPE.md` |

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
.\.venv\Scripts\python.exe main.py ecosystem ingest factorlib "D:\fxtrading\FactorLibDLL" --dry-run
```

### 1d · Public signal (Twitter/X single tweet · no Bearer)

```powershell
# Single public status URL — syndication (no TWITTER_BEARER_TOKEN)
.\.venv\Scripts\python.exe main.py twitter "https://x.com/<user>/status/<id>"

# Timeline needs Bearer
# $env:TWITTER_BEARER_TOKEN="..."
# .\.venv\Scripts\python.exe main.py twitter @handle --timeline --limit 5
```

If the settled card is one-off noise → delete later (section **6**). Do not invent update flows.

**Skip / escalate:** CARD without producer `SETV-INST-*` when required → Class **A** · [`PRODUCER_GAP_AAPL_INST_SIDECAR_V0.md`](../interop/PRODUCER_GAP_AAPL_INST_SIDECAR_V0.md).

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
.\.venv\Scripts\python.exe main.py retrieve query "GOLD H4 State Snapshot" --lane proprietary --top 5
.\.venv\Scripts\python.exe main.py retrieve query "GOLD H4 State Snapshot" --lane general --top 5

.\.venv\Scripts\python.exe main.py reconstruct --from-index --taxonomy-prefix "专有知识/SETV" --view taxonomy --limit 40
.\.venv\Scripts\python.exe main.py retrieve query "USDJPY" --lane proprietary --top 3 --graph data/reconstruct/<stamp>

# Optional GNN shadow blend (default OFF)
# $env:KF_GNN_BOOST="1"
# .\.venv\Scripts\python.exe main.py gnn eval --graph data/reconstruct/<stamp>
```

Family multi-card (UI or API): proprietary lane · e.g. `SETV-FAM-AAPL-TV-2024-WDH4`.

Evidence: [`USAGE_EVIDENCE_B_20260828.md`](../audit/USAGE_EVIDENCE_B_20260828.md) · [`USAGE_EVIDENCE_C_20260828.md`](../audit/USAGE_EVIDENCE_C_20260828.md) · [`USAGE_EVIDENCE_AAPL_20260828.md`](../audit/USAGE_EVIDENCE_AAPL_20260828.md)

---

## 4. Express (optional)

```powershell
.\.venv\Scripts\python.exe main.py animate <card.md> --fast --renderer auto   # manim→mpl→pillow
.\.venv\Scripts\python.exe main.py animate --golden                            # H2b smoke
.\.venv\Scripts\python.exe main.py compile <card.md> --from-card --animate --fast
```

`KF_ANIMATE_RENDERER=auto|manim|mpl|pillow`

---

## 5. Access audit

Trail: `data/audit/access/YYYYMMDD.jsonl` (gitignored / local).

```powershell
Get-Content data\audit\access\$(Get-Date -Format yyyyMMdd).jsonl | Select-Object -Last 30
.\.venv\Scripts\python.exe -c "from app.knowledge.access_audit import read_access_events; print(len(read_access_events()))"
```

---

## 6. Maintain — delete only

Full SOP: [`KNOWLEDGE_MAINTAIN_DELETE_V0.md`](KNOWLEDGE_MAINTAIN_DELETE_V0.md)

```powershell
.\.venv\Scripts\python.exe main.py knowledge delete <PATH|ID> --dry-run
.\.venv\Scripts\python.exe main.py knowledge delete <PATH|ID> --yes
```

UI: **沉淀** →「维护 · 删除」· Web UI: `python main.py ui` → http://127.0.0.1:8765.  
Audit: `data/audit/maintain/YYYYMMDD.jsonl`.

Add/update = **re-acquire**, never patch cards in place.

---

## 7. Encrypted export (leave restricted)

Plaintext external export of `local_only` / encrypted-policy cards is **blocked**. Use `.kfexport`:

```powershell
.\.venv\Scripts\python.exe main.py export encrypted data\knowledge\restricted\setv\snapshots\<card>.md
.\.venv\Scripts\python.exe main.py export decrypt data\exports\<stem>.kfexport -o data\exports\<stem>.md
```

---

## 8. One-shot bulk sequence (copy/paste)

```powershell
cd D:\KnowledgeForge
$SETV = "D:\fxtrading"

.\.venv\Scripts\python.exe main.py setv ingest --setv-root $SETV --no-index

.\.venv\Scripts\python.exe main.py index rebuild --subdir restricted
.\.venv\Scripts\python.exe main.py index rebuild
.\.venv\Scripts\python.exe main.py retrieve index --from-index --no-write-back-packages

.\.venv\Scripts\python.exe main.py retrieve query "GOLD H4 State Snapshot" --lane proprietary --top 5
Get-Content data\audit\access\$(Get-Date -Format yyyyMMdd).jsonl | Select-Object -Last 10

# drop junk card if needed:
# .\.venv\Scripts\python.exe main.py knowledge delete data\knowledge\<junk>.md --yes
```

---

## 9. Failure map (quick)

| Symptom | Class | Action |
|---------|-------|--------|
| CARD skipped · no `SETV-INST-*` | **A** Producer | Packet SETV; do not invent |
| Nested restricted missing from `units.jsonl` | **B** | `index rebuild` (rglob) + `retrieve index` |
| Soft boost / SETV clique edges | **C** | Already gated · rebuild reconstruct with default min-conf |
| `no KOs pass access filter` on general lane | Expected | Use `--lane proprietary` |
| `export blocked` plaintext | Policy | Use `export encrypted` + key |
| URL twitter finalize crash (`IngestedSource.source`) | Fixed | Upgrade past pipeline finalize path fix |
| Want to “edit” a card | Ops | Delete + re-acquire ([maintain SOP](KNOWLEDGE_MAINTAIN_DELETE_V0.md)) |
| FactorLib matched `CMakeLists.txt` | Ops | md-only discover (already fixed) |

---

## Out of scope

- Pushing restricted cards to GitHub
- Mutating SETV / inventing producer ids
- HOLD residual: **H4 chunk-RAG** · SETV SCOPE Owner Interpret `D:\fxtrading\methodology\evidence\OWNER_INTERPRET_20260828_HOLD_SETV_SCOPE.md` ([schedule](../audit/HOLD_THAW_SCHEDULE_V0.md))
- ~~HOLD 一源多卡 / Manim / GNN~~ → **LANDED** H1–H3
