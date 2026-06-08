#!/usr/bin/env python3
"""
Upload table photos from a local folder to the MinIO site-photos bucket.

Usage
-----
    python scripts/upload_table_photos.py <photos_dir> [options]

Arguments
---------
  photos_dir   Root directory whose sub-folders are named ``table_1``,
               ``table_2``, … and contain the photos/videos for each table.

Options
-------
  --endpoint   MinIO endpoint  (default: $MINIO_ENDPOINT or localhost:9000)
  --access-key MinIO access key (default: $MINIO_ACCESS_KEY or minioadmin)
  --secret-key MinIO secret key (default: $MINIO_SECRET_KEY or minioadmin)
  --bucket     Destination bucket (default: $MINIO_SITE_PHOTOS_BUCKET or site-photos)
  --secure     Use HTTPS (flag; default: $MINIO_SECURE or false)
  --dry-run    Print what would be uploaded without actually uploading

Examples
--------
    # Upload all photos from ./static/media
    python scripts/upload_table_photos.py ./static/media

    # Point to a custom MinIO and bucket
    python scripts/upload_table_photos.py ./static/media \\
        --endpoint minio.example.com:9000 \\
        --bucket site-photos

    # Dry-run to verify what would be sent
    python scripts/upload_table_photos.py ./static/media --dry-run
"""

from __future__ import annotations

import argparse
import mimetypes
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# MIME type helpers
# ---------------------------------------------------------------------------

_SUPPORTED_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".heic",
    ".heif",
    ".mp4",
    ".mov",
    ".webm",
    ".avi",
    ".mkv",
}


def _mime_for(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "application/octet-stream"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload table photos to the MinIO site-photos bucket.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("photos_dir", help="Local folder with table_N sub-directories")
    parser.add_argument(
        "--endpoint",
        default=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        help="MinIO endpoint (default: %(default)s)",
    )
    parser.add_argument(
        "--access-key",
        default=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        help="MinIO access key (default: %(default)s)",
    )
    parser.add_argument(
        "--secret-key",
        default=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        help="MinIO secret key",
    )
    parser.add_argument(
        "--bucket",
        default=os.getenv("MINIO_SITE_PHOTOS_BUCKET", "site-photos"),
        help="Destination bucket (default: %(default)s)",
    )
    parser.add_argument(
        "--secure",
        action="store_true",
        default=os.getenv("MINIO_SECURE", "false").lower() == "true",
        help="Use HTTPS",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without uploading",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    args = _parse_args()

    photos_root = Path(args.photos_dir).resolve()
    if not photos_root.is_dir():
        print(f"ERROR: '{photos_root}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    # Collect files to upload: only table_N sub-directories
    files: list[tuple[Path, str]] = []  # (local_path, bucket_key)
    for table_dir in sorted(photos_root.iterdir()):
        if not table_dir.is_dir() or not table_dir.name.startswith("table_"):
            continue
        for photo in sorted(table_dir.rglob("*")):
            if not photo.is_file():
                continue
            if photo.suffix.lower() not in _SUPPORTED_SUFFIXES:
                print(f"  SKIP (unsupported type): {photo.relative_to(photos_root)}")
                continue
            # Key relative to the bucket root, e.g. table_1/cover.jpg
            key = photo.relative_to(photos_root).as_posix()
            files.append((photo, key))

    if not files:
        print("No supported media files found — nothing to upload.")
        return

    print(f"Found {len(files)} file(s) to upload to bucket '{args.bucket}'.")
    if args.dry_run:
        print("\n[DRY RUN] The following files would be uploaded:")
        for local, key in files:
            print(f"  {key}  ({local.stat().st_size:,} bytes)")
        return

    # Lazy import so the script works even if minio is not installed globally
    try:
        from minio import Minio  # noqa: PLC0415
        from minio.error import S3Error  # noqa: PLC0415
    except ImportError:
        print(
            "ERROR: 'minio' package not found. Install it with:\n  pip install minio",
            file=sys.stderr,
        )
        sys.exit(1)

    client = Minio(
        args.endpoint,
        access_key=args.access_key,
        secret_key=args.secret_key,
        secure=args.secure,
    )

    # Ensure the bucket exists
    try:
        if not client.bucket_exists(args.bucket):
            client.make_bucket(args.bucket)
            print(f"Created bucket '{args.bucket}'.")
    except S3Error as exc:
        if exc.code != "BucketAlreadyOwnedByYou":
            print(f"ERROR creating bucket: {exc}", file=sys.stderr)
            sys.exit(1)

    # Upload
    ok = 0
    errors = 0
    for local, key in files:
        mime = _mime_for(local)
        size = local.stat().st_size
        try:
            client.fput_object(args.bucket, key, str(local), content_type=mime)
            print(f"  OK  {key}  ({size:,} bytes)")
            ok += 1
        except Exception as exc:
            print(f"  ERR {key}: {exc}", file=sys.stderr)
            errors += 1

    print(f"\nDone: {ok} uploaded, {errors} errors.")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
