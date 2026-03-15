"""Phase 0: Verify new inference platform provider API keys and capabilities.

Tests each provider with a single Hindi WAV file and a single code-mixed M4A file.
Reports: API key valid, transcription returned, audio format support.

Usage:
    python scripts/verify_providers.py                    # test all new providers
    python scripts/verify_providers.py --providers groq   # test specific provider
    python scripts/verify_providers.py --providers together_ai groq fireworks
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

# Test files: one Hindi WAV (public dataset), one code-mixed M4A (personal)
WAV_TEST = PROJECT_ROOT / "data" / "audio" / "indicvoices" / "indicvoices_hi_01.wav"
M4A_TEST = PROJECT_ROOT / "data" / "audio" / "personal" / "credit-card-application-1-hinglish.m4a"


def verify_together_ai():
    """Test Together AI Whisper endpoint using OpenAI-compatible API."""
    api_key = os.getenv("TOGETHER_API_KEY", "")
    if not api_key:
        return {"status": "skip", "reason": "TOGETHER_API_KEY not set in .env"}

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")

    results = {}
    for label, path in [("WAV (Hindi)", WAV_TEST), ("M4A (code-mixed)", M4A_TEST)]:
        if not path.exists():
            results[label] = {"status": "skip", "reason": f"File not found: {path}"}
            continue
        try:
            start = time.perf_counter()
            with open(path, "rb") as f:
                response = client.audio.transcriptions.create(
                    model="openai/whisper-large-v3",
                    file=f,
                    language="hi",
                    temperature=0,
                )
            latency = time.perf_counter() - start
            text = response.text if hasattr(response, "text") else str(response)
            results[label] = {
                "status": "ok",
                "transcript_preview": text[:120],
                "latency_seconds": round(latency, 2),
            }
        except Exception as e:
            results[label] = {"status": "error", "error": f"{type(e).__name__}: {e}"}

    return results


def verify_groq():
    """Test Groq Whisper endpoint."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return {"status": "skip", "reason": "GROQ_API_KEY not set in .env"}

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

    results = {}
    # Test with whisper-large-v3-turbo (Groq's primary offering)
    for label, path in [("WAV (Hindi)", WAV_TEST), ("M4A (code-mixed)", M4A_TEST)]:
        if not path.exists():
            results[label] = {"status": "skip", "reason": f"File not found: {path}"}
            continue
        try:
            start = time.perf_counter()
            with open(path, "rb") as f:
                response = client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=f,
                    language="hi",
                    temperature=0,
                )
            latency = time.perf_counter() - start
            text = response.text if hasattr(response, "text") else str(response)
            results[label] = {
                "status": "ok",
                "transcript_preview": text[:120],
                "latency_seconds": round(latency, 2),
            }
        except Exception as e:
            results[label] = {"status": "error", "error": f"{type(e).__name__}: {e}"}

    return results


def verify_fireworks():
    """Test Fireworks AI Whisper endpoint using OpenAI-compatible API."""
    api_key = os.getenv("FIREWORKS_API_KEY", "")
    if not api_key:
        return {"status": "skip", "reason": "FIREWORKS_API_KEY not set in .env"}

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url="https://audio-prod.api.fireworks.ai/v1")

    results = {}
    for label, path in [("WAV (Hindi)", WAV_TEST), ("M4A (code-mixed)", M4A_TEST)]:
        if not path.exists():
            results[label] = {"status": "skip", "reason": f"File not found: {path}"}
            continue
        try:
            start = time.perf_counter()
            with open(path, "rb") as f:
                response = client.audio.transcriptions.create(
                    model="whisper-v3",
                    file=f,
                    language="hi",
                    temperature=0,
                )
            latency = time.perf_counter() - start
            text = response.text if hasattr(response, "text") else str(response)
            results[label] = {
                "status": "ok",
                "transcript_preview": text[:120],
                "latency_seconds": round(latency, 2),
            }
        except Exception as e:
            results[label] = {"status": "error", "error": f"{type(e).__name__}: {e}"}

    return results


def verify_baseten():
    """Test Baseten Model API (shared endpoint, not dedicated deployment)."""
    api_key = os.getenv("BASETEN_API_KEY", "")
    if not api_key:
        return {"status": "skip", "reason": "BASETEN_API_KEY not set in .env"}

    # Baseten Model API uses a different pattern — direct HTTP POST
    # The exact endpoint depends on the model deployment. For Phase 0,
    # we just verify the API key is valid by hitting the models list endpoint.
    import requests

    try:
        response = requests.get(
            "https://api.baseten.co/v1/models",
            headers={"Authorization": f"Api-Key {api_key}"},
            timeout=10,
        )
        if response.status_code == 200:
            models = response.json().get("models", [])
            return {
                "status": "ok",
                "reason": f"API key valid. {len(models)} model(s) found.",
                "note": "Whisper transcription test requires a deployed model (Phase 2).",
            }
        else:
            return {
                "status": "error",
                "error": f"HTTP {response.status_code}: {response.text[:200]}",
            }
    except Exception as e:
        return {"status": "error", "error": f"{type(e).__name__}: {e}"}


PROVIDER_VERIFIERS = {
    "together_ai": ("Together AI", verify_together_ai),
    "groq": ("Groq", verify_groq),
    "fireworks": ("Fireworks AI", verify_fireworks),
    "baseten": ("Baseten", verify_baseten),
}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Verify inference platform API keys")
    parser.add_argument(
        "--providers",
        nargs="+",
        default=list(PROVIDER_VERIFIERS.keys()),
        choices=list(PROVIDER_VERIFIERS.keys()),
        help="Providers to verify",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Phase 0: Inference Platform Provider Verification")
    print("=" * 60)
    print(f"WAV test file:  {WAV_TEST}")
    print(f"M4A test file:  {M4A_TEST}")
    print()

    all_ok = True
    for provider_key in args.providers:
        display_name, verifier = PROVIDER_VERIFIERS[provider_key]
        print(f"--- {display_name} ---")

        result = verifier()

        if isinstance(result, dict) and "status" in result and result["status"] == "skip":
            print(f"  SKIPPED: {result['reason']}")
            all_ok = False
        elif isinstance(result, dict) and "status" in result:
            # Simple result (baseten key check)
            status = result["status"]
            icon = "OK" if status == "ok" else "FAIL"
            print(f"  [{icon}] {result.get('reason', result.get('error', ''))}")
            if result.get("note"):
                print(f"  Note: {result['note']}")
            if status != "ok":
                all_ok = False
        else:
            # Per-format results (together, groq, fireworks)
            for fmt_label, fmt_result in result.items():
                status = fmt_result["status"]
                icon = "OK" if status == "ok" else "FAIL"
                if status == "ok":
                    print(
                        f"  [{icon}] {fmt_label}: "
                        f"latency={fmt_result['latency_seconds']}s  "
                        f"transcript=\"{fmt_result['transcript_preview']}...\""
                    )
                elif status == "skip":
                    print(f"  [SKIP] {fmt_label}: {fmt_result['reason']}")
                else:
                    print(f"  [{icon}] {fmt_label}: {fmt_result['error']}")
                    all_ok = False
        print()

    print("=" * 60)
    if all_ok:
        print("All providers verified. Ready for Phase 1.")
    else:
        print("Some providers need attention. Fix issues above before proceeding.")
    print("=" * 60)


if __name__ == "__main__":
    main()
