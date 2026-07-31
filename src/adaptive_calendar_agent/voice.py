from __future__ import annotations

from pathlib import Path

from adaptive_calendar_agent.config import VoiceConfig


def transcribe(path: Path, config: VoiceConfig) -> str:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "Voice support is not installed. Run: pip install -e '.[voice]'"
        ) from exc

    model = WhisperModel(
        config.model,
        device=config.device,
        compute_type=config.compute_type,
    )
    segments, _ = model.transcribe(str(path), vad_filter=True)
    text = " ".join(segment.text.strip() for segment in segments).strip()
    if not text:
        raise ValueError("No speech was detected in the audio file.")
    return text
