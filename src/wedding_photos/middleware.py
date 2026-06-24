"""
Token validation middleware.

Every request must carry ?t=<SECRET_TOKEN> in the query string.
Static files are exempt — images loaded by <img> tags don't carry
query params, and the token gate on HTML pages is sufficient.
If the token is missing or incorrect, denied.html is served (HTTP 200
to avoid revealing the gate).
"""

from __future__ import annotations

from typing import Any

from fastapi import Request, Response

from wedding_photos.config import SECRET_TOKEN
from wedding_photos.templates import templates


def _normalize_path_for_routing(path: str, root_path: str) -> str:
    """Return path without optional app root prefix to make checks deployment-agnostic."""
    if root_path and path.startswith(root_path):
        stripped = path[len(root_path) :]
        return stripped if stripped.startswith("/") else f"/{stripped}"
    return path


async def require_token(request: Request, call_next: Any) -> Response:
    path = request.url.path
    normalized_path = _normalize_path_for_routing(
        path, request.scope.get("root_path", "")
    )

    # Static files and proxied site-photos are always allowed — images loaded by
    # <img> tags don't carry query params, and the token gate on HTML pages is sufficient.
    if normalized_path.startswith("/static") or normalized_path.startswith(
        "/api/site-photos"
    ):
        return await call_next(request)

    # Admin endpoints are protected by ADMIN_TOKEN Bearer header (checked in the
    # route dependency), not by the guest-facing secret token.
    if normalized_path.startswith("/api/admin"):
        return await call_next(request)

    token = request.query_params.get("t", "")
    if token != SECRET_TOKEN:
        return templates.TemplateResponse(request=request, name="denied.html")

    return await call_next(request)
