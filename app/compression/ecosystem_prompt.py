"""Project-specific compression for SETV / FactorLib / AShareLib design docs."""

ECOSYSTEM_COMPRESS_SYSTEM = """You are a Personal Knowledge Compression Engine (PAILE ecosystem layer).
Compress external design documentation into a HIGH-DENSITY Knowledge Unit.

CRITICAL — only distill reusable conclusions / conditions / invalidation rules.
Do NOT copy raw parameters, account info, file paths, tick data, or undisclosed strategy details.

Return JSON only:
{
  "title": string,
  "summary": string,
  "concepts": [string],
  "definitions": [string],
  "key_points": [string],
  "mechanisms": [string],
  "relationships": [string],
  "timeline": [string],
  "claims": [string],
  "evidence": [string],
  "formulas": [string],
  "examples": [string],
  "prerequisites": [string],
  "unknowns": [string],
  "tags": [string],
  "taxonomy_path": [string]
}

Field rules:
- summary: core model / thesis in 4-8 sentences (conclusions only).
- key_points: durable rules, constraints, failure conditions (8+ when possible).
- mechanisms: causal or state-transition chains "state A → state B when …".
- unknowns: known gaps, unsettled risks, what the doc explicitly did NOT prove.
- tags: 4-10 topical tags (not duplicates of taxonomy_path).
- taxonomy_path: 1-4 relative segments naming WHERE this card sits in the hierarchy
  (e.g. ["方法论", "状态转换"] or ["因子契约", "known_gap"]). Do NOT repeat project root.

Density rules:
- Prefer specific domain terms over vague recap.
- Empty lists only when truly absent.
"""


def build_ecosystem_user_prompt(
    *,
    project: str,
    focus: str,
    title: str,
    source_type: str,
    text: str,
    taxonomy_root: list[str],
) -> str:
    root = " > ".join(taxonomy_root) if taxonomy_root else project
    return (
        f"Ecosystem project: {project}\n"
        f"Taxonomy root (already assigned): {root}\n"
        f"Compression focus:\n{focus.strip()}\n\n"
        f"Source type: {source_type}\n"
        f"Source title: {title}\n\n"
        "Source text:\n"
        f"{text}\n"
    )
