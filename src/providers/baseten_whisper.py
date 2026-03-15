"""Baseten Whisper ASR provider wrapper (stub).

Unlike the OpenAI-compatible providers, Baseten uses a direct HTTP endpoint
specific to the deployed model. The endpoint URL is set after deploying
Whisper Large v3 via the Baseten Model Library (Phase 2).

Docs: https://www.baseten.co/library/whisper-large-v3-turbo-streaming/
"""

import time
from typing import Optional

from src.config import BASETEN_API_KEY

# Set after deploying Whisper on Baseten (Phase 2)
# e.g. "https://model-<model_id>.api.baseten.co/production/predict"
BASETEN_WHISPER_ENDPOINT = None


def transcribe(
    audio_path: str,
    language_code: Optional[str] = None,
    model: str = "whisper-large-v3",
) -> dict:
    """Transcribe audio using Whisper Large v3 deployed on Baseten.

    Args:
        audio_path: Path to audio file.
        language_code: ISO-639-1 language code (e.g. "hi", "kn", "en").
        model: Model name (for metadata only — Baseten serves a single deployed model).

    Returns:
        dict with keys: provider, model, transcript, language_code, latency_seconds, raw_response
    """
    if not BASETEN_WHISPER_ENDPOINT:
        raise RuntimeError(
            "BASETEN_WHISPER_ENDPOINT is not set. Deploy Whisper on Baseten first (Phase 2), "
            "then set the endpoint URL in this file."
        )

    import requests

    with open(audio_path, "rb") as f:
        start = time.perf_counter()
        response = requests.post(
            BASETEN_WHISPER_ENDPOINT,
            headers={"Authorization": f"Api-Key {BASETEN_API_KEY}"},
            files={"audio": f},
            data={"language": language_code} if language_code else {},
            timeout=120,
        )
        latency = time.perf_counter() - start

    response.raise_for_status()
    data = response.json()

    # Response format depends on the Truss config — adjust after deployment
    transcript = data.get("text", data.get("transcription", str(data)))

    return {
        "provider": "baseten",
        "model": model,
        "transcript": transcript,
        "language_code": language_code,
        "latency_seconds": round(latency, 3),
        "raw_response": data,
    }
