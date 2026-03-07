"""Indic text normalization for accurate WER/CER computation.

Handles:
- Unicode NFC normalization
- Devanagari (Hindi) and Kannada script punctuation
- Latin punctuation stripping
- Casing normalization
- Common number word normalization
- Whitespace collapsing

Built as a jiwer-compatible transform pipeline.
"""

import re
import unicodedata


def normalize_text(text: str) -> str:
    """Apply full normalization pipeline to a text string."""
    text = unicode_normalize(text)
    text = normalize_devanagari_variants(text)
    text = strip_punctuation(text)
    text = normalize_numbers(text)
    text = text.lower()
    text = collapse_whitespace(text)
    return text.strip()


def unicode_normalize(text: str) -> str:
    """NFC normalization — canonical decomposition then composition."""
    return unicodedata.normalize("NFC", text)


def normalize_devanagari_variants(text: str) -> str:
    """Normalize common Devanagari character variants that differ across transcribers.

    - Nuqta variants: क़→क, ख़→ख, ग़→ग, ज़→ज, फ़→फ, ड़→ड, ढ़→ढ
    - Chandrabindu/anusvara: both treated the same for WER purposes
    """
    # Strip nuqta (U+093C) — normalizes क़→क, ज़→ज, फ़→फ, etc.
    text = text.replace("\u093C", "")
    # Chandrabindu (ँ U+0901) → Anusvara (ं U+0902) — common transcription variation
    text = text.replace("\u0901", "\u0902")
    return text


def strip_punctuation(text: str) -> str:
    """Remove punctuation from Latin, Devanagari, and Kannada scripts."""
    # Devanagari punctuation: danda, double danda, abbreviation sign
    text = re.sub(r"[\u0964\u0965\u0970]", " ", text)
    # Kannada punctuation
    text = re.sub(r"[\u0CE6-\u0CEF]", lambda m: m.group(), text)  # keep Kannada digits
    # General Unicode punctuation categories (P = punctuation, S = symbol)
    text = re.sub(r"[\u2000-\u206F\u2E00-\u2E7F]", " ", text)  # general punctuation block
    # Standard Latin punctuation and symbols
    text = re.sub(r"[.,!?;:\"'()\[\]{}\-_/\\@#$%^&*~`+=<>|₹]", " ", text)
    # Ellipsis and special quotes
    text = re.sub(r"[…""''«»]", " ", text)
    return text


# Common Hindi number words → digits (for normalizing transcription differences)
_HINDI_NUMBERS = {
    "शून्य": "0", "एक": "1", "दो": "2", "तीन": "3", "चार": "4",
    "पांच": "5", "पाँच": "5", "छह": "6", "छः": "6", "सात": "7",
    "आठ": "8", "नौ": "9", "दस": "10", "सौ": "100", "हज़ार": "1000",
    "हजार": "1000", "लाख": "100000", "करोड़": "10000000",
}

# Common English number words
_ENGLISH_NUMBERS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "hundred": "100", "thousand": "1000", "lakh": "100000",
    "lakhs": "100000", "crore": "10000000", "crores": "10000000",
}


def normalize_numbers(text: str) -> str:
    """Normalize number words to digits and strip commas from numbers."""
    # Remove commas in digit sequences (e.g. "18,500" → "18500")
    text = re.sub(r"(\d),(\d)", r"\1\2", text)
    # Rupee symbol → empty
    text = text.replace("₹", " ")
    return text


def collapse_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters into a single space."""
    return re.sub(r"\s+", " ", text)
