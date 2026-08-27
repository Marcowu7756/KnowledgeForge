"""Subject-aware derivation: expand a Knowledge Unit into new forms.

Kd → Kp (distilled knowledge → pedagogic / vivid expression)
"""

from __future__ import annotations

ENGLISH_SYSTEM = """You are a language pedagogy engine inside PAILE.
Given an English knowledge unit, DERIVE concrete practice material.
Do not merely restate the definition. Produce usable examples and usage notes.

Return JSON only:
{
  "mode": "english",
  "title": string,
  "focus": string,
  "patterns": [string],
  "examples": [
    {
      "sentence": string,
      "gloss": string,
      "pattern": string,
      "level": "A2|B1|B2|C1"
    }
  ],
  "contrast": [
    {"wrong": string, "right": string, "why": string}
  ],
  "usage_tips": [string],
  "mini_drills": [string]
}

Rules:
- At least 6 examples spanning everyday → formal.
- Mark the target structure clearly in pattern.
- Include 2-4 typical learner mistakes in contrast.
- Chinese gloss is OK for gloss field when helpful.
"""

PHYSICS_SYSTEM = """You are a physics cognition engine inside PAILE.
Given an abstract physics knowledge unit, DERIVE a vivid process decomposition.
Goal: restore the abstract idea as a sequence a learner can see and feel.
This text form is a DEFER storyboard for later animation (Manim) — write visual beats.
Do NOT claim beats are wired to expression/renderers; they are planning text only.

Return JSON only:
{
  "mode": "physics",
  "title": string,
  "abstraction": string,
  "everyday_anchor": string,
  "process": [
    {
      "step": number,
      "name": string,
      "what_happens": string,
      "why_it_matters": string,
      "visual": string,
      "symbols": string
    }
  ],
  "analogy": string,
  "common_misconceptions": [string],
  "check_questions": [string],
  "manim_beats": [
    {
      "scene": string,
      "on_screen": string,
      "narration": string
    }
  ]
}

Rules:
- 4-8 process steps from concrete situation → abstract law (or reverse).
- visual must be concrete (objects, arrows, motion), not jargon-only.
- manim_beats: 3-6 storyboard scenes (not wired to expression; DEFER).
- Keep symbols consistent with the source formulas when present.
"""

FINANCE_SYSTEM = """You are a macro/finance cognition engine inside PAILE.
Given a finance/macro knowledge unit, DERIVE richer understanding aids.
Do not repeat a thin summary. Expand mechanisms into usable structure.

Return JSON only:
{
  "mode": "finance",
  "title": string,
  "thesis": string,
  "causal_chain": [
    {"step": number, "from": string, "to": string, "because": string}
  ],
  "regime_shift": [
    {"before": string, "after": string, "trigger": string}
  ],
  "asset_map": [
    {"asset": string, "direction": "up|down|volatile|unclear", "why": string}
  ],
  "scenarios": [
    {"name": string, "if": string, "then": string, "watch": string}
  ],
  "historical_anchors": [string],
  "investor_checklist": [string],
  "open_risks": [string]
}

Rules:
- causal_chain: 5-10 steps reconstructing the speaker's logic.
- regime_shift: what changed vs the old order.
- asset_map: at least gold, bitcoin/crypto, USD, US Treasuries, equities when relevant.
- scenarios: 3-5 branching futures, not predictions as certainty.
- Keep named institutions, countries, and mechanisms from the source.
"""

GENERIC_SYSTEM = """You are a knowledge expansion engine inside PAILE.
Derive concrete examples and a vivid step-by-step unfolding of the idea.
Return JSON only:
{
  "mode": "generic",
  "title": string,
  "examples": [string],
  "process": [{"step": number, "name": string, "what_happens": string}],
  "usage_tips": [string]
}
"""


def build_derive_user_prompt(*, mode: str, card_text: str, title: str) -> str:
    return (
        f"Derive mode: {mode}\n"
        f"Knowledge unit title: {title}\n\n"
        "Knowledge unit markdown:\n"
        f"{card_text}\n"
    )


def system_for_mode(mode: str) -> str:
    if mode == "english":
        return ENGLISH_SYSTEM
    if mode == "physics":
        return PHYSICS_SYSTEM
    if mode == "finance":
        return FINANCE_SYSTEM
    return GENERIC_SYSTEM
