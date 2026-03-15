"""Main evaluation runner — processes audio files through all ASR providers."""

import json
import csv
import sys
import time
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


def load_existing_results(resume_file: str) -> tuple[set, list]:
    """Load completed results from a JSONL file.

    Returns:
        Tuple of (completed_keys, existing_results).
        Keys are (provider_name, filename, model_override, run) tuples.
        existing_results is a list of all result dicts from the JSONL.
    """
    completed = set()
    existing = []
    path = Path(resume_file)
    if path.exists():
        with open(path) as f:
            for line in f:
                try:
                    r = json.loads(line)
                    # Key on model_override (what was requested), not model (what provider returned)
                    key = (r.get("_provider_name", r["provider"]), r["filename"],
                           r.get("_model_override", ""), r.get("run", 1))
                    completed.add(key)
                    existing.append(r)
                except (json.JSONDecodeError, KeyError):
                    continue
    return completed, existing


def transcribe_single(
    provider_name: str,
    audio_path: str,
    language: str,
    model_override: Optional[str] = None,
) -> dict:
    """Run a single transcription, returning result or error info."""
    provider = PROVIDERS[provider_name]

    # Map language code for each provider
    lang_map = LANG_MAPS.get(provider_name, WHISPER_LANG_MAP)
    lang = lang_map.get(language, language)

    try:
        kwargs = {"audio_path": audio_path, "language_code": lang}
        if model_override:
            kwargs["model"] = model_override
        result = provider.transcribe(**kwargs)
        return {"status": "ok", **result}
    except Exception as e:
        return {
            "status": "error",
            "provider": provider_name,
            "model": model_override or "",
            "transcript": "",
            "latency_seconds": 0,
            "error": f"{type(e).__name__}: {e}",
        }


