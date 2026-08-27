"""剧本一：获取知识 — 多源信号进入系统（单元级，不打外网/大模型）。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from app.ingest.asr import AsrError, is_audio_file
from app.ingest.audio import AudioIngestError, ingest_audio
from app.ingest.docs import ingest_file
from app.ingest.errors import FileIngestError
from app.models import IngestedSource
from app.process.cleaner import clean_text
from app.process.splitter import split_text


# --- 小剧本：本地文本文件 ---


def test_acquire_txt_file_becomes_ingested_source(tmp_path: Path):
    path = tmp_path / "note.txt"
    path.write_text("第一段。\n\n第二段关于美债。", encoding="utf-8")
    src = ingest_file(path)
    assert isinstance(src, IngestedSource)
    assert src.source_type == "txt"
    assert "美债" in src.text
    assert src.path == str(path.resolve())


def test_acquire_md_file_keeps_markdown_body(tmp_path: Path):
    path = tmp_path / "note.md"
    path.write_text("# 标题\n\n正文内容", encoding="utf-8")
    src = ingest_file(path)
    assert src.source_type == "md"
    assert "正文内容" in src.text
    assert src.title  # stem or heading-derived


def test_acquire_empty_file_rejected(tmp_path: Path):
    path = tmp_path / "empty.txt"
    path.write_text("   \n", encoding="utf-8")
    with pytest.raises(FileIngestError):
        ingest_file(path)


def test_acquire_missing_file_rejected(tmp_path: Path):
    with pytest.raises(FileIngestError):
        ingest_file(tmp_path / "nope.txt")


# --- 小剧本：清洗与切分（获取后预处理） ---


def test_acquire_clean_text_collapses_whitespace():
    raw = "a   b\r\n\r\n\r\nc"
    assert clean_text(raw) == "a b\n\nc"


def test_acquire_split_text_respects_budget():
    text = "段落一。\n\n" + ("很长。" * 200)
    chunks = split_text(text, max_chars=50)
    assert len(chunks) >= 1
    assert all(len(c) <= 50 or "。" in c for c in chunks)


# --- 小剧本：音频入口门禁（不跑 Whisper 权重） ---


def test_acquire_audio_suffix_gate():
    assert is_audio_file(Path("a.wav"))
    assert is_audio_file(Path("b.MP3"))
    assert not is_audio_file(Path("c.pdf"))


def test_acquire_audio_missing_file(tmp_path: Path):
    with pytest.raises(AudioIngestError):
        ingest_audio(tmp_path / "missing.wav")


def test_acquire_audio_unsupported_suffix(tmp_path: Path):
    bad = tmp_path / "x.txt"
    bad.write_text("nope", encoding="utf-8")
    with pytest.raises(AudioIngestError):
        ingest_audio(bad)


def test_acquire_audio_mocked_asr_builds_source(tmp_path: Path):
    wav = tmp_path / "talk.wav"
    wav.write_bytes(b"RIFF....WAVE")  # content unused due to mock
    with patch(
        "app.ingest.audio.transcribe_file",
        return_value=("这是美债测试录音。", "whisper:zh:mock"),
    ):
        src = ingest_audio(wav)
    assert src.source_type == "audio"
    assert "美债" in src.text
    assert src.metadata["transcript_source"] == "whisper"


def test_acquire_audio_asr_error_surfaces(tmp_path: Path):
    wav = tmp_path / "talk.wav"
    wav.write_bytes(b"RIFF")
    with patch(
        "app.ingest.audio.transcribe_file",
        side_effect=AsrError("whisper not ready"),
    ):
        with pytest.raises(AudioIngestError, match="whisper"):
            ingest_audio(wav)
