"""
Download audio subsets from public speech datasets for the banking eval.

Datasets:
  1. IndicVoices (ai4bharat/indicvoices_r) — Hindi + Kannada, ~10 clips
  2. Svarah (ai4bharat/Svarah) — Indian-accented English, ~5 clips
  3. Mozilla Common Voice (fsicoli/common_voice_17_0) — Hindi + Kannada, ~5 clips

Each dataset is streamed (not fully downloaded) and filtered for clips whose
ground-truth text contains banking-related keywords. If not enough banking
clips are found, general conversational clips are selected as proxies.

Usage:
    python scripts/download_data.py [--hf-token YOUR_TOKEN]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import soundfile as sf
from dotenv import load_dotenv

# Load .env from project root
_project_root = Path(__file__).parent.parent
load_dotenv(_project_root / ".env")

# ── Banking keyword filter ────────────────────────────────────────────────

# Hindi (Devanagari + transliterated) banking terms
HINDI_BANKING_KEYWORDS = [
    # Devanagari
    "खाता", "पैसा", "पैसे", "बैंक", "लेनदेन", "भुगतान", "जमा", "निकासी",
    "ब्याज", "ऋण", "कर्ज", "चेक", "बचत", "शेष", "राशि", "हस्तांतरण",
    "क्रेडिट", "डेबिट", "लोन", "किस्त", "बिल",
    # Transliterated
    "paisa", "paise", "bank", "account", "payment", "transfer", "loan",
    "credit", "debit", "cheque", "deposit", "withdraw", "balance",
    "transaction", "rupee", "rupay", "bill", "emi", "interest",
]

# Kannada banking terms
KANNADA_BANKING_KEYWORDS = [
    "ಖಾತೆ", "ಹಣ", "ಬ್ಯಾಂಕ್", "ಪಾವತಿ", "ಸಾಲ", "ಬಡ್ಡಿ", "ಠೇವಣಿ",
    "ವರ್ಗಾವಣೆ", "ಶಿಲ್ಕು", "ಚೆಕ್",
]

# English banking terms (for Svarah + Common Voice English)
ENGLISH_BANKING_KEYWORDS = [
    "bank", "account", "balance", "payment", "transfer", "loan", "credit",
    "debit", "deposit", "withdraw", "transaction", "cheque", "check",
    "interest", "savings", "emi", "installment", "bill", "rupee", "money",
    "amount", "salary", "pension", "insurance", "investment", "atm", "upi",
    "neft", "rtgs", "ifsc",
]

# General conversational keywords (fallback — queries, complaints, requests)
GENERAL_KEYWORDS = [
    "please", "help", "problem", "issue", "want", "need", "give", "tell",
    "kripya", "madad", "samasya", "chahiye", "dijiye", "bataye",
    "samasyA", "dayavittu", "sahaya",
    # Numbers (often appear in financial contexts)
    "hundred", "thousand", "lakh", "crore", "hazaar", "sau",
]

ALL_KEYWORDS = (
    HINDI_BANKING_KEYWORDS
    + KANNADA_BANKING_KEYWORDS
    + ENGLISH_BANKING_KEYWORDS
    + GENERAL_KEYWORDS
)

# Compile a single regex for fast matching
_kw_pattern = re.compile(
    "|".join(re.escape(kw) for kw in ALL_KEYWORDS),
    re.IGNORECASE,
)


def has_banking_keywords(text: str) -> bool:
    """Check if text contains any banking-related keyword."""
    return bool(_kw_pattern.search(text))


# ── Helpers ───────────────────────────────────────────────────────────────

def save_audio(audio_dict: dict, out_path: Path) -> None:
    """Save a HuggingFace audio dict (array + sampling_rate) to WAV."""
    sf.write(str(out_path), audio_dict["array"], audio_dict["sampling_rate"])


def save_ground_truth(entries: List[Dict], out_path: Path) -> None:
    """Save ground truth entries as JSON."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"  Saved ground truth → {out_path} ({len(entries)} entries)")


# ── Dataset downloaders ──────────────────────────────────────────────────

