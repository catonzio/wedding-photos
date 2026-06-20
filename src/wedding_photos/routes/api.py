"""
API routes for guest uploads and admin operations.

Endpoints:
  POST /api/guests/validate               — validate guest name + surname
  POST /api/uploads                       — upload a file
  GET  /api/uploads                       — list all uploads (for the gallery)
  GET  /api/uploads/{id}/media            — proxy file from MinIO uploads bucket
  GET  /api/site-photos/{path}            — proxy table photo from site-photos bucket
  POST /api/admin/tables/{id}/photos      — upload/replace a table photo (ADMIN_TOKEN)
  DELETE /api/admin/tables/{id}/photos/{key} — remove a table photo (ADMIN_TOKEN)
  POST /api/admin/reload-guests           — reload guests.yaml (ADMIN_TOKEN required)
"""

from __future__ import annotations

import asyncio
import io
import uuid
from typing import Annotated

import magic
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from PIL import Image, ImageOps
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_photos import storage
from wedding_photos.config import ADMIN_TOKEN
from wedding_photos.database import get_session
from wedding_photos.repositories import GuestRepository, UploadRepository

router = APIRouter(prefix="/api")

_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

_ALLOWED_MIME_PREFIXES = ("image/", "video/")

# Maximum long edge after resizing (pixels). Images larger than this are scaled
# down proportionally before compression. Set to 0 to disable resizing.
_MAX_DIMENSION = 2048

# JPEG/WebP compression quality (1–95). 82 gives ~70–80 % size reduction
# on typical smartphone photos with barely perceptible quality loss.
_JPEG_QUALITY = 82


def _compress_image(data: bytes, mime_type: str) -> tuple[bytes, str]:
    """Re-encode an image with Pillow to reduce file size.

    HEIC files are decoded by Pillow if pillow-heif is installed; otherwise
    they are left as-is.  All other recognised formats are re-encoded as JPEG
    (or kept as PNG when the source has transparency).  Videos are not touched.
    Returns the (possibly compressed) bytes and the resulting MIME type.
    """
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)
    except Exception:
        # If Pillow can't open it, return the original untouched.
        return data, mime_type

    # Resize if either dimension exceeds the limit
    if _MAX_DIMENSION > 0 and max(img.size) > _MAX_DIMENSION:
        img.thumbnail((_MAX_DIMENSION, _MAX_DIMENSION), Image.Resampling.LANCZOS)

    # Choose output format
    has_alpha = img.mode in ("RGBA", "LA", "PA") or (
        img.mode == "P" and "transparency" in img.info
    )
    if has_alpha:
        out_format = "PNG"
        out_mime = "image/png"
        save_kwargs: dict = {"optimize": True}
    else:
        out_format = "JPEG"
        out_mime = "image/jpeg"
        if img.mode != "RGB":
            img = img.convert("RGB")
        save_kwargs = {"quality": _JPEG_QUALITY, "optimize": True, "progressive": True}

    buf = io.BytesIO()
    img.save(buf, format=out_format, **save_kwargs)
    return buf.getvalue(), out_mime


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class ValidateRequest(BaseModel):
    name: str
    surname: str


