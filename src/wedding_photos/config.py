"""
Configuration — paths, settings, and table data loading.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent.parent

TEMPLATES_DIR = BASE_DIR / "src" / "templates"
STATIC_DIR = BASE_DIR / "static"
TABLES_YAML = Path(os.getenv("TABLES_YAML", BASE_DIR / "tables.yaml"))

STATIC_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
SECRET_TOKEN: str = os.getenv("SECRET_TOKEN", "")
if not SECRET_TOKEN:
    raise RuntimeError(
        "SECRET_TOKEN environment variable is not set. "
        'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
    )
