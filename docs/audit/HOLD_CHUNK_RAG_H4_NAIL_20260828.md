# Note · H4 HOLD-CHUNK-RAG (doctrine nail)

```yaml
status: NAILED · HOLD
as_of: 2026-08-28
action: none — no H4a · no chunk index · no chat UI
owner: KF (SETV = NO ACTION)
```

## Doctrine

\[
\boxed{\mathrm{Retrieve\ Unit = KnowledgeObject}}
\]

This is a **doctrine-level** constraint, not “chunk not built yet.”

```text
Source → KnowledgeObject → Index → Retrieve → Compose
```

**Not** Source → Chunks → Chunk RAG → Chat.

\[
\boxed{\mathrm{KnowledgeObject = Knowledge\ SoT}}
\]

Chunk must never invert the architecture into Document → Chunk → Answer (KO demoted to “chunk feedstock”).

If chunk is ever allowed:

\[
\boxed{\mathrm{KO \rightarrow Chunk\ Index}\ (aux)}
\qquad
\boxed{\mathrm{not\ Chunk \rightarrow replace\ KO}}
\]

## Freeze table

| Item | Status |
|------|--------|
| Retrieve unit | **KO** |
| Chunk index | absent |
| Chunk retrieval | absent |
| Chat UI | absent |
| SETV action / output | **none** |
| Default after thaw | still **KO** |
| Chunk after thaw | **opt-in** auxiliary only |

## Why HOLD matters

Industry “everyone does RAG” is **not** a thaw trigger. Consume-first:

\[
\boxed{
\mathrm{real\ ask}
\rightarrow
\mathrm{KO\ retrieval\ failure}
\rightarrow
\mathrm{typed\ evidence}
\rightarrow
\mathrm{then\ discuss\ chunk}
}
\]

Example of meaningful evidence: KO content is correct, but the ask maps to a tiny span and whole-card recall causes semantic competition / clear precision loss.

## Thaw (both required)

1. Owner **doctrine amendment** + `THAW HOLD-CHUNK-RAG` (plan: `… H4a`)
2. Real KO-insufficiency evidence for a class of asks

Then only: **H4a** unit dualism + audit → **H4b** chunk sidecar → **H4c** `retrieve --unit chunk` opt-in · default KO unchanged.

Out of scope: raw chunk paste as SoT; silent default flip; bending SETV Artifact / fields for chunk.

## SETV

\[
\boxed{\mathrm{H4\ thaw \neq SCOPE\ thaw}}
\]

H4 is KF retrieval architecture. SETV stays `SETV → Artifact`; KF owns `Artifact → KO → Retrieval`.

## Correct next action

\[
\boxed{\mathrm{HOLD}}
\]

Consume SETV Family + Instance + Evidence. Do not invent demand from the word “RAG.”

Schedule: [`HOLD_THAW_SCHEDULE_V0.md`](HOLD_THAW_SCHEDULE_V0.md) · Scope peer: `D:\fxtrading\methodology\evidence\OWNER_INTERPRET_20260828_HOLD_SETV_SCOPE.md`
