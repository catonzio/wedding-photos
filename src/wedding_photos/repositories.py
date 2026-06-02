"""
Repository classes for guests and uploads.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_photos.config import GUESTS_YAML
from wedding_photos.db_models import Upload

# ---------------------------------------------------------------------------
# Guest repository — in-memory cache backed by guests.yaml
# ---------------------------------------------------------------------------


class GuestRepository:
    # Module-level cache: list of {"name": ..., "surname": ...} dicts (normalised lower-case)
    _cache: list[dict[str, str]] = []

    @classmethod
    def _load_from_disk(cls) -> list[dict[str, str]]:
        with Path(GUESTS_YAML).open() as f:
            data = yaml.safe_load(f) or []
        return [
            {"name": g["name"].strip().lower(), "surname": g["surname"].strip().lower()}
            for g in data
        ]

    @classmethod
    def load(cls) -> None:
        """Load guests from disk into the in-memory cache (called at startup)."""
        cls._cache = cls._load_from_disk()

    @classmethod
    def reload(cls) -> int:
        """Re-read guests.yaml and replace the cache. Returns number of guests loaded."""
        cls._cache = cls._load_from_disk()
        return len(cls._cache)

    @classmethod
    def validate(cls, name: str, surname: str) -> bool:
        """Return True if (name, surname) exists in the guest list (case-insensitive)."""
        needle = {"name": name.strip().lower(), "surname": surname.strip().lower()}
        return needle in cls._cache


# ---------------------------------------------------------------------------
# Upload repository — thin async wrappers over SQLAlchemy
# ---------------------------------------------------------------------------


class UploadRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        guest_name: str,
        guest_surname: str,
        table_id: int | None,
        s3_key: str,
        original_filename: str,
        mime_type: str,
    ) -> Upload:
        upload = Upload(
            id=uuid.uuid4(),
            guest_name=guest_name,
            guest_surname=guest_surname,
            table_id=table_id,
            s3_key=s3_key,
            original_filename=original_filename,
            mime_type=mime_type,
            created_at=datetime.now(timezone.utc),
        )
        session.add(upload)
        await session.commit()
        await session.refresh(upload)
        return upload

    @staticmethod
    async def list_all(session: AsyncSession) -> list[Upload]:
        result = await session.execute(
            select(Upload).order_by(Upload.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, upload_id: uuid.UUID) -> Upload | None:
        return await session.get(Upload, upload_id)
