# Posture Nail · 2026-08-28

```yaml
status: NAILED
authority: SETV Owner + KF consume evidence
next: HOLD
```

\[
\boxed{\mathrm{AAPL\ Per\text{-}TF\ Instance = CLOSED}}
\qquad
\boxed{\mathrm{NEXT = HOLD}}
\qquad
\boxed{\mathrm{Producer\ ID > KF\ cite\text{-}only}}
\]

## Verified closed chain (AAPL)

```text
SETV Family SETV-FAM-AAPL-TV-2024-WDH4
  + INST W/D/H4 (producer-stamped)
  → export.json → KF cite → KO → Index → Retrieval
```

Query proof: `AAPL H4 State Snapshot` · proprietary · Top-3 = AAPL W/H4/D INST  
Evidence: [`USAGE_EVIDENCE_AAPL_20260828.md`](USAGE_EVIDENCE_AAPL_20260828.md)

Three asset layers in KF: **Family** · **Instance** · **Evidence** (sidecar + IT + contract trail).

## Program board (nail)

| Track | Status |
|-------|--------|
| P0 Foundation | CLOSED |
| P1 Expression | CLOSED |
| P2 Reconstruction | LANDED |
| P3 Retrieval | LANDED |
| SETV Content Fill | LANDED |
| AAPL Family | CLOSED |
| AAPL W/D/H4 Instances | CLOSED |
| SETV → KF Retrieval | VERIFIED |
| SETV scope expansion | **HOLD** |
| Tech HOLD residual | **H4** chunk-RAG · [`HOLD_THAW_SCHEDULE_V0.md`](HOLD_THAW_SCHEDULE_V0.md) |
| H1 一源多卡 / H2 Manim(+mpl) / H3 GNN | ✅ thawed & LANDED (2026-08-28) |

Global archive size at nail: **114** knowledge units (SETV state archive forming — not scattered files).

## What NOT to do next

- Do not ask SETV for new axes / metrics / scopes / instance types because AAPL succeeded
- Do not invent `SETV-INST-*` in KF
- Do not reopen Measurement / Forecast for archive growth

## What TO do next

**Consume** settled SETV knowledge inside KF. Let real questions surface gaps, then classify:

```text
B Knowledge Gap  |  C Relation Gap  |  A Producer Gap  |  D Representation Gap
```

Only **D** (settled but still unanswerable) re-enters SETV evolution discussion.

Value question for this HOLD window:

> What fails when we *use* the archive — and is that failure A, B, C, or D?

Day-2 ops: [`OPS_RUNBOOK_V0.md`](../ops/OPS_RUNBOOK_V0.md) · delete-only: [`KNOWLEDGE_MAINTAIN_DELETE_V0.md`](../ops/KNOWLEDGE_MAINTAIN_DELETE_V0.md)


> When KF truly holds these SETV historical states, what can it discover from them?

That is where **SETV → KF → SETV Evolution** starts earning its keep.
