"""Sarvam AI Saarika/Saaras ASR provider wrapper."""

import mimetypes
import time
from pathlib import Path
from typing import Optional

import requests

from src.config import SARVAM_API_KEY

API_URL = "https://api.sarvam.ai/speech-to-text"


def transcribe(
    audio_path: str,
    language_code: Optional[str] = None,
    model: str = "saaras:v3",
    mode: str = "transcribe",
) -> dict:
    """Transcribe audio using Sarvam's speech-to-text API.

    Args:
        audio_path: Path to audio file (.wav or .m4a).
        language_code: BCP-47 language code (e.g. "hi-IN", "kn-IN", "en-IN").
            If None, Sarvam auto-detects.
        model: Model to use. Options: "saaras:v3" (recommended), "saarika:v2.5" (legacy).
        mode: Output mode for saaras:v3. Options: "transcribe", "translate",
            "verbatim", "translit", "codemix". Ignored for saarika models.

    Returns:
        dict with keys: transcript, language_code, latency_seconds, raw_response
    """
    headers = {"api-subscription-key": SARVAM_API_KEY}

    with open(audio_path, "rb") as f:
        mime_type = mimetypes.guess_type(audio_path)[0] or "audio/wav"
        # Sarvam API rejects audio/mp4a-latm; use audio/mp4 for m4a files
        if mime_type == "audio/mp4a-latm":
            mime_type = "audio/mp4"
        files = {"file": (Path(audio_path).name, f, mime_type)}
        data = {"model": model}
        if language_code:
            data["language_code"] = language_code
        if model.startswith("saaras"):
            data["mode"] = mode

        start = time.perf_counter()
        response = requests.post(API_URL, headers=headers, files=files, data=data, timeout=60)
        latency = time.perf_counter() - start

    response.raise_for_status()
    result = response.json()

    return {
        "provider": "sarvam",
        "model": model,
        "transcript": result.get("transcript", ""),
        "language_code": result.get("language_code"),
        "latency_seconds": round(latency, 3),
        "raw_response": result,
    }
