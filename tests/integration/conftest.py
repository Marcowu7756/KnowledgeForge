"""Shared fixtures for slow integration tests (real local models)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app import config

# Reuse scenario cards from unit-test conftest
from tests.conftest import SAMPLE_CARD, SAMPLE_CARD_B


@pytest.fixture
def slow_wav_path() -> Path:
    """Prefer committed fixture; fall back to local inbox smoke file."""
    candidates = [
        Path(__file__).resolve().parent / "fixtures" / "smoke_audio.wav",
        config.INBOX_DIR / "smoke_audio.wav",
        config.ROOT / "data" / "inbox" / "smoke_audio.wav",
    ]
    for path in candidates:
        if path.is_file() and path.stat().st_size > 1000:
            return path
    pytest.skip(
        "no smoke wav — add tests/integration/fixtures/smoke_audio.wav "
        "or data/inbox/smoke_audio.wav"
    )


@pytest.fixture
def slow_retrieve_cards(tmp_path: Path) -> tuple[Path, Path, Path]:
    cards_dir = tmp_path / "cards"
    cards_dir.mkdir()
    card_a = cards_dir / "card_a.md"
    card_b = cards_dir / "card_b.md"
    card_a.write_text(SAMPLE_CARD, encoding="utf-8")
    card_b.write_text(SAMPLE_CARD_B, encoding="utf-8")
    index_dir = tmp_path / "retrieve"
    return card_a, card_b, index_dir
