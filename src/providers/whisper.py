"""OpenAI Whisper ASR provider wrapper."""

import time
from pathlib import Path
from typing import Optional

from openai import OpenAI

from src.config import OPENAI_API_KEY

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def transcribe(
    audio_path: str,
    language_code: Optional[str] = None,
    model: str = "gpt-4o-transcribe",
) -> dict:
    """Transcribe audio using OpenAI Whisper.

    Args:
        audio_path: Path to audio file.
        language_code: ISO-639-1 language code (e.g. "hi", "kn", "en").
            If None, Whisper auto-detects.
        model: Model name. Default "whisper-1".

    Returns:
        dict with keys: transcript, language_code, latency_seconds, raw_response
    """
    client = _get_client()

    with open(audio_path, "rb") as f:
        fmt = "json" if model.startswith("gpt-") else "verbose_json"
        kwargs = {"model": model, "file": f, "response_format": fmt}
        if language_code:
            kwargs["language"] = language_code

        start = time.perf_counter()
        result = client.audio.transcriptions.create(**kwargs)
        latency = time.perf_counter() - start

    return {
        "provider": "whisper",
        "model": model,
        "transcript": result.text,
        "language_code": getattr(result, "language", None),
        "latency_seconds": round(latency, 3),
        "raw_response": result.model_dump() if hasattr(result, "model_dump") else str(result),
    }
