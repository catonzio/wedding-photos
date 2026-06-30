"""
Media normalization helpers.

Converts uploaded media into browser-friendly formats before storage,
including image resizing and compression.
"""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageOps

try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except Exception:
    # Optional dependency. If unavailable, HEIC/HEIF decoding may fail.
    pass

SUPPORTED_IMAGE_MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

SUPPORTED_VIDEO_MIME_TO_EXT = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
}


def normalize_media_for_web(
    data: bytes,
    detected_mime: str,
    original_filename: str,
    *,
    max_dimension: int = 2048,
    jpeg_quality: int = 82,
) -> tuple[bytes, str, str]:
    """Return media bytes in a web-friendly format.

    For images, decode with Pillow, optionally resize, then re-encode to
    JPEG/PNG with compression.
    For videos, allow only MP4/WebM/QuickTime and pass through unchanged.

    Returns ``(normalized_bytes, mime_type, extension)``.
    Raises ``ValueError`` when the media type cannot be normalized safely.
    """
    if detected_mime.startswith("image/"):
        return _normalize_image_for_web(
            data,
            detected_mime,
            max_dimension=max_dimension,
            jpeg_quality=jpeg_quality,
        )

    if detected_mime.startswith("video/"):
        suffix = SUPPORTED_VIDEO_MIME_TO_EXT.get(detected_mime)
        if not suffix:
            raise ValueError(
                "Video format not supported by the web gallery. "
                f"Received: {detected_mime}"
            )
        return data, detected_mime, suffix

    suffix = Path(original_filename).suffix.lower()
    raise ValueError(
        "Unsupported media type. "
        f"Detected MIME: {detected_mime} (file suffix: {suffix or 'n/a'})"
    )


def _normalize_image_for_web(
    data: bytes,
    detected_mime: str,
    *,
    max_dimension: int,
    jpeg_quality: int,
) -> tuple[bytes, str, str]:
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)
    except Exception as exc:
        raise ValueError(
            "Image format cannot be decoded. "
            "Install pillow-heif for HEIC/HEIF support. "
            f"Detected MIME: {detected_mime}"
        ) from exc

    if max_dimension > 0 and max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    has_alpha = img.mode in ("RGBA", "LA", "PA") or (
        img.mode == "P" and "transparency" in img.info
    )
    is_animated = bool(getattr(img, "is_animated", False))

    if has_alpha and not is_animated:
        out_format = "PNG"
        out_mime = "image/png"
        suffix = SUPPORTED_IMAGE_MIME_TO_EXT[out_mime]
        save_kwargs: dict = {"optimize": True}
    else:
        out_format = "JPEG"
        out_mime = "image/jpeg"
        suffix = SUPPORTED_IMAGE_MIME_TO_EXT[out_mime]
        if img.mode != "RGB":
            img = img.convert("RGB")
        save_kwargs = {
            "quality": jpeg_quality,
            "optimize": True,
            "progressive": True,
        }

    out = io.BytesIO()
    img.save(out, format=out_format, **save_kwargs)
    return out.getvalue(), out_mime, suffix
