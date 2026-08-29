# Audit · Taxonomy outline UI — 2026-08-29

```yaml
audit_id: KF-AUDIT-TAXONOMY-OUTLINE-UI-20260829
as_of: 2026-08-29
scope: Reconstruct + Retrieve Excel-like taxonomy outline
prior: TAXONOMY_VS_ACCESS_V0 · TAXONOMY_ACCESS_SPLIT_AUDIT_20260829
ui_version: 0.6.1
```

## 1. Change summary

| Area | Change |
|------|--------|
| Outline API | `GET /api/taxonomy/tree` · `GET /api/taxonomy/cards` |
| Builder | `app/ui/taxonomy_outline.py` — group by `taxonomy.path`, filter by access lane |
| Reconstruct UI | Collapsible outline · sets `taxonomy_prefix` · default view taxonomy |
| Retrieve UI | Same outline · prefix scopes semantic retrieve · group card list |
| Retrieve engine | `taxonomy_prefix` filter on IndexRecord.taxonomy_path |
| Health | `ui_version=0.6.1` · `features.taxonomy_outline=true` |

**Orthogonal:** lane still from access; outline never derives classification.

## 2. Test evidence

| Suite | Result | Notes |
|-------|--------|-------|
| Unit (`tests` ignore integration) | **169 passed** | `data/_tax_outline_unit_20260829.log` |
| Integration | **14 passed · 5 slow skipped** | `data/_tax_outline_integ_20260829.log` |

## 3. Disposition

```text
Engineering: PASS (outline UI + prefix filter)
Archive:     unchanged
Ops:         ISSUE residual (Twitter/TTS)
Unit:        169 passed
Integration: 14 passed · 5 slow skipped
Pushed:      main @ 4959e19
NEXT:        Owner UAT T6–T10 outline smoke
Forbidden:   H4 thaw · SETV scope · access-from-taxonomy
```
