# Usage Evidence Pass · Class C — 20260828

```yaml
run_id: KF-USAGE-C-20260828
class_focus: C · Relation Gap
rules_version: rq_v0.4
```

## Goal

Stop soft shared_concept/shared_tag cliques and zero-affinity graph boosts from drowning retrieve / reconstruct.

---

## Fixes landed

| ID | Change | Where |
|----|--------|-------|
| **HYGIENE-STOPWORDS** | Drop generic shared labels (`SETV`, `H4`, `cite-only`, `(none)`, …) | `app/reconstruct/edge_hygiene.py` |
| **HYGIENE-FANOUT** | Cap shared_concept ≤8 / shared_tag ≤12 co-owners | same |
| **BUILD-NO-FANOUT-BOOST** | Shared-concept weight no longer scales with clique size | `app/reconstruct/build.py` |
| **RECON-DEFAULT-MINCONF** | CLI `--min-confidence` default **0.5** (drops soft tags) | `app/main.py` |
| **BOOST-AFFINITY** | Soft boost needs informative overlap or edge **label_hit**; no 0.25 floor on overlap=0 | `app/retrieve/query.py` |
| **BOOST-SKIP-GENERIC** | Retrieve ignores non-informative edge labels | same |

Tests: `tests/locate/test_relation_hygiene_c.py`

---

## Reconstruct before → after

| Metric | B pass (pre-C) | C pass |
|--------|----------------|--------|
| Graph dir | `20260828T020053Z_8474bd3e` | `20260828T021210Z_aee845d3` |
| kos / nodes | 40 / 187 | 40 / 187 |
| **edges** | **6856** | **1546** |
| high / mid / low | 1639 / 1460 / **3757** | 98 / 1448 / **0** |
| shared_concept | (clique-heavy) | **37** informative |
| shared_tag | dense | **0** (filtered) |

---

## Retrieve evidence

| Query | Graph | Observation |
|-------|-------|-------------|
| `kernel persistence` | C graph | `graph_aware` · seeds semantic-only · **no** `(none)` / overlap=0 soft boost |
| `USDJPY H4` | C graph | Top hits stay on USDJPY family · **no** EURUSD/GBPJPY boost from bare `H4` |
| `USDJPY` `--top 3` | C graph | Non-seed USDJPY evol/exp get `graph_boost` with `shared_concept:USDJPY` · **label_hit** |

Logs: `_usage_reconstruct_c.txt` · `_usage_retrieve_*_c.txt`

---

## Verdict

Class **C** soft Relation Gap for this pass is **closed**: edge density and zero-affinity boosts are gone; informative instrument links still boost.

Still open: **HOLD** items only (SETV NEXT = HOLD after AAPL stamp).
