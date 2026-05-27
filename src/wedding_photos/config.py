"""
Configuration — paths, settings, and table data loading.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
TABLES_YAML = Path(os.getenv("TABLES_YAML", BASE_DIR.parent.parent / "tables.yaml"))

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


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Table:
    id: int
    name: str
    description: str
    cover: str | None
    media: list[str] = field(default_factory=list)


def load_tables() -> list[Table]:
    """Load tables from tables.yaml."""
    import yaml  # noqa: PLC0415 — only imported when needed

    with TABLES_YAML.open() as f:
        data = yaml.safe_load(f)
    return [
        Table(
            id=t.get("id"),
            name=t.get("name"),
            description=t.get("description", ""),
            cover=t.get("cover"),
            media=t.get("media", []),
        )
        for t in data.get("tables", [])
    ]
