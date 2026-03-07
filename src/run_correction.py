"""Post-ASR correction runner — applies LLM-based correction to ASR output.

Supports all 3 providers:
- Sarvam & Whisper: Full-transcript LLM correction (no per-word confidence)
- ElevenLabs: Confidence-guided correction with full-transcript fallback,
  averaged across 3 seeded runs to account for transcription non-determinism

Usage:
    python -m src.run_correction
    python -m src.run_correction --limit 3  # quick test
    python -m src.run_correction --runs 5   # more averaging
    python -m src.run_correction --results-csv data/results/latest.csv --el-model scribe_v2
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from src.config import AUDIO_DIR, GROUND_TRUTH_DIR, RESULTS_DIR
from src.correction.llm_correction import correct_full_transcript
from src.correction.confidence_guided import confidence_guided_correct
from src.metrics.wer import compute_wer
from src.metrics.cer import compute_cer

# Language code mapping for ElevenLabs API
ELEVENLABS_LANG_MAP = {
    "hi": "hi",
    "ka": "kn",
    "kn": "kn",
    "en-IN": "en",
    "hi-en": "hi",
    "kn-en": "kn",
}

# Human-readable language hints for LLM prompts
LANGUAGE_HINTS = {
    "hi": "Hindi (Devanagari)",
    "ka": "Kannada",
    "kn": "Kannada",
    "en-IN": "Indian English",
    "hi-en": "Hindi-English code-mixed",
    "kn-en": "Kannada-English code-mixed",
}

DEFAULT_RESULTS_CSV = "data/results/eval_results_full_merged_20260306_235442.csv"
DEFAULT_SEEDS = [42, 123, 7]


def load_results(csv_path: str) -> list[dict]:
    """Load Day 3 evaluation results from CSV."""
    results = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["wer"] = float(row["wer"]) if row["wer"] else None
            row["cer"] = float(row["cer"]) if row["cer"] else None
            row["latency_seconds"] = float(row["latency_seconds"]) if row["latency_seconds"] else 0
            results.append(row)
    return results


def find_worst_files(results: list[dict], provider: str, threshold: float) -> list[dict]:
    """Find files exceeding WER threshold for a given provider, sorted worst-first."""
    worst = [
        r for r in results
        if r["provider"] == provider
        and r["wer"] is not None
        and r["wer"] > threshold
        and r["status"] == "ok"
    ]
    worst.sort(key=lambda r: r["wer"], reverse=True)
    return worst


def resolve_audio_path(filename: str, source: str) -> str:
    """Resolve filename + source to actual audio file path."""
    if source == "personal":
        return str(AUDIO_DIR / "personal" / filename)
    elif source == "indicvoices":
        return str(AUDIO_DIR / "indicvoices" / filename)
    elif source == "svarah":
        return str(AUDIO_DIR / "svarah" / filename)
    return str(AUDIO_DIR / filename)


def run_full_transcript_correction(file_row: dict, provider_name: str) -> dict:
    """Apply full-transcript LLM correction to any provider's ASR result."""
    language = file_row["language"]
    lang_hint = LANGUAGE_HINTS.get(language, language)

    print(f"    Correcting with full-transcript LLM ({lang_hint})...")
    correction = correct_full_transcript(
        file_row["hypothesis"],
        language_hint=lang_hint,
    )

    wer_before = compute_wer(file_row["reference"], file_row["hypothesis"])
    wer_after = compute_wer(file_row["reference"], correction["corrected"])
    cer_before = compute_cer(file_row["reference"], file_row["hypothesis"])
    cer_after = compute_cer(file_row["reference"], correction["corrected"])

    return {
        "filename": file_row["filename"],
        "language": language,
        "scenario": file_row["scenario"],
        "source": file_row["source"],
        "provider": provider_name,
        "method": "full_transcript_llm",
        "reference": file_row["reference"],
        "original_transcript": file_row["hypothesis"],
        "corrected_transcript": correction["corrected"],
        "wer_before": wer_before["wer"],
        "wer_after": wer_after["wer"],
        "wer_delta": round(wer_after["wer"] - wer_before["wer"], 4),
        "cer_before": cer_before["cer"],
        "cer_after": cer_after["cer"],
        "cer_delta": round(cer_after["cer"] - cer_before["cer"], 4),
        "llm_model": correction["model"],
        "llm_tokens": correction["usage"],
    }