def download_indicvoices(
    audio_dir: Path,
    gt_dir: Path,
    hf_token: Optional[str],
    target_per_lang: int = 5,
    scan_limit: int = 500,
) -> List[Dict]:
    """Download Hindi + Kannada clips from IndicVoices-R."""
    from datasets import load_dataset

    entries = []

    for lang_config in ["Hindi", "Kannada"]:
        lang_code = lang_config[:2].lower()
        out_subdir = audio_dir / "indicvoices"
        out_subdir.mkdir(parents=True, exist_ok=True)

        print(f"\n[IndicVoices] Streaming {lang_config} test split...")
        try:
            ds = load_dataset(
                "ai4bharat/indicvoices_r",
                name=lang_config,
                split="test",
                streaming=True,
                token=hf_token,
            )
        except Exception as e:
            print(f"  ERROR loading {lang_config}: {e}")
            print("  → Is the dataset gated? Accept terms at: "
                  "https://huggingface.co/datasets/ai4bharat/indicvoices_r")
            continue

        banking_clips = []
        general_clips = []
        scanned = 0

        for sample in ds:
            scanned += 1
            if scanned > scan_limit:
                break

            text = sample.get("text") or sample.get("normalized") or ""
            if not text.strip():
                continue

            duration = sample.get("duration", 0)
            if duration < 2.0 or duration > 30.0:
                continue

            if has_banking_keywords(text):
                banking_clips.append(sample)
            elif len(general_clips) < target_per_lang * 2:
                general_clips.append(sample)

            if len(banking_clips) >= target_per_lang:
                break

        # Use banking clips first, fill remaining with general
        selected = banking_clips[:target_per_lang]
        if len(selected) < target_per_lang:
            remaining = target_per_lang - len(selected)
            selected.extend(general_clips[:remaining])

        print(f"  Scanned {scanned} samples, found {len(banking_clips)} banking, "
              f"selected {len(selected)} total")

        for i, sample in enumerate(selected):
            fname = f"indicvoices_{lang_code}_{i+1:02d}.wav"
            fpath = out_subdir / fname
            save_audio(sample["audio"], fpath)

            text = sample.get("text") or sample.get("normalized") or ""
            entry = {
                "filename": fname,
                "source": "indicvoices",
                "language": lang_code,
                "text": text,
                "duration": sample.get("duration", 0),
                "scenario": "S1" if lang_code == "hi" else "S4",
                "has_banking_keywords": has_banking_keywords(text),
                "speaker_id": sample.get("speaker_id", ""),
                "gender": sample.get("gender", ""),
            }
            entries.append(entry)
            print(f"  Saved {fname} ({entry['duration']:.1f}s)")

    return entries


def download_svarah(
    audio_dir: Path,
    gt_dir: Path,
    hf_token: Optional[str],
    target: int = 5,
    scan_limit: int = 500,
) -> List[Dict]:
    """Download Indian-accented English clips from Svarah."""
    from datasets import load_dataset

    out_subdir = audio_dir / "svarah"
    out_subdir.mkdir(parents=True, exist_ok=True)

    print("\n[Svarah] Streaming test split...")
    try:
        ds = load_dataset(
            "ai4bharat/Svarah",
            split="test",
            streaming=True,
            token=hf_token,
        )
    except Exception as e:
        print(f"  ERROR: {e}")
        print("  → Accept terms at: https://huggingface.co/datasets/ai4bharat/Svarah")
        return []

    banking_clips = []
    general_clips = []
    scanned = 0

    for sample in ds:
        scanned += 1
        if scanned > scan_limit:
            break

        text = sample.get("text", "")
        if not text.strip():
            continue

        duration = sample.get("duration", 0)
        if duration < 2.0 or duration > 30.0:
            continue

        if has_banking_keywords(text):
            banking_clips.append(sample)
        elif len(general_clips) < target * 2:
            general_clips.append(sample)

        if len(banking_clips) >= target:
            break

    selected = banking_clips[:target]
    if len(selected) < target:
        remaining = target - len(selected)
        selected.extend(general_clips[:remaining])

    print(f"  Scanned {scanned} samples, found {len(banking_clips)} banking, "
          f"selected {len(selected)} total")

    entries = []
    for i, sample in enumerate(selected):
        fname = f"svarah_en_{i+1:02d}.wav"
        fpath = out_subdir / fname
        # Svarah uses "audio_filepath" not "audio"
        audio_data = sample.get("audio_filepath") or sample.get("audio")
        save_audio(audio_data, fpath)

        text = sample.get("text", "")
        entry = {
            "filename": fname,
            "source": "svarah",
            "language": "en-IN",
            "text": text,
            "duration": sample.get("duration", 0),
            "scenario": "S2",
            "has_banking_keywords": has_banking_keywords(text),
            "primary_language": sample.get("primary_language", ""),
            "gender": sample.get("gender", ""),
        }
        entries.append(entry)
        print(f"  Saved {fname} ({entry['duration']:.1f}s)")

    return entries


