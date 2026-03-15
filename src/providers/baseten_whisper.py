"""Baseten Whisper ASR provider wrapper.

Uses the non-streaming Whisper Large v3 Turbo deployed via Baseten Model Library.
REST API — send base64-encoded audio, get text back. Same pattern as all other providers.

Docs: https://www.baseten.co/library/whisper-large-turbo/
"""

import base64
import time
from pathlib import Path
from typing import Optional

import requests

from src.config import BASETEN_API_KEY

# Set after deploying non-streaming Whisper Large v3 Turbo on Baseten.
# Find the model ID in the Baseten dashboard after deployment.
BASETEN_MODEL_ID = "qvvxrpjq"


def _get_endpoint() -> str:
    if not BASETEN_MODEL_ID:
        raise RuntimeError(
            "BASETEN_MODEL_ID is not set. Deploy non-streaming Whisper Large v3 Turbo "
            "on Baseten, then set the model ID in this file."
        )
    return f"https://model-{BASETEN_MODEL_ID}.api.baseten.co/environments/production/predict"


def transcribe(
    audio_path: str,
    language_code: Optional[str] = None,
    model: str = "whisper-large-v3",
) -> dict:
    """Transcribe audio using Whisper Large v3 Turbo deployed on Baseten.

    Args:
        audio_path: Path to audio file (WAV, M4A, MP3 supported).
        language_code: ISO-639-1 language code (e.g. "hi", "kn", "en").
        model: Model name (for metadata — Baseten serves the deployed model).

    Returns:
        dict with keys: provider, model, transcript, language_code, latency_seconds, raw_response
    """
    endpoint = _get_endpoint()

    with open(audio_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "whisper_input": {
            "audio": {
                "audio_b64": audio_b64,
            },
            "whisper_params": {
                "audio_language": language_code or "en",
            },
        }
    }

    start = time.perf_counter()
    response = requests.post(
        endpoint,
        headers={
            "Authorization": f"Api-Key {BASETEN_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    latency = time.perf_counter() - start

    response.raise_for_status()
    data = response.json()

    # Response has segments with text, timing, and log_prob
    segments = data.get("segments", [])
    transcript = " ".join(seg.get("text", "") for seg in segments).strip()

    return {
        "provider": "baseten",
        "model": model,
        "transcript": transcript,
        "language_code": language_code,
        "latency_seconds": round(latency, 3),
        "raw_response": data,
    }
