"""Main evaluation runner — processes audio files through all ASR providers."""

import json
import csv
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import AUDIO_DIR, GROUND_TRUTH_DIR, RESULTS_DIR
from src.providers import sarvam, elevenlabs_stt, whisper
from src.providers import together_ai, groq_whisper, fireworks_whisper, baseten_whisper
from src.metrics.wer import compute_wer
from src.metrics.cer import compute_cer
from src.metrics.latency import compute_latency_stats
from src.metrics.cost import compute_cost, get_audio_duration_seconds

PROVIDERS = {
    "sarvam": sarvam,
    "elevenlabs": elevenlabs_stt,
    "whisper": whisper,
    "together_ai": together_ai,
    "groq": groq_whisper,
    "fireworks": fireworks_whisper,
    "baseten": baseten_whisper,
}

# Map language codes from ground truth to provider-specific formats
SARVAM_LANG_MAP = {
    "hi": "hi-IN",
    "ka": "kn-IN",
    "kn": "kn-IN",
    "en-IN": "en-IN",
    "hi-en": "hi-IN",
    "kn-en": "kn-IN",
}

WHISPER_LANG_MAP = {
    "hi": "hi",
    "ka": "kn",
    "kn": "kn",
    "en-IN": "en",
    "hi-en": "hi",
    "kn-en": "kn",
}

ELEVENLABS_LANG_MAP = {
    "hi": "hi",
    "ka": "kn",
    "kn": "kn",
    "en-IN": "en",
    "hi-en": "hi",
    "kn-en": "kn",
}

# Unified lookup: provider name -> language map
# All Whisper-based inference platforms use the same language codes as OpenAI Whisper
LANG_MAPS = {
    "sarvam": SARVAM_LANG_MAP,
    "whisper": WHISPER_LANG_MAP,
    "elevenlabs": ELEVENLABS_LANG_MAP,
    "together_ai": WHISPER_LANG_MAP,
    "groq": WHISPER_LANG_MAP,
    "fireworks": WHISPER_LANG_MAP,
    "baseten": WHISPER_LANG_MAP,
}


def load_ground_truth() -> list:
    """Load ground truth from both dataset and personal transcription files."""
    entries = []

    # Public dataset ground truth
    dataset_gt = GROUND_TRUTH_DIR / "dataset_ground_truth.json"
    if dataset_gt.exists():
        with open(dataset_gt) as f:
            for item in json.load(f):
                item["audio_path"] = str(AUDIO_DIR / item["source"] / item["filename"])
                entries.append(item)

    # Personal recordings ground truth
    personal_gt = GROUND_TRUTH_DIR / "personal_template.json"
    if personal_gt.exists():
        with open(personal_gt) as f:
            data = json.load(f)
            clips = data.get("clips", data) if isinstance(data, dict) else data
            for item in clips:
                item["source"] = "personal"
                item["audio_path"] = str(AUDIO_DIR / "personal" / item["filename"])
                entries.append(item)

    return entries


def transcribe_single(provider_name: str, audio_path: str, language: str) -> dict:
    """Run a single transcription, returning result or error info."""
    provider = PROVIDERS[provider_name]

    # Map language code for each provider
    lang_map = LANG_MAPS.get(provider_name, WHISPER_LANG_MAP)
    lang = lang_map.get(language, language)

    try:
        result = provider.transcribe(audio_path, language_code=lang)
        return {"status": "ok", **result}
    except Exception as e:
        return {
            "status": "error",
            "provider": provider_name,
            "transcript": "",
            "latency_seconds": 0,
            "error": f"{type(e).__name__}: {e}",
        }