def run_elevenlabs_correction_multi_seed(
    file_row: dict, seeds: list[int], threshold: float, el_model: str = "scribe_v2"
) -> dict:
    """Run confidence-guided correction across multiple seeds and average results.

    For each seed:
    1. Re-transcribe with that seed (deterministic per seed)
    2. Try confidence-guided correction; fall back to full-transcript if too few flagged
    3. Compute WER/CER for both re-transcription and corrected output

    Returns averaged metrics + per-run details.
    """
    language = file_row["language"]
    lang_code = ELEVENLABS_LANG_MAP.get(language)
    lang_hint = LANGUAGE_HINTS.get(language, language)
    audio_path = resolve_audio_path(file_row["filename"], file_row["source"])
    reference = file_row["reference"]

    wer_before = compute_wer(reference, file_row["hypothesis"])
    cer_before = compute_cer(reference, file_row["hypothesis"])

    per_run = []
    for seed in seeds:
        print(f"      Seed {seed}: re-transcribing ({el_model})...", end=" ", flush=True)
        result = confidence_guided_correct(
            audio_path,
            language_code=lang_code,
            language_hint=lang_hint,
            threshold=threshold,
            seed=seed,
            model=el_model,
        )

        # WER of the raw re-transcription (before LLM correction)
        wer_retranscribed = compute_wer(reference, result["transcript_original"])
        cer_retranscribed = compute_cer(reference, result["transcript_original"])

        # WER after LLM correction
        wer_corrected = compute_wer(reference, result["transcript_corrected"])
        cer_corrected = compute_cer(reference, result["transcript_corrected"])

        run_data = {
            "seed": seed,
            "method_used": result["method_used"],
            "flagged_count": result["flagged_count"],
            "total_words": result["total_words"],
            "retranscribed_text": result["transcript_original"],
            "corrected_text": result["transcript_corrected"],
            "wer_retranscribed": wer_retranscribed["wer"],
            "cer_retranscribed": cer_retranscribed["cer"],
            "wer_corrected": wer_corrected["wer"],
            "cer_corrected": cer_corrected["cer"],
            "word_details": result["words"],
        }
        per_run.append(run_data)

        print(
            f"flagged={result['flagged_count']}/{result['total_words']} "
            f"method={result['method_used']} "
            f"WER retrans={wer_retranscribed['wer']:.2%} "
            f"WER corrected={wer_corrected['wer']:.2%}"
        )

    # Average across runs
    n = len(per_run)
    avg_wer_retranscribed = sum(r["wer_retranscribed"] for r in per_run) / n
    avg_cer_retranscribed = sum(r["cer_retranscribed"] for r in per_run) / n
    avg_wer_corrected = sum(r["wer_corrected"] for r in per_run) / n
    avg_cer_corrected = sum(r["cer_corrected"] for r in per_run) / n
    avg_flagged = sum(r["flagged_count"] for r in per_run) / n

    return {
        "filename": file_row["filename"],
        "language": language,
        "scenario": file_row["scenario"],
        "source": file_row["source"],
        "provider": "elevenlabs",
        "method": per_run[0]["method_used"],  # typically same across runs
        "reference": reference,
        "original_transcript": file_row["hypothesis"],
        "wer_before": wer_before["wer"],
        "cer_before": cer_before["cer"],
        # Re-transcription effect (no LLM)
        "avg_wer_retranscribed": round(avg_wer_retranscribed, 4),
        "avg_cer_retranscribed": round(avg_cer_retranscribed, 4),
        "retranscription_delta": round(avg_wer_retranscribed - wer_before["wer"], 4),
        # After LLM correction
        "avg_wer_corrected": round(avg_wer_corrected, 4),
        "avg_cer_corrected": round(avg_cer_corrected, 4),
        "wer_after": round(avg_wer_corrected, 4),
        "wer_delta": round(avg_wer_corrected - wer_before["wer"], 4),
        "cer_after": round(avg_cer_corrected, 4),
        "cer_delta": round(avg_cer_corrected - cer_before["cer"], 4),
        # Correction effect (isolated from re-transcription)
        "correction_effect": round(avg_wer_corrected - avg_wer_retranscribed, 4),
        "avg_flagged": round(avg_flagged, 1),
        "total_words": per_run[0]["total_words"],
        "threshold": threshold,
        "num_runs": n,
        "seeds": seeds,
        "per_run": per_run,
        "llm_model": "gpt-5.4",
    }


