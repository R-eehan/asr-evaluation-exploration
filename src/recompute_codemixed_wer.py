"""Re-compute WER for code-mixed files with script normalization.

Addresses the script mismatch bias: ElevenLabs outputs English loanwords
in Latin script while ground truth uses native script (Devanagari/Kannada).
This script computes both original and script-normalized WER for comparison.

Also computes entity accuracy for banking-specific terms.
"""

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.metrics.normalize import normalize_text
from src.metrics.script_normalize import normalize_script, is_latin_word
from src.metrics.wer import compute_wer


CODE_MIXED_FILES = [
    "credit-card-application-1-hinglish.m4a",
    "gpay-fraud-1-hinglish.m4a",
    "transaction-check-1-hinglish.m4a",
    "transaction-check-2-hinglish.m4a",
    "debit-card-verification-1-Kannada.m4a",
    "loan-enquiry-1-Kannada.m4a",
    "suspicious-transaction-1-Kannada.m4a",
]

# Banking entities to check for entity accuracy
BANKING_ENTITIES = {
    "credit-card-application-1-hinglish.m4a": {
        "entities": ["credit card", "application", "apply", "online", "branch"],
        "language": "hi-en",
    },
    "gpay-fraud-1-hinglish.m4a": {
        "entities": ["fraud", "gpay", "account", "transfer"],
        "language": "hi-en",
    },
    "transaction-check-1-hinglish.m4a": {
        "entities": ["bank", "card", "unusual", "transaction", "18500", "online payment"],
        "language": "hi-en",
    },
    "transaction-check-2-hinglish.m4a": {
        "entities": ["transaction", "card", "block", "dispute", "process"],
        "language": "hi-en",
    },
    "debit-card-verification-1-Kannada.m4a": {
        "entities": ["bank", "debit card", "verification", "full name", "date of birth", "confirm"],
        "language": "kn-en",
    },
    "loan-enquiry-1-Kannada.m4a": {
        "entities": ["personal loan", "enquiry", "call", "purpose", "explain"],
        "language": "kn-en",
    },
    "suspicious-transaction-1-Kannada.m4a": {
        "entities": ["bank", "fraud", "monitoring team", "debit card", "unusual", "online", "transaction", "19800", "payment", "mumbai"],
        "language": "kn-en",
    },
}

# Native script versions of entity terms for matching
ENTITY_NATIVE_FORMS = {
    "hi-en": {
        "credit card": ["क्रेडिट कार्ड", "credit card"],
        "application": ["एप्लिकेशन", "एप्लीकेशन", "application"],
        "apply": ["अप्लाई", "apply"],
        "online": ["ऑनलाइन", "online"],
        "branch": ["ब्रांच", "branch"],
        "fraud": ["फ्रॉड", "fraud"],
        "gpay": ["जीपे", "जी पे", "gpay", "g pay"],
        "account": ["अकाउंट", "account"],
        "transfer": ["ट्रांसफर", "ट्रांसफ़र", "transfer"],
        "bank": ["बैंक", "bank"],
        "card": ["कार्ड", "card"],
        "unusual": ["अनयूज़ुअल", "अनयूजुअल", "unusual"],
        "transaction": ["ट्रांज़ैक्शन", "ट्रांजैक्शन", "transaction"],
        "18500": ["अठारह हज़ार पाँच सौ", "अठारह हजार पांच सौ", "18500", "18,500"],
        "online payment": ["ऑनलाइन पेमेंट", "online payment"],
        "block": ["ब्लॉक", "block"],
        "dispute": ["डिस्प्यूट", "dispute"],
        "process": ["प्रोसेस", "process"],
    },
    "kn-en": {
        "bank": ["ಬ್ಯಾಂಕ್", "bank"],
        "debit card": ["ಡೆಬಿಟ್ ಕಾರ್ಡ್", "debit card"],
        "verification": ["ವೆರಿಫಿಕೇಶನ್", "verification"],
        "full name": ["ಫುಲ್ ನೇಮ್", "full name"],
        "date of birth": ["ಡೇಟ್ ಆಫ್ ಬರ್ತ್", "date of birth"],
        "confirm": ["ಕನ್ಫರ್ಮ್", "confirm"],
        "personal loan": ["ಪರ್ಸನಲ್ ಲೋನ್", "personal loan"],
        "enquiry": ["ಇನ್ಕ್ವೈರಿ", "ಎನ್ಕ್ವೈರಿ", "enquiry", "inquiry"],
        "call": ["ಕಾಲ್", "call"],
        "purpose": ["ಪರ್ಪಸ್", "purpose"],
        "explain": ["ಎಕ್ಸ್\u200cಪ್ಲೈನ್", "ಎಕ್ಸ್ಪ್ಲೈನ್", "explain"],
        "fraud": ["ಫ್ರಾಡ್", "fraud"],
        "monitoring team": ["ಮಾನಿಟರಿಂಗ್ ಟೀಮ್", "monitoring team"],
        "unusual": ["ಅನ್\u200cಯೂಜುಅಲ್", "ಅನ್ಯೂಜುಅಲ್", "unusual"],
        "online": ["ಆನ್\u200cಲೈನ್", "ಆನ್ಲೈನ್", "online"],
        "transaction": ["ಟ್ರಾನ್ಸಾಕ್ಷನ್", "transaction"],
        "19800": ["ನೈಂಟೀನ್ ಥೌಸಂಡ್ ಎಯ್ಟ್ ಹಂಡ್ರೆಡ್", "nineteen thousand eight hundred", "19800", "19,800"],
        "payment": ["ಪೇಮೆಂಟ್", "payment"],
        "mumbai": ["ಮುಂಬೈ", "mumbai"],
    },
}


