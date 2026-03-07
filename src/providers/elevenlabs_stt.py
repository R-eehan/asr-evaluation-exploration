"""ElevenLabs Scribe ASR provider wrapper."""

import time
from pathlib import Path
from typing import Optional

from elevenlabs.client import ElevenLabs

from src.config import ELEVENLABS_API_KEY

_client = None


def _get_client() -> ElevenLabs:
    global _client
    if _client is None:
        _client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    return _client


def transcribe(
    audio_path: str,
    language_code: Optional[str] = None,
    model: str = "scribe_v2",
) -> dict:
    """Transcribe audio using ElevenLabs Scribe.

    Args:
        audio_path: Path to audio file.
        language_code: ISO-639-1 language code (e.g. "hi", "kn", "en").
            If None, Scribe auto-detects.
        model: Model ID. Default "scribe_v1".

    Returns:
        dict with keys: transcript, language_code, latency_seconds, raw_response
    """
    client = _get_client()

    with open(audio_path, "rb") as f:
        start = time.perf_counter()
        result = client.speech_to_text.convert(
            file=f,
            model_id=model,
            language_code=language_code,
        )
        latency = time.perf_counter() - start

    return {
        "provider": "elevenlabs",
        "model": model,
        "transcript": result.text if hasattr(result, "text") else str(result),
        "language_code": getattr(result, "language_code", getattr(result, "language", None)),
        "latency_seconds": round(latency, 3),
        "raw_response": result.dict() if hasattr(result, "dict") else str(result),
    }
