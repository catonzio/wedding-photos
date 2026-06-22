"""
Repository classes for guests, tables, and uploads.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_photos.db_models import Guest, Table, Upload

# ---------------------------------------------------------------------------
# Guest repository — DB-backed
# ---------------------------------------------------------------------------


class GuestRepository:
    @staticmethod
    async def validate(session: AsyncSession, name: str, surname: str) -> bool:
        """Return True if (name, surname) exists in the guests table (case-insensitive)."""
        result = await session.execute(
            select(Guest).where(
                Guest.name == name.strip().lower(),
                Guest.surname == surname.strip().lower(),
            )
        )
        return result.scalar_one_or_none() is not None


# ---------------------------------------------------------------------------
# Table repository
# ---------------------------------------------------------------------------


class TableRepository:
    @staticmethod
    async def list_all(session: AsyncSession) -> list[Table]:
        result = await session.execute(select(Table).order_by(Table.id))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, table_id: int) -> Table | None:
        result = await session.execute(select(Table).where(Table.id == table_id))
        return result.scalar_one_or_none()


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
