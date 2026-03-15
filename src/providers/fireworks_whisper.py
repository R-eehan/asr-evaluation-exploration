"""Fireworks AI Whisper ASR provider wrapper.

Uses OpenAI-compatible API at https://audio-prod.api.fireworks.ai/v1.
Docs: https://docs.fireworks.ai/guides/querying-asr-models
"""

import time
from pathlib import Path
from typing import Optional

from openai import OpenAI

from src.config import FIREWORKS_API_KEY

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=FIREWORKS_API_KEY, base_url="https://audio-prod.api.fireworks.ai/v1")
    return _client


def transcribe(
    audio_path: str,
    language_code: Optional[str] = None,
    model: str = "whisper-v3",
) -> dict:
    """Transcribe audio using Whisper v3 on Fireworks AI.

    Args:
        audio_path: Path to audio file (WAV, MP3, M4A supported).
        language_code: ISO-639-1 language code (e.g. "hi", "kn", "en").
        model: Model name. Options: "whisper-v3", "whisper-v3-turbo".

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
        "provider": "fireworks",
        "model": model,
        "transcript": result.text,
        "language_code": language_code,
        "latency_seconds": round(latency, 3),
        "raw_response": result.model_dump() if hasattr(result, "model_dump") else str(result),
    }
