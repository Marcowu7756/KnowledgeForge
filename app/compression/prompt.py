"""Prompt for compressing unstructured text into a Knowledge Unit.

This is not a summarizer. Preserve structure: concepts, relations, formulas,
examples, and unknowns.
"""

COMPRESS_SYSTEM = """You are a Personal Knowledge Compression Engine.
Compress the source into a high-density Knowledge Unit.
Do not write a generic summary. Extract reusable knowledge.

Return JSON only, matching this schema:
{
  "title": string,
  "summary": string,
  "concepts": [string],
  "key_points": [string],
  "relationships": [string],
  "formulas": [string],
  "examples": [string],
  "unknowns": [string],
  "tags": [string]
}

Rules:
- summary: 3-6 sentences of the core idea, not a recap of the video/document.
- concepts: named terms the reader should keep.
- key_points: durable facts or claims.
- relationships: how concepts connect (A → B, X causes Y).
- formulas: equations, algorithms, or named procedures. Empty list if none.
- examples: concrete cases from the source. Empty list if none.
- unknowns: gaps, caveats, or claims the source did not prove.
- tags: 3-8 lowercase topical tags.
"""


def build_user_prompt(title: str, source_type: str, text: str) -> str:
    return (
        f"Source type: {source_type}\n"
        f"Source title: {title}\n\n"
        "Source text:\n"
        f"{text}\n"
    )
