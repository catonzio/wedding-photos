"""
MinIO client wrapper.

File downloads are proxied through the FastAPI app so the browser never needs
direct access to the MinIO service.
"""

from __future__ import annotations

import asyncio
import io
from functools import partial

from minio import Minio

from wedding_photos.config import (
    MINIO_ACCESS_KEY,
    MINIO_BUCKET,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
    MINIO_SECURE,
)

_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)


async def upload_file(key: str, data: bytes, content_type: str) -> str:
    """Upload *data* to MinIO under *key* and return the key."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        partial(
            _client.put_object,
            MINIO_BUCKET,
            key,
            io.BytesIO(data),
            len(data),
            content_type=content_type,
        ),
    )
    return key


async def get_file(key: str) -> tuple[bytes, str]:
    """Return the raw bytes and content-type for *key*."""
    loop = asyncio.get_event_loop()

    def _fetch() -> tuple[bytes, str]:
        response = _client.get_object(MINIO_BUCKET, key)
        try:
            content_type = response.headers.get(
                "content-type", "application/octet-stream"
            )
            return response.read(), content_type
        finally:
            response.close()
            response.release_conn()

    return await loop.run_in_executor(None, _fetch)
