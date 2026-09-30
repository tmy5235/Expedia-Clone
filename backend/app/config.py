"""Backend-only configuration loaded from the project root."""

import os
from pathlib import Path

from dotenv import load_dotenv


def load_geoapify_api_key() -> str:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(dotenv_path=env_path, override=False)
    return os.environ.get("GEOAPIFY_API_KEY", "").strip()
