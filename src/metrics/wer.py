"""Word Error Rate computation with Indic text normalization."""

import jiwer

from src.metrics.normalize import normalize_text


def compute_wer(reference: str, hypothesis: str) -> dict:
    """Compute WER between reference and hypothesis transcriptions.

    Both texts are normalized before comparison (Unicode NFC, punctuation
    stripping, lowercasing, whitespace collapsing).

    Returns:
        dict with wer, substitutions, deletions, insertions, ref_words, hyp_words
    """
    ref_norm = normalize_text(reference)
    hyp_norm = normalize_text(hypothesis)

    if not ref_norm.strip():
        return {
            "wer": 0.0 if not hyp_norm.strip() else 1.0,
            "substitutions": 0,
            "deletions": 0,
            "insertions": len(hyp_norm.split()) if hyp_norm.strip() else 0,
            "ref_words": 0,
            "hyp_words": len(hyp_norm.split()) if hyp_norm.strip() else 0,
            "ref_normalized": ref_norm,
            "hyp_normalized": hyp_norm,
        }

    output = jiwer.process_words(ref_norm, hyp_norm)

    return {
        "wer": round(output.wer, 4),
        "substitutions": output.substitutions,
        "deletions": output.deletions,
        "insertions": output.insertions,
        "ref_words": len(ref_norm.split()),
        "hyp_words": len(hyp_norm.split()),
        "ref_normalized": ref_norm,
        "hyp_normalized": hyp_norm,
    }
