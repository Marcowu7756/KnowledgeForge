"""Slow integration skeleton — skipped unless KF_RUN_SLOW=1.

These tests exercise real local models (BGE / Whisper / optional compile).
Default CI and `pytest tests -q` must stay green without them.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

_RUN = os.environ.get("KF_RUN_SLOW", "").strip() in {"1", "true", "yes"}


@pytest.mark.skipif(not _RUN, reason="set KF_RUN_SLOW=1 to run slow integration tests")
def test_slow_bge_embed_one_sentence():
    from app.retrieve.embedder import embed_texts

    vecs = embed_texts(["美债与美元信用"], normalize=True)
    assert len(vecs) == 1
    assert len(vecs[0]) > 8


@pytest.mark.skipif(not _RUN, reason="set KF_RUN_SLOW=1 to run slow integration tests")
def test_slow_whisper_ready_or_skip():
    from app.local_models import whisper_ready

    if not whisper_ready():
        pytest.skip("whisper weights not pulled")
    # Smoke: API import path only; full ASR needs a wav fixture
    from app.ingest.asr import is_audio_file

    assert is_audio_file(Path("sample.wav"))
    assert not is_audio_file(Path("sample.txt"))
