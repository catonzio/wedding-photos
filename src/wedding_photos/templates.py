from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

from wedding_photos.config import IS_PRODUCTION, TEMPLATES_DIR


def https_url_for(request: Request, name: str, **path_params: Any) -> str:

    http_url = request.url_for(name, **path_params)

    # Replace 'http' with 'https'
    return str(http_url).replace("http", "https", 1)


templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

if IS_PRODUCTION:
    templates.env.globals["https_url_for"] = https_url_for