def check_entity(transcript: str, entity_forms: list[str]) -> bool:
    """Check if any form of an entity appears in the transcript."""
    transcript_lower = normalize_text(transcript)
    for form in entity_forms:
        form_lower = normalize_text(form)
        if form_lower in transcript_lower:
            return True
    return False


def main():
    results_path = Path(__file__).parent.parent / "data" / "results" / "eval_results_latest_models_merged.csv"

    with open(results_path) as f:
        rows = list(csv.DictReader(f))

    # Filter to code-mixed files
    cm_rows = [r for r in rows if r["filename"] in CODE_MIXED_FILES]

    print("=" * 100)
    print("SCRIPT-NORMALIZED WER RE-COMPUTATION")
    print("=" * 100)
    print()

    # Compute original and script-normalized WER
    results = []
    for fn in CODE_MIXED_FILES:
        lang = BANKING_ENTITIES[fn]["language"]
        file_rows = [r for r in cm_rows if r["filename"] == fn]
        print(f"--- {fn} (lang={lang}) ---")

        for row in sorted(file_rows, key=lambda r: r["provider"]):
            provider = row["provider"]
            ref = row["reference"]
            hyp = row["hypothesis"]
            orig_wer = float(row["wer"])

            # Script-normalize: replace Latin words with native equivalents
            hyp_normalized = normalize_script(hyp, lang)

            # Count how many words were normalized
            orig_words = hyp.split()
            norm_words = hyp_normalized.split()
            changed = sum(1 for a, b in zip(orig_words, norm_words) if a != b)

            # Compute new WER
            new_wer_result = compute_wer(ref, hyp_normalized)
            new_wer = new_wer_result["wer"]

            delta = new_wer - orig_wer
            results.append({
                "filename": fn,
                "language": lang,
                "provider": provider,
                "model": row["model"],
                "original_wer": orig_wer,
                "script_normalized_wer": new_wer,
                "delta": delta,
                "words_normalized": changed,
                "hypothesis_original": hyp,
                "hypothesis_normalized": hyp_normalized,
            })

            marker = ""
            if abs(delta) > 0.001:
                marker = f" ({'improved' if delta < 0 else 'worsened'} by {abs(delta)*100:.1f}pp)"
            print(f"  [{provider:>10}] Original: {orig_wer*100:5.1f}% → Normalized: {new_wer*100:5.1f}%{marker}  ({changed} words changed)")

        print()

    # Summary table
    print("=" * 100)
    print("SUMMARY: Script-Normalized WER (Code-Mixed Files Only)")
    print("=" * 100)
    print()
    print(f"{'Provider':<12} {'Original Mean WER':>18} {'Normalized Mean WER':>20} {'Delta':>8}")
    print("-" * 62)

    for provider in ["sarvam", "elevenlabs", "whisper"]:
        prov_results = [r for r in results if r["provider"] == provider]
        orig_mean = sum(r["original_wer"] for r in prov_results) / len(prov_results)
        norm_mean = sum(r["script_normalized_wer"] for r in prov_results) / len(prov_results)
        delta = norm_mean - orig_mean
        print(f"{provider:<12} {orig_mean*100:17.2f}% {norm_mean*100:19.2f}% {delta*100:+7.2f}pp")

    print()

    # Entity accuracy
    print("=" * 100)
    print("ENTITY ACCURACY (Banking Terms)")
    print("=" * 100)
    print()

    entity_results = []
    for fn in CODE_MIXED_FILES:
        lang = BANKING_ENTITIES[fn]["language"]
        entities = BANKING_ENTITIES[fn]["entities"]
        file_rows = [r for r in cm_rows if r["filename"] == fn]

        for entity in entities:
            native_forms = ENTITY_NATIVE_FORMS[lang].get(entity, [entity])

            for row in sorted(file_rows, key=lambda r: r["provider"]):
                found = check_entity(row["hypothesis"], native_forms)
                entity_results.append({
                    "filename": fn,
                    "entity": entity,
                    "provider": row["provider"],
                    "found": found,
                })

    # Print entity accuracy by provider
    for provider in ["sarvam", "elevenlabs", "whisper"]:
        prov_entities = [r for r in entity_results if r["provider"] == provider]
        total = len(prov_entities)
        found = sum(1 for r in prov_entities if r["found"])
        print(f"{provider:<12}: {found}/{total} entities correct ({found/total*100:.1f}%)")

    print()
    print("--- Per-file entity breakdown ---")
    for fn in CODE_MIXED_FILES:
        print(f"\n{fn}:")
        entities = BANKING_ENTITIES[fn]["entities"]
        for entity in entities:
            row_str = f"  {entity:<20}"
            for provider in ["sarvam", "elevenlabs", "whisper"]:
                match = [r for r in entity_results
                         if r["filename"] == fn and r["entity"] == entity and r["provider"] == provider]
                if match:
                    status = "Y" if match[0]["found"] else "N"
                    row_str += f"  {provider}={status}"
            print(row_str)

    # Save results
    output_path = Path(__file__).parent.parent / "data" / "results" / "script_normalized_wer.json"
    with open(output_path, "w") as f:
        json.dump({
            "description": "WER re-computation with script normalization for code-mixed files",
            "methodology": "Latin English loanwords in hypotheses replaced with native script equivalents before WER computation",
            "results": results,
            "entity_accuracy": entity_results,
        }, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
