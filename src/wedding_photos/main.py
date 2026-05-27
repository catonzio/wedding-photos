"""
Wedding Photos — FastAPI application entry point.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from wedding_photos.config import STATIC_DIR
from wedding_photos.middleware import require_token
from wedding_photos.routes import pages

app = FastAPI(title="Wedding Photos")

app.middleware("http")(require_token)

app.include_router(pages.router)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
