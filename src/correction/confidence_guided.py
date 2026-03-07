"""ElevenLabs confidence-guided correction using per-word logprob scores.

Re-runs audio through ElevenLabs with timestamps_granularity='word' to get
per-word logprob confidence, flags low-confidence words, and sends them to
an LLM for targeted correction.

Falls back to full-transcript LLM correction when too few words are flagged
(ElevenLabs logprobs are poorly calibrated for Indian languages).
"""

import time
from pathlib import Path
from typing import Optional

from elevenlabs.client import ElevenLabs

from src.config import ELEVENLABS_API_KEY
from src.correction.llm_correction import correct_flagged_words, correct_full_transcript

DEFAULT_LOGPROB_THRESHOLD = -0.5
MIN_FLAGGED_FOR_TARGETED = 2  # fall back to full-transcript if fewer flagged

_client = None


def _get_client() -> ElevenLabs:
    global _client
    if _client is None:
        _client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    return _client


def transcribe_with_word_confidence(
    audio_path: str,
    language_code: Optional[str] = None,
    model: str = "scribe_v2",
    seed: Optional[int] = None,
) -> dict:
    """Transcribe audio with word-level timestamps and logprob scores.

    Args:
        seed: If set, makes transcription deterministic for reproducibility.

    Returns:
        dict with transcript, words (list of word dicts with logprob),
        language_code, latency_seconds.
    """
    client = _get_client()

    kwargs = {
        "model_id": model,
        "language_code": language_code,
        "timestamps_granularity": "word",
    }
    if seed is not None:
        kwargs["seed"] = seed

    with open(audio_path, "rb") as f:
        start = time.perf_counter()
        result = client.speech_to_text.convert(file=f, **kwargs)
        latency = time.perf_counter() - start

    words = []
    if hasattr(result, "words") and result.words:
        for w in result.words:
            word_dict = {
                "text": w.text if hasattr(w, "text") else str(w),
                "type": getattr(w, "type", "word"),
                "logprob": getattr(w, "logprob", None),
                "start": getattr(w, "start", None),
                "end": getattr(w, "end", None),
            }
            words.append(word_dict)

    return {
        "provider": "elevenlabs",
        "model": model,
        "transcript": result.text if hasattr(result, "text") else str(result),
        "words": words,
        "language_code": getattr(result, "language_code", None),
        "latency_seconds": round(latency, 3),
        "seed": seed,
    }


def flag_low_confidence_words(
    words: list[dict],
    threshold: float = DEFAULT_LOGPROB_THRESHOLD,
) -> list[int]:
    """Return indices of words with logprob below threshold.

    Only flags actual words (type='word'), not spacing/punctuation.
    """
    flagged = []
    for i, w in enumerate(words):
        if w.get("type") != "word":
            continue
        logprob = w.get("logprob")
        if logprob is not None and logprob < threshold:
            flagged.append(i)
    return flagged


def confidence_guided_correct(
    audio_path: str,
    language_code: Optional[str] = None,
    language_hint: str = "",
    threshold: float = DEFAULT_LOGPROB_THRESHOLD,
    seed: Optional[int] = None,
    model: str = "scribe_v2",
) -> dict:
    """Full confidence-guided correction pipeline for one audio file.

    1. Re-transcribes with word-level timestamps
    2. Flags low-confidence words
    3. If enough words flagged: targeted LLM correction on flagged words
    4. If too few flagged (overconfident model): falls back to full-transcript LLM correction

    Returns:
        dict with original transcript, corrected transcript, word details,
        flagged indices, and correction metadata.
    """
    # Step 1: Re-transcribe with word confidence
    stt_result = transcribe_with_word_confidence(
        audio_path, language_code=language_code, seed=seed, model=model
    )

    words = stt_result["words"]
    transcript = stt_result["transcript"]

    # Step 2: Flag low-confidence words
    flagged = flag_low_confidence_words(words, threshold=threshold)

    word_details = []
    for i, w in enumerate(words):
        if w.get("type") == "word":
            word_details.append({
                "text": w["text"],
                "logprob": w.get("logprob"),
                "flagged": i in set(flagged),
            })

    # Step 3: Correction — targeted if enough flagged, otherwise full-transcript fallback
    if len(flagged) >= MIN_FLAGGED_FOR_TARGETED:
        correction = correct_flagged_words(
            transcript, flagged, words, language_hint=language_hint
        )
        method_used = "targeted_flagged"
    else:
        # Fallback: full-transcript correction (same approach as Sarvam)
        correction = correct_full_transcript(
            transcript, language_hint=language_hint
        )
        correction["flagged_count"] = len(flagged)
        method_used = "full_transcript_fallback"

    return {
        "transcript_original": transcript,
        "transcript_corrected": correction["corrected"],
        "words": word_details,
        "flagged_count": len(flagged),
        "total_words": len([w for w in words if w.get("type") == "word"]),
        "threshold": threshold,
        "method_used": method_used,
        "stt_latency": stt_result["latency_seconds"],
        "seed": seed,
        "correction": correction,
    }
