"""
Seed the database with guests and tables from YAML files.

Usage:
    python scripts/seed_db.py

Reads:
  - data/guests.yaml  (or $GUESTS_YAML)
  - data/tables.yaml  (or $TABLES_YAML)

Optional:
    --tables-csv <path>  Import tables from CSV instead of YAML. The CSV must
    include these columns exactly: id,name,date,subtitle,description,extract,media_folder

Guests are upserted by (name, surname) — duplicates are skipped.
Tables are upserted by id — existing rows are overwritten and their
media folder path is updated.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from pathlib import Path

# Ensure the src/ package is importable when run from the project root.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml
from sqlalchemy import select

from wedding_photos.config import GUESTS_YAML, TABLES_YAML
from wedding_photos.database import _engine, _session_factory, create_tables
from wedding_photos.db_models import Guest, Table


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

    def _media_folder_from_row(row: dict) -> str:
        # Backward-compatible fallback for old YAML format.
        if row.get("media_folder"):
            return str(row["media_folder"]).strip().strip("/")
        if row.get("cover"):
            cover = str(row["cover"]).strip().strip("/")
            return cover.rsplit("/", 1)[0] if "/" in cover else ""
        return ""

    for t in rows:
        table_id = t["id"]
        media_folder = _media_folder_from_row(t)

        # Upsert the Table row
        existing = await session.get(Table, table_id)
        if existing is None:
            table_row = Table(
                id=table_id,
                name=t["name"],
                description=t.get("description", ""),
                media_folder=media_folder,
                date=t.get("date"),
            )
            session.add(table_row)
        else:
            existing.name = t["name"]
            existing.description = t.get("description", "")
            existing.media_folder = media_folder
            existing.date = t.get("date")
            table_row = existing

        await session.flush()

        upserted += 1

    await session.commit()
    return upserted


async def seed_tables_from_csv(session, csv_path: Path) -> int:
    if not csv_path.exists():
        print(f"  tables CSV not found at {csv_path}, skipping.")
        return 0

    required_columns = [
        "id",
        "name",
        "date",
        "subtitle",
        "description",
        "extract",
        "media_folder",
    ]

    upserted = 0
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        missing = [c for c in required_columns if c not in fieldnames]
        if missing:
            raise ValueError("CSV missing required columns: " + ", ".join(missing))

        for row in reader:
            raw_id = str(row.get("id", "")).strip()
            if not raw_id:
                continue

            table_id = int(raw_id)
            name = str(row.get("name", "")).strip()
            date = str(row.get("date", "")).strip() or None
            subtitle = str(row.get("subtitle", "")).strip()
            description = str(row.get("description", "")).strip()
            extract = str(row.get("extract", "")).strip()
            media_folder = str(row.get("media_folder", "")).strip().strip("/")

            existing = await session.get(Table, table_id)
            if existing is None:
                table_row = Table(
                    id=table_id,
                    name=name,
                    date=date,
                    subtitle=subtitle,
                    description=description,
                    extract=extract,
                    media_folder=media_folder,
                )
                session.add(table_row)
            else:
                existing.name = name
                existing.date = date
                existing.subtitle = subtitle
                existing.description = description
                existing.extract = extract
                existing.media_folder = media_folder

            upserted += 1

    await session.commit()
    return upserted


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed guests and tables")
    parser.add_argument(
        "--tables-csv",
        default="",
        help=(
            "Optional CSV path for tables. If provided, YAML table import is skipped. "
            "Required columns: id,name,date,subtitle,description,extract,media_folder"
        ),
    )
    return parser.parse_args()


async def main() -> None:
    args = _parse_args()

    print("Creating tables if needed…")
    await create_tables()

    async with _session_factory() as session:
        print("Seeding guests…")
        n_guests = await seed_guests(session)
        print(f"  {n_guests} new guest(s) inserted.")

        print("Seeding tables…")
        if args.tables_csv:
            n_tables = await seed_tables_from_csv(session, Path(args.tables_csv))
        else:
            n_tables = await seed_tables(session)
        print(f"  {n_tables} table(s) upserted.")

    await _engine.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
