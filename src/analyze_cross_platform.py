"""Phase 4: Cross-platform analysis for inference platform evaluation.

Reads the cross-platform results CSV and produces:
1. Script-normalized WER for code-mixed files
2. Entity accuracy for banking terms
3. Error type breakdown (substitution/insertion/deletion) per provider per language
4. Provider agreement analysis across all 28 files

Usage:
    python -m src.analyze_cross_platform --results data/results/eval_results_cross_platform_v1_*.csv
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.metrics.normalize import normalize_text
from src.metrics.script_normalize import normalize_script
from src.metrics.wer import compute_wer
from src.metrics.cer import compute_cer

# Language categories
LANG_NAMES = {
    "hi": "Hindi",
    "ka": "Kannada",
    "en-IN": "English (Indian)",
    "hi-en": "Hinglish",
    "kn-en": "Kannada-English",
}

# Extended Hindi loanword mapping for pure Hindi files
# These words appear in Hindi audio transcriptions as Latin script
_HINDI_LOANWORDS = {
    "order": "ऑर्डर",
    "book": "बुक",
    "discount": "डिस्काउंट",
}

# Banking entities for entity accuracy (from recompute_codemixed_wer.py)
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
        "entities": ["bank", "fraud", "monitoring team", "debit card", "unusual", "online",
                     "transaction", "19800", "payment", "mumbai"],
        "language": "kn-en",
    },
}

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
        "transaction": ["ट्रांज़ैक्शन", "ट्रांजैक्शन", "ट्रांजाक्शन", "transaction"],
        "18500": ["अठारह हज़ार पाँच सौ", "अठारह हजार पांच सौ", "18500", "18,500"],
        "online payment": ["ऑनलाइन पेमेंट", "ओनलाइन पेमेंट", "online payment"],
        "block": ["ब्लॉक", "block"],
        "dispute": ["डिस्प्यूट", "dispute"],
        "process": ["प्रोसेस", "process"],
    },
    "kn-en": {
        "bank": ["ಬ್ಯಾಂಕ್", "ಬಾಂಕ್", "bank"],
        "debit card": ["ಡೆಬಿಟ್ ಕಾರ್ಡ್", "debit card"],
        "verification": ["ವೆರಿಫಿಕೇಶನ್", "ವೈರಿಫಿಕೆಶಿನ್", "verification"],
        "full name": ["ಫುಲ್ ನೇಮ್", "ಫುಲ್ನೇಮ್", "full name"],
        "date of birth": ["ಡೇಟ್ ಆಫ್ ಬರ್ತ್", "date of birth"],
        "confirm": ["ಕನ್ಫರ್ಮ್", "ಕಂಫರ್ಮ್", "confirm"],
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
    transcript_lower = normalize_text(transcript)
    for form in entity_forms:
        if normalize_text(form) in transcript_lower:
            return True
    return False


def analyze_script_normalization(rows: list, providers: list) -> dict:
    """Task 1: Script-normalized WER for code-mixed files."""
    print("=" * 90)
    print("1. SCRIPT-NORMALIZED WER (Code-Mixed Files)")
    print("=" * 90)
    print()

    cm_rows = [r for r in rows if r["filename"] in BANKING_ENTITIES]
    results = []

    for fn in BANKING_ENTITIES:
        lang = BANKING_ENTITIES[fn]["language"]
        file_rows = [r for r in cm_rows if r["filename"] == fn]
        print(f"--- {fn} ({lang}) ---")

        for row in sorted(file_rows, key=lambda r: providers.index(r["provider"]) if r["provider"] in providers else 99):
            if row["provider"] not in providers:
                continue

            ref = row["reference"]
            hyp = row["hypothesis"]
            orig_wer = float(row["wer"]) if row["wer"] else None

            if orig_wer is None:
                continue

            hyp_normalized = normalize_script(hyp, lang)
            new_wer_result = compute_wer(ref, hyp_normalized)
            new_wer = new_wer_result["wer"]
            delta = new_wer - orig_wer

            results.append({
                "filename": fn,
                "language": lang,
                "provider": row["provider"],
                "original_wer": orig_wer,
                "normalized_wer": new_wer,
                "delta": delta,
            })

            marker = ""
            if abs(delta) > 0.001:
                marker = f" ({'improved' if delta < 0 else 'worsened'} by {abs(delta)*100:.1f}pp)"
            print(f"  {row['provider']:>12}: {orig_wer*100:5.1f}% → {new_wer*100:5.1f}%{marker}")

        print()

    # Summary by provider
    print("SUMMARY: Mean WER Before/After Script Normalization")
    print(f"{'Provider':<14} {'Original':>10} {'Normalized':>12} {'Delta':>8}")
    print("-" * 48)
    for p in providers:
        p_results = [r for r in results if r["provider"] == p]
        if not p_results:
            continue
        orig = sum(r["original_wer"] for r in p_results) / len(p_results)
        norm = sum(r["normalized_wer"] for r in p_results) / len(p_results)
        delta = norm - orig
        print(f"{p:<14} {orig*100:9.1f}% {norm*100:11.1f}% {delta*100:+7.1f}pp")
    print()

    return results


def analyze_entity_accuracy(rows: list, providers: list) -> dict:
    """Task 2: Entity accuracy for banking terms."""
    print("=" * 90)
    print("2. ENTITY ACCURACY (Banking Terms)")
    print("=" * 90)
    print()

    cm_rows = [r for r in rows if r["filename"] in BANKING_ENTITIES]
    entity_results = []

    for fn in BANKING_ENTITIES:
        lang = BANKING_ENTITIES[fn]["language"]
        entities = BANKING_ENTITIES[fn]["entities"]
        file_rows = [r for r in cm_rows if r["filename"] == fn]

        for entity in entities:
            native_forms = ENTITY_NATIVE_FORMS[lang].get(entity, [entity])
            for row in file_rows:
                if row["provider"] not in providers:
                    continue
                found = check_entity(row["hypothesis"], native_forms)
                entity_results.append({
                    "filename": fn,
                    "entity": entity,
                    "provider": row["provider"],
                    "found": found,
                })

    # Summary by provider
    print(f"{'Provider':<14} {'Found':>6} {'Total':>6} {'Accuracy':>10}")
    print("-" * 40)
    for p in providers:
        p_ents = [r for r in entity_results if r["provider"] == p]
        if not p_ents:
            continue
        found = sum(1 for r in p_ents if r["found"])
        total = len(p_ents)
        print(f"{p:<14} {found:>6} {total:>6} {found/total*100:>9.1f}%")
    print()

    # Per-file breakdown
    print("Per-file entity breakdown:")
    for fn in BANKING_ENTITIES:
        entities = BANKING_ENTITIES[fn]["entities"]
        print(f"\n  {fn}:")
        for entity in entities:
            row_str = f"    {entity:<20}"
            for p in providers:
                match = [r for r in entity_results
                         if r["filename"] == fn and r["entity"] == entity and r["provider"] == p]
                if match:
                    row_str += f"  {p[:8]}={'Y' if match[0]['found'] else 'N'}"
            print(row_str)
    print()

    return entity_results


def analyze_error_types(rows: list, providers: list) -> dict:
    """Task 3: Error type breakdown per provider per language."""
    print("=" * 90)
    print("3. ERROR TYPE BREAKDOWN (Substitution / Insertion / Deletion)")
    print("=" * 90)
    print()

    results = defaultdict(lambda: defaultdict(lambda: {"sub": 0, "ins": 0, "del": 0, "total_ref": 0, "files": 0}))

    for row in rows:
        if row["provider"] not in providers or row["status"] != "ok":
            continue
        lang = row["language"]
        prov = row["provider"]
        sub = int(row["substitutions"])
        ins = int(row["insertions"])
        dele = int(row["deletions"])
        ref_words = len(row["reference"].split())

        results[lang][prov]["sub"] += sub
        results[lang][prov]["ins"] += ins
        results[lang][prov]["del"] += dele
        results[lang][prov]["total_ref"] += ref_words
        results[lang][prov]["files"] += 1

    for lang_code in ["hi", "ka", "en-IN", "hi-en", "kn-en"]:
        if lang_code not in results:
            continue
        lang_name = LANG_NAMES.get(lang_code, lang_code)
        print(f"--- {lang_name} ---")
        print(f"{'Provider':<14} {'Sub%':>7} {'Ins%':>7} {'Del%':>7} {'Sub':>5} {'Ins':>5} {'Del':>5} {'RefWords':>9}")
        print("-" * 70)

        for p in providers:
            if p not in results[lang_code]:
                continue
            d = results[lang_code][p]
            total_ref = d["total_ref"]
            sub_pct = d["sub"] / total_ref * 100 if total_ref else 0
            ins_pct = d["ins"] / total_ref * 100 if total_ref else 0
            del_pct = d["del"] / total_ref * 100 if total_ref else 0
            print(f"{p:<14} {sub_pct:>6.1f}% {ins_pct:>6.1f}% {del_pct:>6.1f}% {d['sub']:>5} {d['ins']:>5} {d['del']:>5} {total_ref:>9}")

        print()

    return dict(results)


def analyze_provider_agreement(rows: list, providers: list) -> dict:
    """Task 4: Cross-platform agreement analysis."""
    print("=" * 90)
    print("4. PROVIDER AGREEMENT ANALYSIS")
    print("=" * 90)
    print()

    # Group by filename
    by_file = defaultdict(dict)
    for row in rows:
        if row["provider"] in providers and row["status"] == "ok":
            by_file[row["filename"]][row["provider"]] = {
                "wer": float(row["wer"]) if row["wer"] else None,
                "hypothesis": row["hypothesis"],
            }

    agreement_results = []

    # For each file, compute WER spread and word-level agreement
    print(f"{'File':<48} {'WER Range':>12} {'Spread':>8} {'Agreement':>10}")
    print("-" * 82)

    for fn in sorted(by_file.keys()):
        prov_data = by_file[fn]
        if len(prov_data) < len(providers):
            continue

        wers = [prov_data[p]["wer"] for p in providers if p in prov_data and prov_data[p]["wer"] is not None]
        if not wers:
            continue

        min_wer = min(wers)
        max_wer = max(wers)
        spread = max_wer - min_wer

        # Word-level agreement: what fraction of words are identical across all providers?
        hypotheses = [prov_data[p]["hypothesis"] for p in providers if p in prov_data]
        word_lists = [h.split() for h in hypotheses]
        if word_lists:
            # Compare all providers against the first one for a simple agreement metric
            max_len = max(len(wl) for wl in word_lists)
            if max_len > 0:
                # Pairwise: count positions where all providers agree
                min_len = min(len(wl) for wl in word_lists)
                agree_count = 0
                for i in range(min_len):
                    words_at_i = set(wl[i] for wl in word_lists)
                    if len(words_at_i) == 1:
                        agree_count += 1
                agreement = agree_count / max_len
            else:
                agreement = 0
        else:
            agreement = 0

        agreement_results.append({
            "filename": fn,
            "min_wer": min_wer,
            "max_wer": max_wer,
            "spread": spread,
            "word_agreement": agreement,
        })

        # Color-code the spread
        spread_marker = "  " if spread < 0.05 else " *" if spread < 0.15 else " **" if spread < 0.3 else "***"
        print(f"{fn:<48} {min_wer*100:4.0f}-{max_wer*100:4.0f}% {spread*100:>6.1f}pp {agreement*100:>8.0f}%{spread_marker}")

    print()
    print("Legend: * = moderate spread (5-15pp), ** = high (15-30pp), *** = very high (>30pp)")
    print()

    # Summary: files with consensus vs divergence
    consensus = [r for r in agreement_results if r["spread"] < 0.05]
    moderate = [r for r in agreement_results if 0.05 <= r["spread"] < 0.15]
    high = [r for r in agreement_results if r["spread"] >= 0.15]
    print(f"Consensus (<5pp spread):  {len(consensus)}/{len(agreement_results)} files")
    print(f"Moderate (5-15pp spread): {len(moderate)}/{len(agreement_results)} files")
    print(f"High divergence (>15pp):  {len(high)}/{len(agreement_results)} files")

    if high:
        print(f"\nHigh-divergence files:")
        for r in sorted(high, key=lambda x: -x["spread"]):
            print(f"  {r['filename']}: {r['spread']*100:.0f}pp spread ({r['min_wer']*100:.0f}%-{r['max_wer']*100:.0f}%)")

    print()
    return agreement_results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Phase 4: Cross-platform analysis")
    parser.add_argument("--results", required=True, help="Path to cross-platform results CSV")
    args = parser.parse_args()

    with open(args.results) as f:
        rows = list(csv.DictReader(f))

    # Detect providers in the data
    providers = list(dict.fromkeys(r["provider"] for r in rows if r["status"] == "ok"))
    print(f"Providers found: {', '.join(providers)}")
    print(f"Total results: {len(rows)}")
    print()

    # Run all analyses
    norm_results = analyze_script_normalization(rows, providers)
    entity_results = analyze_entity_accuracy(rows, providers)
    error_results = analyze_error_types(rows, providers)
    agreement_results = analyze_provider_agreement(rows, providers)

    # Save all results to JSON
    output_path = Path(args.results).parent / "phase4_cross_platform_analysis.json"
    with open(output_path, "w") as f:
        json.dump({
            "description": "Phase 4 cross-platform analysis results",
            "source_csv": args.results,
            "providers": providers,
            "script_normalization": norm_results,
            "entity_accuracy": entity_results,
            "agreement": agreement_results,
        }, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nAll results saved to {output_path}")


if __name__ == "__main__":
    main()