def download_common_voice(
    audio_dir: Path,
    gt_dir: Path,
    hf_token: Optional[str],
    target_per_lang: int = 3,
    scan_limit: int = 300,
) -> List[Dict]:
    """Download Hindi + Kannada clips from Common Voice (community fork)."""
    from datasets import load_dataset

    entries = []

    for lang_code in ["hi", "kn"]:
        out_subdir = audio_dir / "common_voice"
        out_subdir.mkdir(parents=True, exist_ok=True)

        print(f"\n[Common Voice] Streaming {lang_code} test split...")
        try:
            ds = load_dataset(
                "fsicoli/common_voice_17_0",
                lang_code,
                split="test",
                streaming=True,
                trust_remote_code=True,
            )
        except Exception as e:
            print(f"  ERROR loading {lang_code}: {e}")
            print("  → Trying validation split...")
            try:
                ds = load_dataset(
                    "fsicoli/common_voice_17_0",
                    lang_code,
                    split="validation",
                    streaming=True,
                    trust_remote_code=True,
                )
            except Exception as e2:
                print(f"  ERROR on validation too: {e2}")
                continue

        banking_clips = []
        general_clips = []
        scanned = 0

        for sample in ds:
            scanned += 1
            if scanned > scan_limit:
                break

            text = sample.get("sentence", "")
            if not text.strip():
                continue

            if has_banking_keywords(text):
                banking_clips.append(sample)
            elif len(general_clips) < target_per_lang * 2:
                general_clips.append(sample)

            if len(banking_clips) >= target_per_lang:
                break

        selected = banking_clips[:target_per_lang]
        if len(selected) < target_per_lang:
            remaining = target_per_lang - len(selected)
            selected.extend(general_clips[:remaining])

        print(f"  Scanned {scanned} samples, found {len(banking_clips)} banking, "
              f"selected {len(selected)} total")

        for i, sample in enumerate(selected):
            fname = f"cv_{lang_code}_{i+1:02d}.wav"
            fpath = out_subdir / fname
            save_audio(sample["audio"], fpath)

            text = sample.get("sentence", "")
            entry = {
                "filename": fname,
                "source": "common_voice",
                "language": lang_code,
                "text": text,
                "duration": len(sample["audio"]["array"]) / sample["audio"]["sampling_rate"],
                "scenario": "S1" if lang_code == "hi" else "S4",
                "has_banking_keywords": has_banking_keywords(text),
                "gender": sample.get("gender", ""),
                "age": sample.get("age", ""),
            }
            entries.append(entry)
            print(f"  Saved {fname} ({entry['duration']:.1f}s)")

    return entries


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Download speech eval audio subsets")
    parser.add_argument("--hf-token", default=None, help="HuggingFace token for gated datasets")
    args = parser.parse_args()

    # Resolve token: CLI arg > env var > None
    hf_token = args.hf_token
    if not hf_token:
        hf_token = os.getenv("HF_TOKEN") or None

    project_root = Path(__file__).parent.parent
    audio_dir = project_root / "data" / "audio"
    gt_dir = project_root / "data" / "ground_truth"

    all_entries = []

    # 1. IndicVoices — ~14 clips (7 Hindi, 7 Kannada)
    #    Increased from 5/lang to 7/lang to compensate for Common Voice being unavailable
    print("=" * 60)
    print("DOWNLOADING INDICVOICES SUBSET")
    print("=" * 60)
    iv_entries = download_indicvoices(audio_dir, gt_dir, hf_token, target_per_lang=7)
    all_entries.extend(iv_entries)

    # 2. Svarah — ~7 clips (Indian-accented English)
    #    Increased from 5 to 7 to compensate for Common Voice being unavailable
    print("\n" + "=" * 60)
    print("DOWNLOADING SVARAH SUBSET")
    print("=" * 60)
    sv_entries = download_svarah(audio_dir, gt_dir, hf_token, target=7)
    all_entries.extend(sv_entries)

    # 3. Common Voice — SKIPPED
    #    Mozilla emptied all Common Voice datasets on HuggingFace (Oct 2025).
    #    The community fork (fsicoli) uses loading scripts which datasets>=4.5 no
    #    longer supports. Per plan fallback: relying on IndicVoices + Svarah +
    #    personal recordings instead.
    print("\n" + "=" * 60)
    print("SKIPPING COMMON VOICE (unavailable on HuggingFace)")
    print("=" * 60)
    print("  Mozilla emptied HF datasets; community forks use deprecated loading scripts.")
    print("  Compensating with extra IndicVoices + Svarah clips.")

    # Save combined ground truth
    save_ground_truth(all_entries, gt_dir / "dataset_ground_truth.json")

    # Summary
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    by_source = {}
    for e in all_entries:
        by_source.setdefault(e["source"], []).append(e)
    for source, clips in by_source.items():
        banking = sum(1 for c in clips if c.get("has_banking_keywords"))
        print(f"  {source}: {len(clips)} clips ({banking} with banking keywords)")
    print(f"  TOTAL: {len(all_entries)} clips from public datasets")
    print(f"\n  Personal recordings: add 5-6 clips to data/audio/personal/")
    print(f"  Then fill in data/ground_truth/personal_template.json")


if __name__ == "__main__":
    main()