class UploadOut(BaseModel):
    id: str
    guest_name: str
    guest_surname: str
    table_id: int | None
    original_filename: str
    mime_type: str
    media_url: str
    created_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_admin(request: Request) -> None:
    """Dependency: enforce ADMIN_TOKEN Bearer header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = auth.removeprefix("Bearer ").strip()
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")


def _upload_to_out(upload, request: Request) -> dict:
    token = request.query_params.get("t", "")
    # Return relative URL so browser uses the same scheme as the page (fixes mixed content warning)
    media_url = f"/wedding-photos/api/uploads/{upload.id}/media"
    if token:
        media_url = f"{media_url}?t={token}"
    return {
        "id": str(upload.id),
        "guest_name": upload.guest_name,
        "guest_surname": upload.guest_surname,
        "table_id": upload.table_id,
        "original_filename": upload.original_filename,
        "mime_type": upload.mime_type,
        "media_url": media_url,
        "created_at": upload.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/guests/validate")
async def validate_guest(body: ValidateRequest) -> dict:
    if not GuestRepository.validate(body.name, body.surname):
        raise HTTPException(
            status_code=422,
            detail="Nome e cognome non trovati nella lista degli invitati.",
        )
    return {"valid": True}


@router.post("/uploads")
async def create_upload(
    request: Request,
    name: Annotated[str, Form()],
    surname: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    table_id: Annotated[int | None, Form()] = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    # Re-validate guest
    if not GuestRepository.validate(name, surname):
        raise HTTPException(
            status_code=422,
            detail="Nome e cognome non trovati nella lista degli invitati.",
        )

    # Read file data
    data = await file.read()

    # Enforce size limit
    if len(data) > _MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File troppo grande (max 50 MB).")

    # Detect MIME type via magic bytes
    detected_mime = magic.from_buffer(data[:2048], mime=True)
    if not any(detected_mime.startswith(prefix) for prefix in _ALLOWED_MIME_PREFIXES):
        raise HTTPException(
            status_code=415,
            detail=f"Tipo di file non supportato: {detected_mime}.",
        )

    # Compress images in a thread pool to avoid blocking the event loop
    if detected_mime.startswith("image/"):
        loop = asyncio.get_event_loop()
        data, detected_mime = await loop.run_in_executor(
            None, _compress_image, data, detected_mime
        )

    # Derive extension from the (possibly updated) MIME type
    original_filename = file.filename or "upload"
    _mime_to_ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
    if detected_mime.startswith("image/"):
        suffix = _mime_to_ext.get(detected_mime, ".jpg")
    elif "." in original_filename:
        suffix = "." + original_filename.rsplit(".", 1)[-1].lower()
    else:
        suffix = ""

    s3_key = f"uploads/{uuid.uuid4()}{suffix}"

    # Upload to MinIO
    await storage.upload_file(s3_key, data, detected_mime)

    # Persist metadata
    upload = await UploadRepository.create(
        session,
        guest_name=name,
        guest_surname=surname,
        table_id=table_id,
        s3_key=s3_key,
        original_filename=original_filename,
        mime_type=detected_mime,
    )

    return _upload_to_out(upload, request)


@router.get("/uploads")
async def list_uploads(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    uploads = await UploadRepository.list_all(session)
    return [_upload_to_out(u, request) for u in uploads]


@router.get("/uploads/{upload_id}/media", name="get_upload_media")
async def get_upload_media(
    upload_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> Response:
    upload = await UploadRepository.get_by_id(session, upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload non trovato.")

    data, content_type = await storage.get_file(upload.s3_key)
    return Response(content=data, media_type=content_type)


@router.get("/site-photos/{photo_path:path}", name="get_site_photo")
async def get_site_photo(photo_path: str) -> Response:
    """Proxy a table photo from the site-photos bucket. No token required (used by <img> tags)."""
    try:
        data, content_type = await storage.get_site_photo(photo_path)
    except Exception:
        raise HTTPException(status_code=404, detail="Foto non trovata.")
    return Response(content=data, media_type=content_type)


@router.post("/admin/tables/{table_id}/photos", name="admin_upload_table_photo")
async def admin_upload_table_photo(
    table_id: int,
    file: Annotated[UploadFile, File()],
    _: None = Depends(_require_admin),
) -> dict:
    """Upload or replace a photo for *table_id* in the site-photos bucket.

    The file is stored at ``table_{id}/{original_filename}`` and the key is
    returned so the caller can update ``tables.yaml`` accordingly.
    """
    data = await file.read()

    if len(data) > _MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File troppo grande (max 50 MB).")

    detected_mime = magic.from_buffer(data[:2048], mime=True)
    if not any(detected_mime.startswith(p) for p in _ALLOWED_MIME_PREFIXES):
        raise HTTPException(
            status_code=415,
            detail=f"Tipo di file non supportato: {detected_mime}.",
        )

    original_filename = file.filename or "photo"
    key = f"table_{table_id}/{original_filename}"
    await storage.upload_site_photo(key, data, detected_mime)
    return {"key": key, "mime_type": detected_mime, "size": len(data)}


@router.delete(
    "/admin/tables/{table_id}/photos/{photo_key:path}", name="admin_delete_table_photo"
)
async def admin_delete_table_photo(
    table_id: int,
    photo_key: str,
    _: None = Depends(_require_admin),
) -> dict:
    """Delete a photo from the site-photos bucket.

    *photo_key* is the key relative to the bucket root (e.g. ``table_1/cover.jpg``).
    The key must belong to the given table (prefix ``table_{id}/``).
    """
    expected_prefix = f"table_{table_id}/"
    if not photo_key.startswith(expected_prefix):
        raise HTTPException(
            status_code=400,
            detail=f"La chiave deve iniziare con '{expected_prefix}'.",
        )
    try:
        await storage.delete_site_photo(photo_key)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"deleted": photo_key}


@router.post("/admin/reload-guests")
async def reload_guests(_: None = Depends(_require_admin)) -> dict:
    count = GuestRepository.reload()
    return {"loaded": count}
