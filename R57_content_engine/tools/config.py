"""
Configuration loader for Creative Content Engine.
Loads API keys from references/.env and provides centralized constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from references/.env
PROJECT_ROOT = Path(__file__).parent.parent
ENV_PATH = PROJECT_ROOT / "references" / ".env"
load_dotenv(ENV_PATH)

# --- API Keys ---
FAL_API_KEY = os.getenv("FAL_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- WaveSpeed AI ---
WAVESPEED_API_KEY = os.getenv("WAVESPEED_API_KEY")
WAVESPEED_API_URL = "https://api.wavespeed.ai/api/v3"

# --- Fal.ai ---
# fal_client reads FAL_KEY from env; bridge it from FAL_API_KEY so users
# only have to set one variable in references/.env.
if FAL_API_KEY and not os.getenv("FAL_KEY"):
    os.environ["FAL_KEY"] = FAL_API_KEY

# --- Airtable ---
AIRTABLE_API_URL = "https://api.airtable.com/v0"
AIRTABLE_TABLE_NAME = "May2025 - Provinzial_Geier&Ayhan"

# --- Cost Constants (legacy — use get_cost() for multi-provider) ---
IMAGE_COST = 0.04   # per Nano Banana image via Fal (approximate)
VIDEO_COST = 0.40   # per Kling/Sora video via Fal (approximate)
WAVESPEED_VIDEO_COST = 0.30  # per Kling/Sora video via WaveSpeed (approximate)

# --- Per-model per-provider costs ---
# Fal prices are approximate — verify at fal.ai/models/<model>/api.
COSTS = {
    # Image models
    ("nano-banana", "google"): 0.04,
    ("nano-banana", "fal"): 0.04,
    ("nano-banana-pro", "google"): 0.13,
    ("nano-banana-pro", "fal"): 0.04,
    ("gpt-image-1.5", "wavespeed"): 0.07,  # ~$0.04 medium / ~$0.08 high via OpenAI — verify at wavespeed.ai
    # Video models
    ("veo-3.1", "google"): 0.50,
    ("kling-3.0", "fal"): 0.45,           # Kling 2.1 master on Fal — verify
    ("sora-2-pro", "fal"): 0.50,          # Sora 2 i2v Pro on Fal — verify
    ("kling-3.0", "wavespeed"): 0.30,
    ("sora-2", "wavespeed"): 0.30,
    ("sora-2-pro", "wavespeed"): 0.30,
}

# --- Default Models ---
DEFAULT_IMAGE_MODEL = "nano-banana-pro"
DEFAULT_VIDEO_MODEL = "veo-3.1"

# --- Directories ---
INPUTS_DIR = PROJECT_ROOT / "references" / "inputs"

# --- Video Models (Fal.ai) ---
# All Fal video endpoints are image-to-video and consume a hosted image_url.
# Kling 3.0 → Kling v2.1 master on Fal (closest equivalent).
# Sora 2 Pro → fal-ai/sora-2/image-to-video/pro.
VIDEO_MODELS = {
    "kling-3.0": "fal-ai/kling-video/v2.1/master/image-to-video",
    "sora-2-pro": "fal-ai/sora-2/image-to-video/pro",
    "veo-3.1": "veo-3.1-generate-preview",
}

# --- Video Models (WaveSpeed AI) ---
# Same models available through WaveSpeed's infrastructure.
# WaveSpeed uses model ID in the URL path (not request body).
WAVESPEED_VIDEO_MODELS = {
    "kling-3.0": "kwaivgi/kling-v3.0-pro/image-to-video",
    "kling-3.0-std": "kwaivgi/kling-v3.0-std/image-to-video",
    "sora-2": "openai/sora-2/image-to-video",
    "sora-2-pro": "openai/sora-2/image-to-video-pro",
}


def get_cost(model, provider=None):
    """
    Get the cost per generation for a model+provider combination.

    Args:
        model: Model name (e.g., "nano-banana-pro", "veo-3.1")
        provider: Provider name (e.g., "google", "fal"). If None, uses default.

    Returns:
        float: Cost per unit
    """
    if provider is None:
        # Import here to avoid circular imports
        from .providers import IMAGE_PROVIDERS, VIDEO_PROVIDERS
        if model in IMAGE_PROVIDERS:
            provider = IMAGE_PROVIDERS[model]["default"]
        elif model in VIDEO_PROVIDERS:
            provider = VIDEO_PROVIDERS[model]["default"]
        else:
            return 0.0
    return COSTS.get((model, provider), 0.0)


def check_credentials():
    """Verify required API keys are set. Returns list of missing keys."""
    required = {
        "AIRTABLE_API_KEY": AIRTABLE_API_KEY,
        "AIRTABLE_BASE_ID": AIRTABLE_BASE_ID,
    }
    missing = [name for name, value in required.items() if not value]

    # At least one generation provider must be configured
    if not FAL_API_KEY and not GOOGLE_API_KEY:
        missing.append("FAL_API_KEY or GOOGLE_API_KEY (at least one required)")

    if missing:
        print("Missing API keys:")
        for key in missing:
            print(f"  - {key}")
        print(f"\nAdd them to: {ENV_PATH}")
    return missing


def check_wavespeed_credentials():
    """Verify WaveSpeed API key + Airtable keys are set. Returns list of missing keys."""
    required = {
        "WAVESPEED_API_KEY": WAVESPEED_API_KEY,
        "AIRTABLE_API_KEY": AIRTABLE_API_KEY,
        "AIRTABLE_BASE_ID": AIRTABLE_BASE_ID,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        print("Missing API keys:")
        for key in missing:
            print(f"  - {key}")
        print(f"\nAdd them to: {ENV_PATH}")
    return missing
