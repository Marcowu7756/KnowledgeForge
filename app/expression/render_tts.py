from __future__ import annotations

from pathlib import Path

from app import config


class TtsError(RuntimeError):
    """Local TTS could not run."""


def render_system_tts(text: str, dest: Path, *, voice_hint: str = "zh") -> Path:
    """Fallback: Windows SAPI / platform voices via pyttsx3."""
    try:
        import pyttsx3
    except ImportError as exc:  # pragma: no cover
        raise TtsError("pyttsx3 not installed. Run: pip install pyttsx3") from exc

    dest.parent.mkdir(parents=True, exist_ok=True)
    engine = pyttsx3.init()
    engine.setProperty("rate", 165)

    if voice_hint.startswith("zh"):
        for voice in engine.getProperty("voices"):
            name = (voice.name or "") + (getattr(voice, "id", "") or "")
            if any(k in name.lower() for k in ("chinese", "zh", "huihui", "kangkang")):
                engine.setProperty("voice", voice.id)
                break

    engine.save_to_file(text, str(dest))
    engine.runAndWait()
    if not dest.exists() or dest.stat().st_size == 0:
        raise TtsError("TTS produced empty audio file")
    return dest


def render_narration_wav(
    text: str,
    dest: Path,
    *,
    voice_hint: str = "zh",
    voice_name: str | None = None,
    engine: str | None = None,
) -> Path:
    """Synthesize narration.

    Prefer voice-clone (your recorded sample) when available; else system TTS.
    """
    chosen = (engine or config.TTS_ENGINE or "clone").strip().lower()
    if chosen == "clone":
        try:
            from app.voice.clone_tts import CloneTtsError, speak_with_voice
            from app.voice.bank import resolve_voice

            if resolve_voice(voice_name) is not None:
                return speak_with_voice(text, dest, voice_name=voice_name)
        except CloneTtsError as exc:
            # Fall through to system voice with a clear warning path.
            if chosen == "clone" and voice_name:
                raise TtsError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            # Missing f5-tts / model still allows system fallback when no --voice forced.
            if voice_name:
                raise TtsError(str(exc)) from exc

    return render_system_tts(text, dest, voice_hint=voice_hint)
