"""Configuration loader — reads API keys from .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# API Keys
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")

# Paths
DATA_DIR = PROJECT_ROOT / "data"
AUDIO_DIR = DATA_DIR / "audio"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"
RESULTS_DIR = DATA_DIR / "results"

# Ensure directories exist
for d in [AUDIO_DIR, GROUND_TRUTH_DIR, RESULTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
