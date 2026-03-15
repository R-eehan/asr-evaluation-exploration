"""Cost calculator — computes per-request cost based on provider pricing and audio duration."""

from pathlib import Path

# Pricing: provider -> model -> cost per audio minute (USD)
# Sources: provider pricing pages, verified March 2026
#   Together AI: https://www.together.ai/pricing
#   Groq: https://groq.com/pricing
#   Fireworks AI: https://fireworks.ai/pricing
#   OpenAI: https://costgoat.com/pricing/openai-transcription
PRICING_PER_AUDIO_MINUTE = {
    "together_ai": {
        "openai/whisper-large-v3": 0.0015,       # $0.09/hr
    },
    "groq": {
        "whisper-large-v3": 0.00185,              # $0.111/hr
        "whisper-large-v3-turbo": 0.000667,       # $0.04/hr
        "distil-whisper-large-v3-en": 0.000333,   # $0.02/hr (being deprecated)
    },
    "fireworks": {
        "whisper-v3": 0.0015,                     # $0.09/hr
        "whisper-v3-turbo": 0.0009,               # $0.054/hr
    },
    "whisper": {
        "gpt-4o-transcribe": 0.006,               # $0.36/hr
        "gpt-4o-mini-transcribe": 0.003,           # $0.18/hr
        "whisper-1": 0.006,                        # $0.36/hr
    },
    "baseten": {
        # GPU-minute pricing, not per-audio-minute. H100 MIG at ~$0.0625/GPU-min.
        # Actual cost depends on utilization and cold start. Cannot compute per-request.
        "whisper-large-v3": None,
    },
    "sarvam": {},     # free tier / unclear per-minute pricing
    "elevenlabs": {},  # free tier / unclear per-minute pricing
}


def get_audio_duration_seconds(audio_path: str) -> float:
    """Get audio duration in seconds using pydub (already in requirements)."""
    from pydub import AudioSegment

    ext = Path(audio_path).suffix.lower()
    if ext == ".wav":
        audio = AudioSegment.from_wav(audio_path)
    elif ext in (".m4a", ".mp4"):
        audio = AudioSegment.from_file(audio_path, format="m4a")
    elif ext == ".mp3":
        audio = AudioSegment.from_mp3(audio_path)
    elif ext == ".flac":
        audio = AudioSegment.from_file(audio_path, format="flac")
    else:
        audio = AudioSegment.from_file(audio_path)

    return len(audio) / 1000.0


def compute_cost(provider: str, model: str, audio_duration_seconds: float) -> float | None:
    """Compute cost in USD for a single transcription request.

    Returns None if pricing is unavailable for the provider/model.
    """
    provider_pricing = PRICING_PER_AUDIO_MINUTE.get(provider, {})
    per_minute = provider_pricing.get(model)

    if per_minute is None:
        return None

    audio_minutes = audio_duration_seconds / 60.0
    return round(per_minute * audio_minutes, 6)
