from __future__ import annotations

from dataclasses import dataclass, field

from wedding_photos.config import TABLES_YAML


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
