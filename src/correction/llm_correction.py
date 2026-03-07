"""LLM-based post-ASR correction with banking domain prompts.

Two modes:
1. Full-transcript correction (for Sarvam — no per-word confidence available)
2. Targeted correction of flagged words (for ElevenLabs — uses logprob scores)
"""

from openai import OpenAI

from src.config import OPENAI_API_KEY

_client = None

MODEL = "gpt-5.4"

BANKING_SYSTEM_PROMPT = (
    "You are correcting ASR transcription errors from Indian banking calls.\n\n"
    "RULES:\n"
    "1. ONLY fix clear transcription errors (garbled words, missing sounds, wrong homophones).\n"
    "2. NEVER standardize dialect to written form. Preserve exactly how it was spoken — "
    "colloquial, informal, regional variants are CORRECT if that is what was said.\n"
    "3. NEVER merge or split words across boundaries. If the ASR output has two separate words, "
    "keep them as two words.\n"
    "4. Preserve the original script (Devanagari, Kannada, Latin). Do not transliterate.\n"
    "5. If unsure whether something is an error, LEAVE IT UNCHANGED. A false correction is worse "
    "than a missed one.\n"
    "6. For code-mixed text (Hindi-English, Kannada-English): English banking terms are strong "
    "signal — fix obvious English word errors confidently. Be more conservative with the "
    "Indic-language portions.\n"
    "7. Numbers, amounts, and account references: preserve the format used by the speaker.\n\n"
    "Banking vocabulary: खाता/account, ब्याज/interest, किस्त/EMI, राशि/amount, जमा/deposit, "
    "निकासी/withdrawal, शेष/balance, ಖಾತೆ, ಬಡ್ಡಿ, ಕಂತು, ಮೊತ್ತ.\n\n"
    "Return ONLY the corrected text. If nothing needs correction, return the input exactly as-is."
)

TARGETED_SYSTEM_PROMPT = (
    "You are correcting low-confidence words from an ASR transcript of an Indian banking call. "
    "The full transcript is given with uncertain words marked as [?word?].\n\n"
    "RULES:\n"
    "1. For each marked word: if you are confident it is wrong, replace it. "
    "If you are unsure, KEEP THE ORIGINAL WORD.\n"
    "2. NEVER change unmarked words. They are high-confidence and should be trusted.\n"
    "3. NEVER standardize dialect to written form. Preserve spoken/colloquial variants.\n"
    "4. NEVER merge or split words across boundaries.\n"
    "5. Preserve the original script (Devanagari, Kannada, Latin).\n\n"
    "Banking vocabulary: खाता, ब्याज, किस्त, राशि, जमा, निकासी, शेष, "
    "ಖಾತೆ, ಬಡ್ಡಿ, ಕಂತು, ಮೊತ್ತ.\n\n"
    "Return ONLY the corrected full transcript with markers removed. "
    "If no marked words need correction, return the transcript with markers simply removed."
)


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def correct_full_transcript(transcript: str, language_hint: str = "") -> dict:
    """Send full ASR transcript to LLM for correction.

    Used for Sarvam outputs (no per-word confidence available).

    Args:
        transcript: Raw ASR transcript text.
        language_hint: e.g. "Hindi", "Kannada", "Hindi-English code-mixed".

    Returns:
        dict with corrected_text and metadata.
    """
    client = _get_client()

    user_msg = f"Correct this ASR transcript"
    if language_hint:
        user_msg += f" (language: {language_hint})"
    user_msg += f":\n\n{transcript}"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": BANKING_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
        max_completion_tokens=1024,
    )

    corrected = response.choices[0].message.content.strip()

    return {
        "method": "full_transcript",
        "original": transcript,
        "corrected": corrected,
        "model": MODEL,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
        },
    }


def correct_flagged_words(transcript: str, flagged_indices: list[int],
                          words: list[dict], language_hint: str = "") -> dict:
    """Send transcript with flagged low-confidence words to LLM for targeted correction.

    Used for ElevenLabs outputs (has per-word logprob scores).

    Args:
        transcript: Full ASR transcript text.
        flagged_indices: Indices into the words list that are low-confidence.
        words: List of word dicts from ElevenLabs (with text, logprob, type).
        language_hint: e.g. "Hindi", "Kannada".

    Returns:
        dict with corrected_text and metadata.
    """
    if not flagged_indices:
        return {
            "method": "targeted_flagged",
            "original": transcript,
            "corrected": transcript,
            "flagged_count": 0,
            "model": MODEL,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        }

    # Build transcript with markers around low-confidence words
    flagged_set = set(flagged_indices)
    marked_parts = []
    for i, w in enumerate(words):
        if w.get("type") == "spacing":
            marked_parts.append(w["text"])
        elif i in flagged_set:
            marked_parts.append(f"[?{w['text']}?]")
        else:
            marked_parts.append(w["text"])
    marked_transcript = "".join(marked_parts)

    client = _get_client()

    user_msg = f"Correct the marked words in this ASR transcript"
    if language_hint:
        user_msg += f" (language: {language_hint})"
    user_msg += f":\n\n{marked_transcript}"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": TARGETED_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
        max_completion_tokens=1024,
    )

    corrected = response.choices[0].message.content.strip()

    return {
        "method": "targeted_flagged",
        "original": transcript,
        "corrected": corrected,
        "marked_transcript": marked_transcript,
        "flagged_count": len(flagged_indices),
        "model": MODEL,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
        },
    }
