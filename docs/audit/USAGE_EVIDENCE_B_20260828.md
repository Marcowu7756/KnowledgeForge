# Usage Evidence Pass · Class B/C — 2026-08-28

```yaml
run_id: KF-USAGE-B-20260828
head_before: f2c5074
class_focus: B · Knowledge Gap (+ C · Relation notes)
```

## Goal

Prove settled proprietary KOs are **findable** under AccessPolicy lanes, and record what still fails as B/C (not A).

---

## B gap found & fixed

| ID | Finding | Fix |
|----|---------|-----|
| **GAP-INDEX-SHALLOW** | `index rebuild --subdir restricted` used non-recursive `glob("*.md")` — nested SETV/Factor/AShare cards never entered `units.jsonl` (stuck at ~32) | `rebuild_index` → `rglob`; after fix **111** units (**64** SETV / **79** restricted) |
| **GAP-LANE-EMPTY-MSG** | General lane on SETV-only vector index raised “empty retrieve index” | Clearer error: no KOs pass lane filter · try `--lane proprietary` |

Test: `tests/locate/test_index_rebuild_nested.py`

---

## Retrieve evidence

### Index build

| Step | Result |
|------|--------|
| `index rebuild --subdir restricted` | 111 global units |
| `retrieve index --from-index` (SETV taxonomy) | **64** vectors · dim 512 |
| `retrieve index --from-index` (full) | **111** vectors |

Logs: `_usage_index_rebuild.txt` · `_usage_retrieve_index*.txt`

### Query results (full index)

| Query | Lane | Top-1 | Verdict |
|-------|------|-------|---------|
| `GOLD H4 State Snapshot` | proprietary | **SETV-INST-GOLD-H4-2024-2026** (0.71) | ✅ B closed for this ask |
| same | general | public PAILE/grammar (≤0.45) · **no GOLD restricted** | ✅ lane fence works |
| `kernel persistence ecology…` | proprietary | L-KP / KERNEL_* evolution | ✅ |
| `Uncertainty Language SETV` | proprietary | OWNER_CONFIRM / DESIGN uncertainty | ✅ |
| `RSI Factor Spec FactorLib` | proprietary | **RSI 因子设计规范** (0.65) | ✅ Factor KO live |

CLI: `retrieve query … --lane proprietary|general` (default proprietary).

### Graph-aware note (**C**)

`kernel persistence` + SETV reconstruct graph → `graph_aware`, but several boosts show `shared_concept:(none)` / `overlap=0.00` while still applying boost. Soft Relation quality — **C · Relation Gap** to tighten later (not blocking retrieve).

---

## Reconstruct evidence

```text
reconstruct --from-index --taxonomy-prefix 专有知识/SETV --view taxonomy --limit 40
→ data/reconstruct/20260828T020053Z_8474bd3e
  kos=40  nodes=187  edges=6856
  conf: high 1639 · mid 1460 · low 3757
```

Taxonomy view builds. High low-confidence edge ratio → further **C** work (edge hygiene), not A.

---

## Classification of remaining issues

| ID | Class | Status |
|----|-------|--------|
| GAP-INDEX-SHALLOW | **B** | ✅ FIXED this pass |
| GAP-LANE-EMPTY-MSG | **B** | ✅ FIXED |
| Soft graph boost / edge density | **C** | OPEN · observe |
| AAPL INST sidecars | **A** | unchanged · SETV |
| Ops runbook | Ops | still thin |

---

## Reproduce

```powershell
.\.venv\Scripts\python.exe main.py index rebuild --subdir restricted
.\.venv\Scripts\python.exe main.py retrieve index --from-index --no-write-back-packages
.\.venv\Scripts\python.exe main.py retrieve query "GOLD H4 State Snapshot" --lane proprietary --top 5
.\.venv\Scripts\python.exe main.py retrieve query "GOLD H4 State Snapshot" --lane general --top 5
.\.venv\Scripts\python.exe main.py reconstruct --from-index --taxonomy-prefix "专有知识/SETV" --view taxonomy --limit 40
```

**Verdict:** Class **B** for “SETV/Factor KOs exist but not retrievable” is **closed** after nested index fix + usage smoke. Next value is **C** edge quality and/or **A** AAPL producer stamps — not more SETV ingest volume.
