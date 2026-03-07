"""Character Error Rate computation with Indic text normalization."""

import jiwer

from src.metrics.normalize import normalize_text


def compute_cer(reference: str, hypothesis: str) -> dict:
    """Compute CER between reference and hypothesis transcriptions.

    Especially important for Hindi/Kannada where single character errors
    can change word meaning entirely.

    Returns:
        dict with cer, substitutions, deletions, insertions, ref_chars, hyp_chars
    """
    ref_norm = normalize_text(reference)
    hyp_norm = normalize_text(hypothesis)

    if not ref_norm.strip():
        return {
            "cer": 0.0 if not hyp_norm.strip() else 1.0,
            "substitutions": 0,
            "deletions": 0,
            "insertions": len(hyp_norm.replace(" ", "")) if hyp_norm.strip() else 0,
            "ref_chars": 0,
            "hyp_chars": len(hyp_norm.replace(" ", "")) if hyp_norm.strip() else 0,
            "ref_normalized": ref_norm,
            "hyp_normalized": hyp_norm,
        }

    output = jiwer.process_characters(ref_norm, hyp_norm)

    return {
        "cer": round(output.cer, 4),
        "substitutions": output.substitutions,
        "deletions": output.deletions,
        "insertions": output.insertions,
        "ref_chars": len(ref_norm.replace(" ", "")),
        "hyp_chars": len(hyp_norm.replace(" ", "")),
        "ref_normalized": ref_norm,
        "hyp_normalized": hyp_norm,
    }
