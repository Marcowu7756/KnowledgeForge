"""UI narrate endpoint — KO → same-language audio."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.expression.derive import AudioLanguageNotSupportedError
from app.expression.objects import AudioExpression, ExpressionEvidence
from app.ui.server import create_app


def test_narrate_api_returns_wav_metadata(monkeypatch, tmp_path):
    client = TestClient(create_app())
    wav = tmp_path / "narration.wav"
    wav.write_bytes(b"RIFF" + b"\0" * 40)

    class FakeResult:
        expression = AudioExpression(
            id="ax_test",
            source_ko="ko_test",
            script="美债与美元信用。",
            voice="me",
            language="zh-CN",
            evidence=ExpressionEvidence(derived_from="ko_test"),
        )
        expression_path = tmp_path / "audio_expression.json"
        wav_path = wav

    monkeypatch.setattr(
        "app.ui.actions.run_narrate_ko",
        lambda path, progress=None: {
            "ok": True,
            "ko_id": "ko_test",
            "language": "zh-CN",
            "voice": "me",
            "script": "美债与美元信用。",
            "wav": "expression/ui_narrate/ko_test/narration.wav",
            "expression": "data/expression/ui_narrate/ko_test/audio_expression.json",
        },
    )

    res = client.post("/api/narrate", json={"path": "data/knowledge/test.md"})
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["language"] == "zh-CN"
    assert body["voice"] == "me"
    assert "美债" in body["script"]


def test_narrate_api_language_hold_is_422(monkeypatch):
    client = TestClient(create_app())

    def _hold(path, progress=None):
        raise AudioLanguageNotSupportedError("ja", ko_id="ko_ja")

    monkeypatch.setattr("app.ui.actions.run_narrate_ko", _hold)
    res = client.post("/api/narrate", json={"path": "data/knowledge/ja.md"})
    assert res.status_code == 422
    assert "HOLD" in res.json()["detail"] or "not supported" in res.json()["detail"]


def test_health_ko_narrate_feature_flag():
    client = TestClient(create_app())
    body = client.get("/api/health").json()
    assert body["ui_version"] == "0.6.4"
    assert body["features"]["ko_narrate_preview"] is True
