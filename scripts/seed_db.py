"""
Seed the database with guests and tables from YAML files.

Usage:
    python scripts/seed_db.py

Reads:
  - data/guests.yaml  (or $GUESTS_YAML)
  - data/tables.yaml  (or $TABLES_YAML)

Guests are upserted by (name, surname) — duplicates are skipped.
Tables are upserted by id — existing rows are overwritten and their
media items are replaced.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure the src/ package is importable when run from the project root.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml
from sqlalchemy import delete, select

from wedding_photos.config import GUESTS_YAML, TABLES_YAML
from wedding_photos.database import _engine, _session_factory, create_tables
from wedding_photos.db_models import Guest, Table, TableMedia


async def seed_guests(session) -> int:
    with Path(GUESTS_YAML).open() as f:
        data = yaml.safe_load(f) or []

    inserted = 0
    for g in data:
        name = g["name"].strip().lower()
        surname = g["surname"].strip().lower()
        existing = await session.execute(
            select(Guest).where(Guest.name == name, Guest.surname == surname)
        )
        if existing.scalar_one_or_none() is None:
            session.add(Guest(name=name, surname=surname))
            inserted += 1

    await session.commit()
    return inserted


async def seed_tables(session) -> int:
    tables_path = Path(str(TABLES_YAML))
    if not tables_path.exists():
        print(f"  tables YAML not found at {tables_path}, skipping.")
        return 0

    with tables_path.open() as f:
        data = yaml.safe_load(f) or {}

    rows = data.get("tables", [])
    upserted = 0

    for t in rows:
        table_id = t["id"]

        # Upsert the Table row
        existing = await session.get(Table, table_id)
        if existing is None:
            table_row = Table(
                id=table_id,
                name=t["name"],
                description=t.get("description", ""),
                cover=t.get("cover"),
                date=t.get("date"),
            )
            session.add(table_row)
        else:
            existing.name = t["name"]
            existing.description = t.get("description", "")
            existing.cover = t.get("cover")
            existing.date = t.get("date")
            table_row = existing

        await session.flush()

        # Replace media items
        await session.execute(delete(TableMedia).where(TableMedia.table_id == table_id))
        for position, key in enumerate(t.get("media", [])):
            session.add(TableMedia(table_id=table_id, key=key, position=position))

        upserted += 1

    await session.commit()
    return upserted


async def main() -> None:
    print("Creating tables if needed…")
    await create_tables()

    async with _session_factory() as session:
        print("Seeding guests…")
        n_guests = await seed_guests(session)
        print(f"  {n_guests} new guest(s) inserted.")

        print("Seeding tables…")
        n_tables = await seed_tables(session)
        print(f"  {n_tables} table(s) upserted.")

    await _engine.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
