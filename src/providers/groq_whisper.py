"""Groq Whisper ASR provider wrapper.

Uses OpenAI-compatible API at https://api.groq.com/openai/v1.
Docs: https://console.groq.com/docs/speech-to-text
"""

import time
from pathlib import Path
from typing import Optional

from openai import OpenAI

from src.config import GROQ_API_KEY

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    return _client


def transcribe(
    audio_path: str,
    language_code: Optional[str] = None,
    model: str = "whisper-large-v3",
) -> dict:
    """Transcribe audio using Whisper on Groq.

    Args:
        audio_path: Path to audio file (WAV, MP3, M4A supported).
        language_code: ISO-639-1 language code (e.g. "hi", "kn", "en").
        model: Model name. Options: "whisper-large-v3-turbo", "whisper-large-v3",
            "distil-whisper-large-v3-en" (English-only).

    Returns:
        dict with keys: provider, model, transcript, language_code, latency_seconds, raw_response
    """
    client = _get_client()

    with open(audio_path, "rb") as f:
        kwargs = {
            "model": model,
            "file": f,
            "response_format": "json",
            "temperature": 0,
        }
        if language_code:
            kwargs["language"] = language_code

        start = time.perf_counter()
        result = client.audio.transcriptions.create(**kwargs)
        latency = time.perf_counter() - start

    return {
        "provider": "groq",
        "model": model,
        "transcript": result.text,
        "language_code": language_code,
        "latency_seconds": round(latency, 3),
        "raw_response": result.model_dump() if hasattr(result, "model_dump") else str(result),
    }
