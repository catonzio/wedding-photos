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
TABLES_YAML = Path(os.getenv("TABLES_YAML", BASE_DIR / "data" / "tables.yaml"))

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

ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "")
if not ADMIN_TOKEN:
    raise RuntimeError(
        "ADMIN_TOKEN environment variable is not set. "
        'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
    )

GUESTS_YAML: str = os.getenv("GUESTS_YAML", str(BASE_DIR / "data" / "guests.yaml"))

# ---------------------------------------------------------------------------
# MinIO
# ---------------------------------------------------------------------------
MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "wedding-uploads")
MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASE_URL: str = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://wedding:wedding@localhost:5432/wedding"
)
