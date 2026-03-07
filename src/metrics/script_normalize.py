"""Script-agnostic normalization for fair cross-provider WER comparison.

Problem: ElevenLabs outputs English loanwords in Latin script ("credit card")
while ground truth and other providers use native script ("क्रेडिट कार्ड").
This inflates ElevenLabs' WER on code-mixed content.

Solution: Build a Latin → native script mapping from our ground truth data,
replace Latin words in hypotheses with native equivalents before WER computation.
"""

import re

# Hindi-English (hi-en): Latin → Devanagari mappings
# Derived from ground truth in personal_template.json
_LATIN_TO_DEVANAGARI = {
    "sir": "सर",
    "hello": "हेलो",
    "recently": "रिसेंटली",
    "credit": "क्रेडिट",
    "card": "कार्ड",
    "application": "एप्लिकेशन",
    "submit": "सबमिट",
    "apply": "अप्लाई",
    "online": "ऑनलाइन",
    "branch": "ब्रांच",
    "through": "थ्रू",
    "fraud": "फ्रॉड",
    "number": "नंबर",
    "gpay": "जीपे",
    "account": "अकाउंट",
    "transfer": "ट्रांसफर",
    "bank": "बैंक",
    "unusual": "अनयूज़ुअल",
    "transaction": "ट्रांज़ैक्शन",
    "payment": "पेमेंट",
    "block": "ब्लॉक",
    "dispute": "डिस्प्यूट",
    "process": "प्रोसेस",
    "start": "स्टार्ट",
}

# Kannada-English (kn-en): Latin → Kannada mappings
_LATIN_TO_KANNADA = {
    "sir": "ಸರ್",
    "hello": "ಹಲೋ",
    "bank": "ಬ್ಯಾಂಕ್",
    "debit": "ಡೆಬಿಟ್",
    "card": "ಕಾರ್ಡ್",
    "verification": "ವೆರಿಫಿಕೇಶನ್",
    "full": "ಫುಲ್",
    "name": "ನೇಮ್",
    "date": "ಡೇಟ್",
    "of": "ಆಫ್",
    "birth": "ಬರ್ತ್",
    "confirm": "ಕನ್ಫರ್ಮ್",
    "personal": "ಪರ್ಸನಲ್",
    "loan": "ಲೋನ್",
    "enquiry": "ಇನ್ಕ್ವೈರಿ",
    "inquiry": "ಇನ್ಕ್ವೈರಿ",
    "call": "ಕಾಲ್",
    "purpose": "ಪರ್ಪಸ್",
    "explain": "ಎಕ್ಸ್\u200cಪ್ಲೈನ್",
    "fraud": "ಫ್ರಾಡ್",
    "monitoring": "ಮಾನಿಟರಿಂಗ್",
    "team": "ಟೀಮ್",
    "unusual": "ಅನ್\u200cಯೂಜುಅಲ್",
    "online": "ಆನ್\u200cಲೈನ್",
    "transaction": "ಟ್ರಾನ್ಸಾಕ್ಷನ್",
    "try": "ಟ್ರೈ",
    "nineteen": "ನೈಂಟೀನ್",
    "thousand": "ಥೌಸಂಡ್",
    "eight": "ಎಯ್ಟ್",
    "hundred": "ಹಂಡ್ರೆಡ್",
    "payment": "ಪೇಮೆಂಟ್",
    "mumbai": "ಮುಂಬೈ",
}


def is_latin_word(word: str) -> bool:
    """Check if a word is primarily Latin script."""
    latin_chars = sum(1 for c in word if "a" <= c.lower() <= "z")
    return latin_chars > len(word) * 0.5 if word else False


def normalize_script(text: str, language: str) -> str:
    """Replace Latin-script English words with native script equivalents.

    Args:
        text: Transcript text (may contain mixed Latin + native script)
        language: Language code ('hi-en' for Hinglish, 'kn-en' for Kannada-English)

    Returns:
        Text with Latin loanwords replaced by native script equivalents
    """
    if language == "hi-en":
        mapping = _LATIN_TO_DEVANAGARI
    elif language == "kn-en":
        mapping = _LATIN_TO_KANNADA
    else:
        return text  # No normalization for monolingual content

    words = text.split()
    normalized = []
    for word in words:
        # Strip punctuation for lookup, preserve for output
        clean = re.sub(r"[.,!?;:\"'()\[\]{}]", "", word).lower()
        if is_latin_word(word) and clean in mapping:
            normalized.append(mapping[clean])
        else:
            normalized.append(word)

    return " ".join(normalized)
