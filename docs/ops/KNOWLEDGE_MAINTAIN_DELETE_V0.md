# Knowledge Maintain — Delete Only v0

```yaml
status: LANDED
as_of: 2026-08-28
commit: 0f68a4c+
rule: 只删 · 不增 · 不改；新增/更新 = 重新获取
```

## Doctrine

Settled knowledge that is junk or unimportant may be **removed**.  
There is **no** in-place edit / patch API for cards.

| Need | Do this |
|------|---------|
| New knowledge | Re-acquire (twitter / file / setv / …) → compress → card |
| Refresh / correct | Re-acquire the same source (or better source) → new card; delete old if obsolete |
| Remove junk | `knowledge delete` |

## Safety rails

- Only paths under `data/knowledge/**`
- Never deletes `INDEX.md` / `README.md`
- Prunes global + local indexes
- By default also prunes matching **retrieve** vector rows (`--keep-retrieve` to skip)
- Audit trail: `data/audit/maintain/YYYYMMDD.jsonl` (local / gitignored)

## CLI

```powershell
cd D:\KnowledgeForge

# Preview (no delete)
.\.venv\Scripts\python.exe main.py knowledge delete <PATH|ID> --dry-run

# Delete one or many (interactive confirm)
.\.venv\Scripts\python.exe main.py knowledge delete data\knowledge\<card>.md
.\.venv\Scripts\python.exe main.py knowledge delete <unit_id>

# Non-interactive (scripts / Owner-approved)
.\.venv\Scripts\python.exe main.py knowledge delete data\knowledge\<card>.md --yes

# Keep retrieve vectors (rare; then rebuild retrieve yourself)
.\.venv\Scripts\python.exe main.py knowledge delete data\knowledge\<card>.md --yes --keep-retrieve
```

Confirm prompt expects the word `DELETE` unless `--yes`.

## HTTP / UI

| Surface | How |
|---------|-----|
| API | `DELETE /api/knowledge` body `{ "paths": ["..."], "dry_run": false, "prune_retrieve": true }` |
| UI | Workshop → **沉淀** →「维护 · 删除」→ confirm |

Health flag: `features.knowledge_delete: true`

## After delete

Usually nothing else required. If you used `--keep-retrieve` or suspect stale graph:

```powershell
.\.venv\Scripts\python.exe main.py retrieve index --from-index --no-write-back-packages
# optional reconstruct refresh if graph cited the deleted KO
```

## Example (Twitter junk / one-off signal)

```powershell
# Settle
.\.venv\Scripts\python.exe main.py twitter "https://x.com/elonmusk/status/<id>"

# Later: decide not to keep → delete card only
.\.venv\Scripts\python.exe main.py knowledge delete data\knowledge\<stem>.md --yes
```

Raw under `data/raw/` is **not** auto-deleted (audit/repro). Delete raw manually if needed.

## Out of scope

- Bulk “smart” importance ranking
- Soft-delete / recycle bin UI
- Editing card YAML in forms
- Deleting packages / expression artifacts (separate hygiene)

## Cross-links

- Ops master: [`OPS_RUNBOOK_V0.md`](OPS_RUNBOOK_V0.md)
- Matrix: [`REQ_VS_LANDED_20260828.md`](../audit/REQ_VS_LANDED_20260828.md)
- UI: [`WINDOWS_UI_v0.md`](../ui/WINDOWS_UI_v0.md)
- Code: `app/knowledge/maintain.py`