def run_evaluation(
    entries: Optional[list] = None,
    providers: Optional[list] = None,
    limit: Optional[int] = None,
) -> list:
    """Run full evaluation across all entries and providers.

    Args:
        entries: Ground truth entries. If None, loads from files.
        providers: List of provider names. If None, uses all.
        limit: Max number of audio files to process (for testing).

    Returns:
        List of result dicts, one per (audio_file, provider) pair.
    """
    if entries is None:
        entries = load_ground_truth()
    if providers is None:
        providers = list(PROVIDERS.keys())
    if limit:
        entries = entries[:limit]

    results = []
    total = len(entries) * len(providers)
    count = 0

    for entry in entries:
        audio_path = entry["audio_path"]
        filename = entry["filename"]
        reference = entry["text"]
        language = entry.get("language", "")
        scenario = entry.get("scenario", "")
        source = entry.get("source", "")

        if not Path(audio_path).exists():
            print(f"  SKIP {filename} — file not found at {audio_path}")
            continue

        # Compute audio duration once per file for cost calculation
        try:
            audio_duration_sec = get_audio_duration_seconds(audio_path)
        except Exception:
            audio_duration_sec = None

        for provider_name in providers:
            count += 1
            print(f"  [{count}/{total}] {provider_name} <- {filename} ...", end=" ", flush=True)

            result = transcribe_single(provider_name, audio_path, language)

            if result["status"] == "ok":
                wer_result = compute_wer(reference, result["transcript"])
                cer_result = compute_cer(reference, result["transcript"])
                print(f"WER={wer_result['wer']:.2%} latency={result['latency_seconds']}s")
            else:
                wer_result = {"wer": None, "substitutions": 0, "deletions": 0, "insertions": 0}
                cer_result = {"cer": None}
                print(f"ERROR: {result.get('error', 'unknown')}")

            # Compute cost for this request
            model_name = result.get("model", "")
            cost_usd = None
            if audio_duration_sec is not None and result["status"] == "ok":
                cost_usd = compute_cost(provider_name, model_name, audio_duration_sec)

            results.append({
                "filename": filename,
                "source": source,
                "language": language,
                "scenario": scenario,
                "provider": result.get("provider", provider_name),
                "model": model_name,
                "reference": reference,
                "hypothesis": result.get("transcript", ""),
                "wer": wer_result["wer"],
                "cer": cer_result["cer"],
                "substitutions": wer_result.get("substitutions", 0),
                "deletions": wer_result.get("deletions", 0),
                "insertions": wer_result.get("insertions", 0),
                "latency_seconds": result.get("latency_seconds", 0),
                "audio_duration_sec": audio_duration_sec,
                "cost_usd": cost_usd,
                "status": result["status"],
                "error": result.get("error", ""),
            })

    return results


def save_results(results: list, tag: str = "") -> tuple:
    """Save results to CSV and JSON in the results directory.

    Returns:
        Tuple of (csv_path, json_path).
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_{tag}" if tag else ""
    csv_path = RESULTS_DIR / f"eval_results{suffix}_{timestamp}.csv"
    json_path = RESULTS_DIR / f"eval_results{suffix}_{timestamp}.json"

    # CSV
    if results:
        fieldnames = list(results[0].keys())
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

    # JSON
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return str(csv_path), str(json_path)


def print_summary(results: list):
    """Print a summary table of results by provider."""
    from collections import defaultdict

    by_provider = defaultdict(list)
    for r in results:
        if r["status"] == "ok" and r["wer"] is not None:
            by_provider[r["provider"]].append(r)

    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)

    for provider, items in sorted(by_provider.items()):
        wers = [r["wer"] for r in items]
        cers = [r["cer"] for r in items if r["cer"] is not None]
        latencies = [r["latency_seconds"] for r in items]
        lat_stats = compute_latency_stats(latencies)

        print(f"\n--- {provider.upper()} ({len(items)} files) ---")
        print(f"  WER:     mean={sum(wers)/len(wers):.2%}  min={min(wers):.2%}  max={max(wers):.2%}")
        if cers:
            print(f"  CER:     mean={sum(cers)/len(cers):.2%}  min={min(cers):.2%}  max={max(cers):.2%}")
        print(f"  Latency: p50={lat_stats['p50']}s  p95={lat_stats['p95']}s  mean={lat_stats['mean']}s")

        # Errors
        errors = [r for r in results if r["provider"] == provider and r["status"] == "error"]
        if errors:
            print(f"  Errors:  {len(errors)} failed")

    print("\n" + "=" * 70)


def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Run ASR evaluation")
    parser.add_argument("--limit", type=int, default=None, help="Max audio files to process")
    parser.add_argument("--providers", nargs="+", default=None, help="Providers to test")
    parser.add_argument("--tag", default="", help="Tag for output filenames")
    args = parser.parse_args()

    print(f"Loading ground truth...")
    entries = load_ground_truth()
    print(f"Found {len(entries)} audio files with ground truth.\n")

    providers = args.providers or list(PROVIDERS.keys())
    print(f"Providers: {', '.join(providers)}")
    print(f"Limit: {args.limit or 'all'}\n")

    print("Starting evaluation...")
    results = run_evaluation(entries, providers=providers, limit=args.limit)

    csv_path, json_path = save_results(results, tag=args.tag)
    print(f"\nResults saved to:\n  CSV:  {csv_path}\n  JSON: {json_path}")

    print_summary(results)


if __name__ == "__main__":
    # Add project root to path so imports work
    sys.path.insert(0, str(Path(__file__).parent.parent))
    main()