def save_correction_results(results: list[dict], tag: str = "correction_v2") -> tuple:
    """Save correction results to CSV and JSON."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = RESULTS_DIR / f"{tag}_{timestamp}.csv"
    json_path = RESULTS_DIR / f"{tag}_{timestamp}.json"

    # CSV (flat fields only)
    csv_fields = [
        "filename", "language", "scenario", "source", "provider", "method",
        "wer_before", "wer_after", "wer_delta",
        "cer_before", "cer_after", "cer_delta",
        "avg_wer_retranscribed", "retranscription_delta", "correction_effect",
        "avg_flagged", "total_words", "threshold", "num_runs",
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    # JSON (full details including per-run transcripts)
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return str(csv_path), str(json_path)


def print_comparison_table(results: list[dict]):
    """Print before/after WER comparison table."""
    print("\n" + "=" * 110)
    print("POST-ASR CORRECTION RESULTS (v2 — GPT-5.4 + fallback + 3-seed avg)")
    print("=" * 110)

    by_provider = defaultdict(list)
    for r in results:
        by_provider[r["provider"]].append(r)

    for provider, items in sorted(by_provider.items()):
        method_label = items[0].get("method", "unknown")
        print(f"\n--- {provider.upper()} ---")

        if provider == "elevenlabs":
            print(
                f"{'File':<40} {'Lang':<6} {'WER Orig':>9} "
                f"{'WER Retr':>9} {'WER Corr':>9} {'Delta':>8} "
                f"{'Corr Eff':>9} {'Method':<22}"
            )
            print("-" * 110)
            for r in items:
                delta_str = f"{r['wer_delta']:+.2%}"
                corr_eff = r.get("correction_effect", 0)
                corr_str = f"{corr_eff:+.2%}" if corr_eff else "+0.00%"
                method = r.get("method", "")
                print(
                    f"{r['filename']:<40} {r['language']:<6} "
                    f"{r['wer_before']:>8.2%} "
                    f"{r.get('avg_wer_retranscribed', r['wer_before']):>8.2%} "
                    f"{r['wer_after']:>8.2%} "
                    f"{delta_str:>8} {corr_str:>9}  {method}"
                )
        else:
            print(
                f"{'File':<40} {'Lang':<6} {'WER Before':>10} "
                f"{'WER After':>10} {'Delta':>8} {'CER Delta':>9}"
            )
            print("-" * 110)
            for r in items:
                delta_str = f"{r['wer_delta']:+.2%}"
                cer_delta_str = f"{r['cer_delta']:+.2%}"
                print(
                    f"{r['filename']:<40} {r['language']:<6} "
                    f"{r['wer_before']:>9.2%} {r['wer_after']:>9.2%} "
                    f"{delta_str:>8} {cer_delta_str:>9}"
                )

        wer_deltas = [r["wer_delta"] for r in items]
        improved = sum(1 for d in wer_deltas if d < 0)
        worsened = sum(1 for d in wer_deltas if d > 0)
        unchanged = sum(1 for d in wer_deltas if d == 0)
        avg_delta = sum(wer_deltas) / len(wer_deltas) if wer_deltas else 0

        print(f"\n  Summary: {improved} improved, {worsened} worsened, {unchanged} unchanged")
        print(f"  Average WER delta: {avg_delta:+.2%}")

        if provider == "elevenlabs":
            corr_effects = [r.get("correction_effect", 0) for r in items]
            avg_corr = sum(corr_effects) / len(corr_effects) if corr_effects else 0
            print(f"  Average correction effect (isolated): {avg_corr:+.2%}")

    print("\n" + "=" * 110)


def main():
    parser = argparse.ArgumentParser(description="Post-ASR correction pipeline")
    parser.add_argument(
        "--results-csv", default=DEFAULT_RESULTS_CSV,
        help="Path to evaluation results CSV",
    )
    parser.add_argument("--wer-threshold", type=float, default=0.05,
                        help="Min WER to attempt correction (default 0.05 = 5%%)")
    parser.add_argument("--providers", nargs="+", default=["sarvam", "elevenlabs", "whisper"],
                        help="Providers to correct")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max files per provider (for testing)")
    parser.add_argument("--logprob-threshold", type=float, default=-0.5)
    parser.add_argument("--runs", type=int, default=3,
                        help="Number of seeded runs for ElevenLabs averaging (default 3)")
    parser.add_argument("--el-model", default="scribe_v2",
                        help="ElevenLabs model for re-transcription (scribe_v1 or scribe_v2)")
    parser.add_argument("--tag", default="correction_v3",
                        help="Tag for output filenames")
    parser.add_argument("--skip-languages", nargs="+", default=["en-IN"],
                        help="Languages to skip (default: en-IN)")
    args = parser.parse_args()

    seeds = DEFAULT_SEEDS[:args.runs]

    print(f"Post-ASR Correction Pipeline")
    print(f"  LLM: GPT-5.4 | ElevenLabs model: {args.el_model} | Runs: {args.runs} (seeds: {seeds})")
    print(f"  Logprob threshold: {args.logprob_threshold} | WER threshold: {args.wer_threshold:.0%}")
    print(f"  Skip languages: {args.skip_languages}")
    print(f"  Providers: {args.providers}\n")

    print("Loading results...")
    all_results = load_results(args.results_csv)
    print(f"  Loaded {len(all_results)} result rows.\n")

    correction_results = []

    for provider_name in args.providers:
        # Find files above WER threshold, skipping excluded languages
        worst = find_worst_files(all_results, provider_name, args.wer_threshold)
        worst = [r for r in worst if r["language"] not in args.skip_languages]

        if args.limit:
            worst = worst[:args.limit]

        if not worst:
            print(f"{provider_name.upper()}: No files above {args.wer_threshold:.0%} WER (after skipping {args.skip_languages})")
            continue

        print(f"\n{'='*60}")
        if provider_name == "elevenlabs":
            print(f"ELEVENLABS — Confidence-guided + fallback ({args.runs}-seed avg, {args.el_model})")
        else:
            print(f"{provider_name.upper()} — Full-transcript LLM correction (GPT-5.4)")
        print(f"{'='*60}")

        print(f"Files (WER > {args.wer_threshold:.0%}): {len(worst)}")
        for r in worst:
            print(f"  {r['filename']:<45} WER={r['wer']:.2%} ({r['language']})")

        for i, row in enumerate(worst, 1):
            print(f"\n  [{i}/{len(worst)}] {row['filename']} (WER={row['wer']:.2%})")
            try:
                if provider_name == "elevenlabs":
                    result = run_elevenlabs_correction_multi_seed(
                        row, seeds=seeds, threshold=args.logprob_threshold,
                        el_model=args.el_model,
                    )
                    delta = result["wer_delta"]
                    corr_eff = result.get("correction_effect", 0)
                    print(
                        f"    Avg WER: {result['wer_before']:.2%} -> {result['wer_after']:.2%} "
                        f"(delta: {delta:+.2%}, correction effect: {corr_eff:+.2%})"
                    )
                else:
                    result = run_full_transcript_correction(row, provider_name)
                    delta = result["wer_delta"]
                    print(f"    WER: {result['wer_before']:.2%} -> {result['wer_after']:.2%} ({delta:+.2%})")
                correction_results.append(result)
            except Exception as e:
                print(f"    ERROR: {e}")

    if correction_results:
        csv_path, json_path = save_correction_results(correction_results, tag=args.tag)
        print(f"\nResults saved to:\n  CSV:  {csv_path}\n  JSON: {json_path}")
        print_comparison_table(correction_results)
    else:
        print("\nNo correction results generated.")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))
    main()
