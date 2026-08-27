"""Slow integration — real BGE / Whisper smoke (KF_RUN_SLOW=1).

Default `pytest tests -q` skips these via @pytest.mark.slow + skipif.
Run:

    $env:KF_RUN_SLOW="1"
    .\.venv\Scripts\python.exe -m pytest tests/integration -q
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.local_models import embed_ready, whisper_ready

pytestmark = pytest.mark.slow

_RUN = os.environ.get("KF_RUN_SLOW", "").strip().lower() in {"1", "true", "yes", "on"}


def _require_slow() -> None:
    if not _RUN:
        pytest.skip("set KF_RUN_SLOW=1 to run slow integration tests")


@pytest.fixture(autouse=True)
def _slow_gate():
    _require_slow()


def test_slow_local_models_ready():
    """Gate: both BGE and Whisper weights must be pulled before deeper smokes."""
    if not embed_ready():
        pytest.skip("embed model not ready — python main.py models pull --only embed")
    if not whisper_ready():
        pytest.skip("whisper model not ready — python main.py models pull --only whisper")
    assert embed_ready()
    assert whisper_ready()


def test_slow_bge_embed_one_sentence():
    from app.retrieve.embedder import embed_texts

    if not embed_ready():
        pytest.skip("embed model not ready")

    vecs = embed_texts(["美债与美元信用"], normalize=True)
    assert len(vecs) == 1
    assert len(vecs[0]) > 8
    # Normalized → unit length (~1.0)
    norm = float((vecs[0] ** 2).sum() ** 0.5)
    assert 0.95 <= norm <= 1.05


def test_slow_bge_retrieve_roundtrip(slow_retrieve_cards):
    from app.retrieve.index_build import build_ko_index
    from app.retrieve.query import retrieve_kos

    if not embed_ready():
        pytest.skip("embed model not ready")

    card_a, card_b, index_dir = slow_retrieve_cards
    manifest, kos, _writeback = build_ko_index(
        paths=[str(card_a), str(card_b)],
        dest=index_dir,
    )
    assert manifest.count == 2
    assert len(kos) == 2

    result = retrieve_kos("美债与美元信用", top_k=2, index_dir=index_dir)
    assert result.hits
    top = result.hits[0]
    assert top.semantic_score > 0.2
    assert "美债" in top.title or any("美债" in c for c in top.concepts)


def test_slow_whisper_transcribe_smoke_wav(slow_wav_path: Path):
    from app.ingest.asr import is_audio_file, transcribe_file

    if not whisper_ready():
        pytest.skip("whisper weights not pulled")

    assert is_audio_file(slow_wav_path)
    text, tag = transcribe_file(slow_wav_path)
    assert text.strip()
    assert len(text.strip()) >= 4
    assert tag.startswith("whisper:")


def test_slow_whisper_ingest_audio_pipeline(slow_wav_path: Path, monkeypatch, tmp_path: Path):
    """End-to-end: wav → ingest_audio → non-empty transcript text."""
    from app import config
    from app.ingest.audio import ingest_audio

    if not whisper_ready():
        pytest.skip("whisper weights not pulled")

    monkeypatch.setattr(config, "RAW_DIR", tmp_path / "raw")
    (tmp_path / "raw").mkdir(parents=True, exist_ok=True)

    source = ingest_audio(slow_wav_path)
    assert source.source_type == "audio"
    assert source.text.strip()
    assert source.metadata.get("transcript_source") == "whisper"
