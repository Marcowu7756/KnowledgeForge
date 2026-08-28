# Access Governance Audit Trail v0

**Status:** LANDED  
**Module:** `app/knowledge/access_audit.py`  
**Default:** ON (`KF_ACCESS_AUDIT=0` to disable)

## Purpose

With real proprietary assets in KF (SETV · FactorLib · AShareLib), every
retrieve / compose / expression / export decision gets a **local append-only**
JSONL line. This is governance evidence — not a vault, not synced to SETV.

## Layout

```text
data/audit/access/YYYYMMDD.jsonl
```

One object per line (`AccessAuditEvent`).

| Field | Meaning |
|-------|---------|
| `action` | `retrieve` · `compose` · `expression` · `export` |
| `outcome` | `allow` · `deny` · `filter` · `warning` |
| `classification` / `source_project` / `ko_id` / `path` | subject |
| `lane` / `llm_provider` | context |
| `mode` / `reason` | gate result |
| `detail` | batch counts, etc. |

## Wired call sites

| Site | What is logged |
|------|----------------|
| `retrieve/query.py` | Index filter summary (allowed / denied_by_class) |
| `compose/engine.py` | Per-blocked KO + batch summary |
| `path_access.gate_preview` | Expression gate |
| `path_access.gate_export` | Expression + export gates (UI `/api/export`) |

## Inspect

```powershell
Get-Content data\audit\access\*.jsonl | Select-Object -Last 20
# or
.\.venv\Scripts\python.exe -c "from app.knowledge.access_audit import read_access_events; print(len(read_access_events()))"
```

## Not in scope (v0)

- Encrypted export payload (still `encrypted_export_unimplemented`)
- Remote SIEM / push to GitHub
- Per-token LLM prompt redaction beyond KO-level compose filter
