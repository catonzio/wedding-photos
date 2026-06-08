"""
MinIO client wrapper.

Two buckets are used:
  - uploads         (MINIO_UPLOADS_BUCKET)     — guest photo uploads
  - site-photos     (MINIO_SITE_PHOTOS_BUCKET)  — table/site photos

File downloads are proxied through the FastAPI app so the browser never needs
direct access to the MinIO service.
"""

from __future__ import annotations

import asyncio
import io
from functools import partial

from minio import Minio
from minio.error import S3Error

from wedding_photos.config import (
    MINIO_ACCESS_KEY,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
    MINIO_SECURE,
    MINIO_SITE_PHOTOS_BUCKET,
    MINIO_UPLOADS_BUCKET,
)

_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)


def ensure_buckets() -> None:
    """Create the uploads and site-photos buckets if they do not exist yet."""
    for bucket in (MINIO_UPLOADS_BUCKET, MINIO_SITE_PHOTOS_BUCKET):
        try:
            if not _client.bucket_exists(bucket):
                _client.make_bucket(bucket)
        except S3Error as exc:
            # Re-raise unexpected errors; swallow "already exists" races.
            if exc.code != "BucketAlreadyOwnedByYou":
                raise


# ---------------------------------------------------------------------------
# Guest uploads bucket
# ---------------------------------------------------------------------------


async def upload_file(key: str, data: bytes, content_type: str) -> str:
    """Upload *data* to the uploads bucket under *key* and return the key."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        partial(
            _client.put_object,
            MINIO_UPLOADS_BUCKET,
            key,
            io.BytesIO(data),
            len(data),
            content_type=content_type,
        ),
    )
    return key


async def get_file(key: str) -> tuple[bytes, str]:
    """Return the raw bytes and content-type for *key* from the uploads bucket."""
    loop = asyncio.get_event_loop()

    def _fetch() -> tuple[bytes, str]:
        response = _client.get_object(MINIO_UPLOADS_BUCKET, key)
        try:
            content_type = response.headers.get(
                "content-type", "application/octet-stream"
            )
            return response.read(), content_type
        finally:
            response.close()
            response.release_conn()

    return await loop.run_in_executor(None, _fetch)


# ---------------------------------------------------------------------------
# Site-photos bucket (table images)
# ---------------------------------------------------------------------------


async def upload_site_photo(key: str, data: bytes, content_type: str) -> str:
    """Upload *data* to the site-photos bucket under *key* and return the key."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        partial(
            _client.put_object,
            MINIO_SITE_PHOTOS_BUCKET,
            key,
            io.BytesIO(data),
            len(data),
            content_type=content_type,
        ),
    )
    return key


async def delete_site_photo(key: str) -> None:
    """Delete *key* from the site-photos bucket."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: _client.remove_object(MINIO_SITE_PHOTOS_BUCKET, key),
    )


async def get_site_photo(key: str) -> tuple[bytes, str]:
    """Return the raw bytes and content-type for *key* from the site-photos bucket."""
    loop = asyncio.get_event_loop()

    def _fetch() -> tuple[bytes, str]:
        response = _client.get_object(MINIO_SITE_PHOTOS_BUCKET, key)
        try:
            content_type = response.headers.get(
                "content-type", "application/octet-stream"
            )
            return response.read(), content_type
        finally:
            response.close()
            response.release_conn()

    return await loop.run_in_executor(None, _fetch)
