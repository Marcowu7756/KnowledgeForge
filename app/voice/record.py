from __future__ import annotations

from pathlib import Path

from app.voice.bank import VoiceProfile, write_profile_from_wav

DEFAULT_RECORD_SCRIPT = (
    "这是一段用于声音克隆的样本录音。"
    "我会用这个声音，把知识讲解内容朗读出来。"
)


class VoiceRecordError(RuntimeError):
    """Microphone record failed."""


def record_wav(
    dest: Path,
    *,
    seconds: float = 12.0,
    sample_rate: int = 24000,
) -> tuple[Path, float]:
    """Record mono PCM from default microphone into dest WAV."""
    try:
        import sounddevice as sd
        import soundfile as sf
    except ImportError as exc:  # pragma: no cover
        raise VoiceRecordError(
            "sounddevice/soundfile required. Run: pip install sounddevice soundfile"
        ) from exc

    seconds = max(3.0, min(float(seconds), 30.0))
    print(f"[voice] recording {seconds:.0f}s … speak clearly now", flush=True)
    audio = sd.rec(
        int(seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    dest.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(dest), audio, sample_rate)
    return dest, seconds


def transcribe_sample(wav_path: Path) -> str:
    """Use local Whisper to caption the voice sample (needed by clone TTS)."""
    from faster_whisper import WhisperModel

    from app import config

    model = WhisperModel(
        config.WHISPER_MODEL,
        device="cpu",
        compute_type="int8",
    )
    segments, _info = model.transcribe(
        str(wav_path),
        language=config.WHISPER_LANGUAGE,
        vad_filter=True,
    )
    text = " ".join(seg.text.strip() for seg in segments if seg.text and seg.text.strip())
    return text.strip()


def record_profile(
    name: str,
    *,
    seconds: float = 12.0,
    transcript: str | None = None,
    auto_transcribe: bool = False,
) -> VoiceProfile:
    from tempfile import TemporaryDirectory

    text = (transcript or "").strip()
    if not text:
        text = DEFAULT_RECORD_SCRIPT
        print("[voice] 请朗读下面这段话（尽量自然、清晰）：", flush=True)
        print(f"[voice] {text}", flush=True)

    with TemporaryDirectory(prefix="kf_voice_") as tmp:
        raw = Path(tmp) / "sample.wav"
        path, duration = record_wav(raw, seconds=seconds)
        if auto_transcribe and transcript is None:
            print("[voice] transcribing sample with Whisper …", flush=True)
            whisper_text = transcribe_sample(path)
            if whisper_text:
                text = whisper_text
        if not text.strip():
            raise VoiceRecordError(
                "transcript empty — pass --transcript or use --auto-transcribe"
            )
        return write_profile_from_wav(
            name,
            path,
            transcript=text.strip(),
            source="record",
            duration_sec=duration,
        )


def import_profile(
    name: str,
    wav_path: str | Path,
    *,
    transcript: str | None = None,
    auto_transcribe: bool = True,
) -> VoiceProfile:
    path = Path(wav_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"audio file not found: {path}")
    text = (transcript or "").strip()
    if not text and auto_transcribe:
        print("[voice] transcribing sample with Whisper …", flush=True)
        text = transcribe_sample(path)
    if not text:
        raise VoiceRecordError("transcript empty — pass --transcript")
    duration = None
    try:
        import soundfile as sf

        info = sf.info(str(path))
        duration = float(info.duration)
    except Exception:  # noqa: BLE001
        pass
    return write_profile_from_wav(
        name,
        path,
        transcript=text,
        source="import",
        duration_sec=duration,
    )
