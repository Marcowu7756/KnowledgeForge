from __future__ import annotations

from typing import Any

from app.compose.models import ComposeResultMeta


def render_paper(payload: dict[str, Any], meta: ComposeResultMeta) -> str:
    lines = [
        f"# {payload.get('title') or meta.query}",
        "",
        "```yaml",
        f"kind: paper",
        f"compose_id: {meta.id}",
        f"query: {meta.query}",
        f"provider: {meta.llm_provider}",
        f"retrieve_mode: {meta.retrieve_mode}",
        f"sources: {[s.ko_id for s in meta.sources]}",
        "```",
        "",
        "## Abstract",
        "",
        str(payload.get("abstract") or "").strip(),
        "",
    ]
    for sec in payload.get("sections") or []:
        if not isinstance(sec, dict):
            continue
        heading = str(sec.get("heading") or "Section").strip()
        body = str(sec.get("body") or "").strip()
        src = sec.get("source_ko_ids") or []
        lines.append(f"## {heading}")
        lines.append("")
        if src:
            lines.append(f"_sources: {', '.join(str(x) for x in src)}_")
            lines.append("")
        lines.append(body)
        lines.append("")
    conclusion = str(payload.get("conclusion") or "").strip()
    if conclusion:
        lines.extend(["## Conclusion", "", conclusion, ""])
    refs = payload.get("references") or []
    if refs:
        lines.extend(["## References", ""])
        for r in refs:
            lines.append(f"- {r}")
        lines.append("")
    unknowns = payload.get("unknowns") or []
    if unknowns:
        lines.extend(["## Unknowns", ""])
        for u in unknowns:
            lines.append(f"- {u}")
        lines.append("")
    lines.extend(["## Retrieval evidence", ""])
    for s in meta.sources:
        lines.append(f"- `{s.score:.4f}` {s.title} (`{s.ko_id}`)")
    lines.append("")
    return "\n".join(lines)


def render_lecture(payload: dict[str, Any], meta: ComposeResultMeta) -> str:
    lines = [
        f"# {payload.get('title') or meta.query} — 讲解稿",
        "",
        "```yaml",
        f"kind: lecture",
        f"compose_id: {meta.id}",
        f"query: {meta.query}",
        f"audience: {payload.get('audience') or ''}",
        f"duration_hint: {payload.get('duration_hint') or ''}",
        f"provider: {meta.llm_provider}",
        f"retrieve_mode: {meta.retrieve_mode}",
        "```",
        "",
        "## Outline",
        "",
    ]
    for item in payload.get("outline") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Script", "", str(payload.get("script") or "").strip(), ""])
    takes = payload.get("key_takeaways") or []
    if takes:
        lines.extend(["## Key takeaways", ""])
        for t in takes:
            lines.append(f"- {t}")
        lines.append("")
    unknowns = payload.get("unknowns") or []
    if unknowns:
        lines.extend(["## Unknowns", ""])
        for u in unknowns:
            lines.append(f"- {u}")
        lines.append("")
    lines.extend(["## Sources", ""])
    for s in meta.sources:
        lines.append(f"- `{s.score:.4f}` {s.title} (`{s.ko_id}`)")
    lines.append("")
    return "\n".join(lines)
