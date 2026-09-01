"""Voice profile language routing — me vs me_en."""

from __future__ import annotations

from app.expression.derive import _detect_language, _voice_name_for_script
from app.voice import bank


def test_voice_for_language_routes_en_to_me_en(monkeypatch):
    monkeypatch.setattr(bank, "profile_exists", lambda name: name == "me_en")
    monkeypatch.setattr(bank, "default_voice_name", lambda: "me")

    assert bank.voice_for_language("en") == "me_en"
    assert bank.voice_for_language("en-US") == "me_en"
    assert bank.voice_for_language("zh-CN") == "me"
    assert bank.voice_for_language(None) == "me"
    assert bank.voice_for_language("en", explicit="me") == "me"


def test_voice_for_language_falls_back_without_me_en(monkeypatch):
    monkeypatch.setattr(bank, "profile_exists", lambda name: False)
    monkeypatch.setattr(bank, "default_voice_name", lambda: "me")
    assert bank.voice_for_language("en") == "me"


def test_derive_script_language_picks_voice(monkeypatch):
    monkeypatch.setattr(bank, "profile_exists", lambda name: name == "me_en")
    monkeypatch.setattr(bank, "default_voice_name", lambda: "me")

    assert _detect_language("Hello world about Italy.") == "en"
    assert _detect_language("我们来理解「美债」。") == "zh-CN"
    assert _voice_name_for_script("en") == "me_en"
    assert _voice_name_for_script("zh-CN") == "me"
