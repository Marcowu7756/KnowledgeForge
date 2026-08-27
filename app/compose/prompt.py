from __future__ import annotations

PAPER_SYSTEM = """你是学术写作助手。根据检索到的 KnowledgeObject 材料，写一篇结构化中文论文草稿。
只依据给定材料与合理推断；不要编造具体数据。若材料不足，在 unknowns 中说明。
返回严格 JSON：
{
  "title": string,
  "abstract": string,
  "sections": [
    {"heading": string, "body": string, "source_ko_ids": [string]}
  ],
  "conclusion": string,
  "references": [string],
  "unknowns": [string]
}
要求：
- 3-6 个 sections
- body 为连贯论述（每节 150-400 字），不是要点列表堆砌
- references 引用材料标题或 KO id
- 全程中文（除非专有名词）
"""

LECTURE_SYSTEM = """你是讲解稿作者。根据检索到的 KnowledgeObject 材料，写一份可朗读的讲解稿。
语气清楚、有节奏，适合口头讲述。不要编造具体数据。
返回严格 JSON：
{
  "title": string,
  "audience": string,
  "duration_hint": string,
  "outline": [string],
  "script": string,
  "key_takeaways": [string],
  "source_ko_ids": [string],
  "unknowns": [string]
}
要求：
- script 为完整口播正文 600-1200 字
- outline 4-8 条
- 全程中文（除非专有名词）
"""


def build_compose_user_prompt(
    *,
    kind: str,
    query: str,
    packs: list[dict],
) -> str:
    blocks: list[str] = [
        f"任务类型: {kind}",
        f"用户主题/问题: {query}",
        "",
        "以下是检索到的 KnowledgeObject 材料（按相关度排序）：",
        "",
    ]
    for i, pack in enumerate(packs, start=1):
        blocks.append(f"### [{i}] {pack.get('title')}")
        blocks.append(f"ko_id: {pack.get('ko_id')}")
        blocks.append(f"score: {pack.get('score')}")
        blocks.append(f"concepts: {', '.join(pack.get('concepts') or [])}")
        blocks.append("")
        blocks.append((pack.get("card_text") or pack.get("summary") or "")[:3500])
        blocks.append("")
        blocks.append("---")
        blocks.append("")
    blocks.append("请基于以上材料生成 JSON 结果。")
    return "\n".join(blocks)
