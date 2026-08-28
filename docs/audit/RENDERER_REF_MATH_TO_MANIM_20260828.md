# Note · Math To Manim = External Renderer Reference (no product path)

```yaml
status: NAILED · OBSERVE ONLY
as_of: 2026-08-28
action: none — no slice · no Expression change · no integration
```

## Accurate pipeline (current)

\[
\boxed{
\mathrm{KO}
\rightarrow
\mathrm{ExpressionObject}
\rightarrow
\mathrm{Beats}
\rightarrow
\mathrm{Renderer}
\rightarrow
\mathrm{Artifact}
}
\]

H2 renderers already exist (position = **Renderer only**):

```text
manim_v0 → mpl_v0 → Pillow
```

Pillow GIF remains the primary knowledge-visualization path. GIF 优先；默认不做视频产品化。

## Freeze table

| Item | Status |
|------|--------|
| KO → ExpressionObject | ✅ CLOSED |
| Expression → Beats | 既有架构 |
| H2 Manim / mpl | ✅ LANDED (renderer) |
| Pillow GIF | ✅ 动图主路径 |
| GIF 优先 | ✅ 保持 |
| derive `manim_beats` → Expression | ⏸ DEFER · `not_wired_to_expression` |
| Math To Manim product path | ❌ 不追 |
| LLM → `scene.py` | ❌ 不采用 |
| Bend Expression around Manim | ❌ 不允许 |

## Principle

\[
\boxed{
\mathrm{Semantic}
\rightarrow
\mathrm{VisualExpression}
\rightarrow
\mathrm{Beats}
\rightarrow
\mathrm{Renderer}
}
\]

**Not** Semantic → LLM → Manim code. Renderer follows Expression; Expression does not bend around a renderer.

## Math To Manim positioning

> **External Renderer Reference / No Product Path**

Validates that semantic → motion visualization is feasible. Does **not** change KnowledgeForge Contract, Expression, or priorities.

## Correct next action

\[
\boxed{\mathrm{HOLD}}
\]

Continue观察. Revisit `manim_beats → Expression` (or richer media) only when **real consume evidence** shows current VisualExpression + Pillow cannot express a needed process — or when video production cost collapses enough to justify a media-tier path. Until then: remark only, no design, no落地.

Cross-links: [`HOLD_THAW_SCHEDULE_V0.md`](HOLD_THAW_SCHEDULE_V0.md) H2 · [`POSTURE_NAIL_20260828.md`](POSTURE_NAIL_20260828.md)