def run_evaluation(
    entries: Optional[list] = None,
    providers: Optional[list] = None,
    limit: Optional[int] = None,
    files: Optional[list] = None,
    repeats: int = 1,
    model_override: Optional[str] = None,
    delay: float = 0,
    resume_file: Optional[str] = None,
) -> list:
    """Run full evaluation across all entries and providers.

    Args:
        entries: Ground truth entries. If None, loads from files.
        providers: List of provider names. If None, uses all.
        limit: Max number of audio files to process (for testing).
        files: Specific filenames to include (e.g. ["indicvoices_hi_01.wav"]).
        repeats: Number of times to run each (file, provider) pair.
        model_override: Override the default model for all providers.
        delay: Seconds to wait between API calls (rate limit protection).
        resume_file: Path to JSONL file for incremental writes + resumability.
            If set, completed pairs are skipped and new results are appended.

    Returns:
        List of result dicts, one per (audio_file, provider, run) triple.
    """
    if entries is None:
        entries = load_ground_truth()
    if providers is None:
        providers = list(PROVIDERS.keys())
    if files:
        entries = [e for e in entries if e["filename"] in files]
    if limit:
        entries = entries[:limit]

    # Pre-filter entries with missing audio files for accurate progress counter
    valid_entries = []
    for entry in entries:
        if Path(entry["audio_path"]).exists():
            valid_entries.append(entry)
        else:
            print(f"  SKIP {entry['filename']} — file not found at {entry['audio_path']}")
    entries = valid_entries

    # Load already-completed pairs if resuming
    completed = set()
    existing_results = []
    if resume_file:
        completed, existing_results = load_existing_results(resume_file)
        if completed:
            print(f"  Resuming: {len(completed)} results already completed, will skip.\n")

    results = []
    total = len(entries) * len(providers) * repeats
    count = 0
    skipped = 0

    for entry in entries:
        audio_path = entry["audio_path"]
        filename = entry["filename"]
        reference = entry["text"]
        language = entry.get("language", "")
        scenario = entry.get("scenario", "")
        source = entry.get("source", "")

        # Compute audio duration once per file for cost calculation
        try:
            audio_duration_sec = get_audio_duration_seconds(audio_path)
        except Exception:
            audio_duration_sec = None

        for provider_name in providers:
            for run in range(1, repeats + 1):
                count += 1

                # Check if already completed (resumability)
                # Key on provider_name and model_override (what was requested),
                # not the provider's returned model name
                resume_key = (provider_name, filename, model_override or "", run)
                if resume_key in completed:
                    skipped += 1
                    run_label = f" (run {run}/{repeats})" if repeats > 1 else ""
                    print(f"  [{count}/{total}] {provider_name} <- {filename}{run_label} ... CACHED")
                    continue

                run_label = f" (run {run}/{repeats})" if repeats > 1 else ""
                print(f"  [{count}/{total}] {provider_name} <- {filename}{run_label} ...", end=" ", flush=True)

                result = transcribe_single(provider_name, audio_path, language, model_override)

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

                row = {
                    "filename": filename,
                    "source": source,
                    "language": language,
                    "scenario": scenario,
                    "provider": result.get("provider", provider_name),
                    "model": model_name,
                    "run": run,
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
                    # Tracking fields for resumability (keyed on what was requested)
                    "_provider_name": provider_name,
                    "_model_override": model_override or "",
                }

                results.append(row)

                # Write incrementally to JSONL for resumability
                if resume_file:
                    with open(resume_file, "a") as f:
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")

                # Rate limit protection
                if delay > 0:
                    time.sleep(delay)

    if skipped:
        print(f"\n  Skipped {skipped} already-completed pairs.")

    # Merge existing + new results so save_results and print_summary get the full picture
    all_results = existing_results + results
    return all_results


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

        model_name = items[0].get("model", "")
        model_label = f" [{model_name}]" if model_name else ""

        print(f"\n--- {provider.upper()}{model_label} ({len(items)} files) ---")
        print(f"  WER:     mean={sum(wers)/len(wers):.2%}  min={min(wers):.2%}  max={max(wers):.2%}")
        if cers:
            print(f"  CER:     mean={sum(cers)/len(cers):.2%}  min={min(cers):.2%}  max={max(cers):.2%}")
        print(f"  Latency: p50={lat_stats['p50']}s  p95={lat_stats['p95']}s  mean={lat_stats['mean']}s")

        # Cost summary
        costs = [r["cost_usd"] for r in items if r.get("cost_usd") is not None]
        if costs:
            print(f"  Cost:    total=${sum(costs):.4f}  per_file=${sum(costs)/len(costs):.6f}")

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
    parser.add_argument("--files", nargs="+", default=None, help="Specific filenames to process (e.g. indicvoices_hi_01.wav)")
    parser.add_argument("--providers", nargs="+", default=None, help="Providers to test")
    parser.add_argument("--tag", default="", help="Tag for output filenames")
    parser.add_argument("--repeats", type=int, default=1, help="Repeat each (file, provider) pair N times")
    parser.add_argument("--model", default=None, help="Override default model for all providers")
    parser.add_argument("--delay", type=float, default=0, help="Seconds between API calls (rate limit protection)")
    parser.add_argument("--resume", default=None, help="JSONL file path for incremental writes + resume from")
    args = parser.parse_args()

    print(f"Loading ground truth...")
    entries = load_ground_truth()
    print(f"Found {len(entries)} audio files with ground truth.\n")

    providers = args.providers or list(PROVIDERS.keys())
    print(f"Providers: {', '.join(providers)}")
    print(f"Limit: {args.limit or 'all'}")
    if args.files:
        print(f"Files: {', '.join(args.files)}")
    print(f"Repeats: {args.repeats}")
    if args.model:
        print(f"Model override: {args.model}")
    if args.delay:
        print(f"Delay: {args.delay}s between calls")
    if args.resume:
        print(f"Resume file: {args.resume}")
    print()

    print("Starting evaluation...")
    results = run_evaluation(
        entries,
        providers=providers,
        limit=args.limit,
        files=args.files,
        repeats=args.repeats,
        model_override=args.model,
        delay=args.delay,
        resume_file=args.resume,
    )

    csv_path, json_path = save_results(results, tag=args.tag)
    print(f"\nResults saved to:\n  CSV:  {csv_path}\n  JSON: {json_path}")

    print_summary(results)


if __name__ == "__main__":
    # Add project root to path so imports work
    sys.path.insert(0, str(Path(__file__).parent.parent))
    main()
