"""Shared fixtures for KnowledgeForge scenario unit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.knowledge.object import (
    ContentBlock,
    KnowledgeObject,
    RelationEdge,
    SourceRef,
)
from app.models import KnowledgeUnit


SAMPLE_CARD = """# 美债与美元信用

```yaml
id: testko001abc
title: 美债与美元信用
source: unit-test
type: notes
tags: ["金融", "美债"]
```

## Core Idea

美债收益率上升削弱美元避险属性。

## Concepts

- 美债
- 美元
- 避险资产

## Mechanisms

- 美债收益率上升 → 美股疲软 → 避险情绪上升

## Relationship

- 美债收益率上升 → 美股疲软
- 全球化逆转 → 产业空心化

## Timeline

- 2008年 — 危机后收益率走低
- 2026年 — 信用担忧上升

## Key Points

- 美元储备地位受到挑战
- 黄金与比特币上涨

## Prerequisites

- 了解国债收益率基础
"""


SAMPLE_CARD_B = """# 石油美元机制

```yaml
id: testko002def
title: 石油美元机制
source: unit-test
type: notes
tags: ["金融", "石油美元"]
```

## Core Idea

石油交易锚定美元支撑储备货币地位。

## Concepts

- 石油美元
- 美元
- 储备货币

## Mechanisms

- 石油计价美元化 → 美元需求上升 → 储备地位巩固

## Relationship

- 石油美元 → 美元高估值
"""


@pytest.fixture
def tmp_card(tmp_path: Path) -> Path:
    path = tmp_path / "card_a.md"
    path.write_text(SAMPLE_CARD, encoding="utf-8")
    return path


@pytest.fixture
def tmp_cards(tmp_path: Path) -> list[Path]:
    a = tmp_path / "card_a.md"
    b = tmp_path / "card_b.md"
    a.write_text(SAMPLE_CARD, encoding="utf-8")
    b.write_text(SAMPLE_CARD_B, encoding="utf-8")
    return [a, b]


@pytest.fixture
def sample_unit() -> KnowledgeUnit:
    return KnowledgeUnit(
        id="testko001abc",
        title="美债与美元信用",
        source="unit-test",
        type="notes",
        summary="美债收益率上升削弱美元避险属性。",
        concepts=["美债", "美元", "避险资产"],
        mechanisms=["美债收益率上升 → 美股疲软 → 避险情绪上升"],
        relationships=["美债收益率上升 → 美股疲软"],
        timeline=["2008年 — 危机后收益率走低", "2026年 — 信用担忧上升"],
        key_points=["美元储备地位受到挑战"],
        prerequisites=["了解国债收益率基础"],
        tags=["金融", "美债"],
    )


@pytest.fixture
def sample_ko(sample_unit: KnowledgeUnit) -> KnowledgeObject:
    from app.knowledge.object import from_knowledge_unit

    return from_knowledge_unit(
        sample_unit,
        source=SourceRef(type="notes", origin="unit-test", mode="from_card"),
        knowledge_md="card_a.md",
    )


@pytest.fixture
def two_kos(tmp_cards: list[Path]) -> list[KnowledgeObject]:
    from app.knowledge.parse import load_knowledge_object

    return [load_knowledge_object(p) for p in tmp_cards]
