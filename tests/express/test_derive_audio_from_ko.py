"""derive_audio_from_ko — language-specific narration from canonical KO."""

from __future__ import annotations

import pytest

from app.expression.derive import (
    AudioLanguageNotSupportedError,
    derive_audio_from_ko,
)
from app.knowledge.object import ContentBlock, KnowledgeObject, RelationEdge, SourceRef
from app.voice import bank


def _ko(
    *,
    title: str,
    summary: str = "",
    mechanisms: list[str] | None = None,
    key_points: list[str] | None = None,
    relations: list[RelationEdge] | None = None,
) -> KnowledgeObject:
    return KnowledgeObject(
        source=SourceRef(type="notes", origin="unit-test", mode="from_card"),
        content=ContentBlock(
            title=title,
            summary=summary,
            mechanisms=mechanisms or [],
            key_points=key_points or [],
        ),
        relations=relations or [],
    )


@pytest.fixture(autouse=True)
def _voice_profiles(monkeypatch):
    monkeypatch.setattr(bank, "profile_exists", lambda name: name in {"me", "me_en"})
    monkeypatch.setattr(bank, "default_voice_name", lambda: "me")


def test_zh_ko_uses_chinese_narration_and_me(sample_ko):
    ax = derive_audio_from_ko(sample_ko)

    assert ax.language == "zh-CN"
    assert ax.voice == "me"
    assert "我们来理解" not in ax.script
    assert sample_ko.content.title in ax.script
    assert sample_ko.content.summary in ax.script


def test_en_ko_uses_english_narration_and_me_en():
    ko = _ko(
        title="US Treasury yields and dollar credibility",
        summary="Rising yields weaken the dollar's safe-haven role.",
        key_points=["Reserve status is under pressure"],
    )

    ax = derive_audio_from_ko(ko)

    assert ax.language == "en"
    assert ax.voice == "me_en"
    assert "我们来理解" not in ax.script
    assert "核心关系" not in ax.script
    assert "需要抓住" not in ax.script
    assert ko.content.title in ax.script
    assert ko.content.summary in ax.script


def test_en_ko_relations_use_english_phrasing():
    ko = _ko(
        title="Italy campaign",
        summary="Strategic pressure across the peninsula.",
        relations=[
            RelationEdge.model_validate(
                {"from": "Supply lines", "to": "Rome", "type": "controls", "label": ""}
            )
        ],
    )

    ax = derive_audio_from_ko(ko)

    assert ax.language == "en"
    assert ax.voice == "me_en"
    assert "controls" in ax.script
    assert "作用于" not in ax.script


def test_unsupported_language_raises_hold_not_chinese_fallback():
    ko = _ko(
        title="ナポレオン",
        summary="イタリア戦役の概要。",
    )

    with pytest.raises(AudioLanguageNotSupportedError) as exc:
        derive_audio_from_ko(ko)

    assert exc.value.language == "ja"
    assert exc.value.ko_id == ko.id


def test_explicit_voice_override_still_respected(sample_ko):
    ax = derive_audio_from_ko(sample_ko, voice="me_en")
    assert ax.voice == "me_en"
