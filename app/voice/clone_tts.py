from __future__ import annotations

from pathlib import Path

from app import config
from app.voice.bank import VoiceProfile, resolve_voice

_F5_MODEL: object | None = None


class CloneTtsError(RuntimeError):
    """Voice-clone TTS failed."""


def _f5_vocab_file() -> str:
    base = Path(config.TTS_MODEL_PATH)
    local = base / "F5TTS_v1_Base" / "vocab.txt"
    if local.is_file():
        return str(local)
    from app.local_models import _ensure_f5_vocab

    try:
        return str(_ensure_f5_vocab(base))
    except RuntimeError as exc:
        raise CloneTtsError(
            "F5-TTS vocab missing — run: python main.py models pull --only tts"
        ) from exc


def _load_f5():
    global _F5_MODEL
    if _F5_MODEL is not None:
        return _F5_MODEL
    try:
        from f5_tts.api import F5TTS
    except ImportError as exc:  # pragma: no cover
        raise CloneTtsError(
            "f5-tts not installed. Run: pip install f5-tts"
        ) from exc

    from app.local_models import vocos_ready

    vocos_path = Path(config.VOCOS_MODEL_PATH)
    if not vocos_ready():
        raise CloneTtsError(
            f"vocos incomplete under {vocos_path} — run: python main.py models pull --only vocos"
        )

    ckpt = Path(config.TTS_MODEL_PATH)
    candidate = ckpt / "F5TTS_v1_Base" / "model_1250000.safetensors"
    if not candidate.is_file():
        raise CloneTtsError(
            "F5-TTS weights missing — run: python main.py models pull --only tts"
        )

    print("[tts] loading F5-TTS (local weights) …", flush=True)
    _F5_MODEL = F5TTS(
        device="cpu",
        ckpt_file=str(candidate),
        vocab_file=_f5_vocab_file(),
        vocoder_local_path=str(vocos_path),
    )
    return _F5_MODEL


def speak_with_voice(
    text: str,
    dest: Path,
    *,
    voice: VoiceProfile | None = None,
    voice_name: str | None = None,
) -> Path:
    """Clone narration using a recorded/imported voice sample (F5-TTS)."""
    profile = voice or resolve_voice(voice_name)
    if profile is None:
        raise CloneTtsError(
            "no voice sample — run: python main.py voice record --name me"
        )
    sample = Path(profile.sample_path)
    if not sample.is_file():
        raise CloneTtsError(f"sample wav missing: {sample}")
    if not profile.transcript.strip():
        raise CloneTtsError(
            f"voice '{profile.name}' has empty transcript; "
            "re-record or: voice import ... --transcript '...'"
        )

    text = text.strip()
    if not text:
        raise CloneTtsError("text to speak is empty")

    dest.parent.mkdir(parents=True, exist_ok=True)
    model = _load_f5()
    try:
        result = model.infer(
            ref_file=str(sample),
            ref_text=profile.transcript,
            gen_text=text,
            file_wave=str(dest),
            nfe_step=int(config.TTS_NFE_STEP),
        )
    except TypeError:
        result = model.infer(
            ref_audio=str(sample),
            ref_text=profile.transcript,
            gen_text=text,
            file_wave=str(dest),
            nfe_step=int(config.TTS_NFE_STEP),
        )

    if dest.exists() and dest.stat().st_size > 0:
        return dest

    import numpy as np
    import soundfile as sf

    if isinstance(result, tuple) and len(result) >= 2:
        wav, sr = result[0], result[1]
        sf.write(str(dest), np.asarray(wav), int(sr))
        return dest
    raise CloneTtsError("F5-TTS produced no audio file")
