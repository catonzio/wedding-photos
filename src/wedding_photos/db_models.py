"""
ORM models for the wedding photos application.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wedding_photos.database import Base

# ---------------------------------------------------------------------------
# Guest model
# ---------------------------------------------------------------------------


class Guest(Base):
    __tablename__ = "guests"
    __table_args__ = (UniqueConstraint("name", "surname"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Stored in lower-case for case-insensitive lookup
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    surname: Mapped[str] = mapped_column(String(100), nullable=False)


# ---------------------------------------------------------------------------
# Table / TableMedia models
# ---------------------------------------------------------------------------


class Table(Base):
    __tablename__ = "tables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    cover: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[str | None] = mapped_column(String(100), nullable=True)

    media_items: Mapped[list[TableMedia]] = relationship(
        "TableMedia",
        back_populates="table",
        order_by="TableMedia.position",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def media(self) -> list[str]:
        return [m.key for m in self.media_items]


class TableMedia(Base):
    __tablename__ = "table_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    table_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tables.id", ondelete="CASCADE"), nullable=False
    )
    key: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    table: Mapped[Table] = relationship("Table", back_populates="media_items")


# ---------------------------------------------------------------------------
# Upload model
# ---------------------------------------------------------------------------


class Upload(Base):
    __tablename__ = "uploads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    guest_name: Mapped[str] = mapped_column(String(100), nullable=False)
    guest_surname: Mapped[str] = mapped_column(String(100), nullable=False)
    table_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    s3_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
