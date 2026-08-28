"""H2b · frozen golden AnimationSchema for Manim CI/smoke.

ASCII-only labels for cross-platform font stability.
Does not consume derive manim_beats.
"""

from __future__ import annotations

from app.expression.schema import AnimationSchema, AnimationSpec, AnimationState, AnimationTransition

GOLDEN_ID = "KF-H2B-GOLDEN-V0"
GOLDEN_TITLE = "KF H2b Golden"
# Soft bounds — Manim ql GIF varies by platform/ffmpeg; not a byte-exact golden.
MIN_GIF_BYTES = 2_000
MAX_GIF_BYTES = 5_000_000


def golden_animation_schema() -> AnimationSchema:
    return AnimationSchema(
        title=GOLDEN_TITLE,
        animation=AnimationSpec(
            type="state_transition",
            states=[
                AnimationState(label="Observe", caption="archived state"),
                AnimationState(label="Evidence", caption="IT pointer"),
                AnimationState(label="Cite", caption="KF KO only"),
            ],
            transitions=[
                AnimationTransition(**{"from": 0, "to": 1, "label": "stamp"}),
                AnimationTransition(**{"from": 1, "to": 2, "label": "ingest"}),
            ],
        ),
    )
