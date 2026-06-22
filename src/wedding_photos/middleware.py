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
from fastapi.templating import Jinja2Templates

from wedding_photos.config import SECRET_TOKEN, TEMPLATES_DIR

_templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


async def require_token(request: Request, call_next: Any) -> Response:
    path = request.url.path

    # Static files and proxied site-photos are always allowed — images loaded by
    # <img> tags don't carry query params, and the token gate on HTML pages is sufficient.
    if path.startswith("/wedding-photos/static") or "/api/site-photos" in path:
        return await call_next(request)

    # Admin endpoints are protected by ADMIN_TOKEN Bearer header (checked in the
    # route dependency), not by the guest-facing secret token.
    if path.startswith("/api/admin"):
        return await call_next(request)

    token = request.query_params.get("t", "")
    if token != SECRET_TOKEN:
        return _templates.TemplateResponse(request=request, name="denied.html")

    return await call_next(request)
