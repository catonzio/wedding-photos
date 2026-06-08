"""
Wedding Photos — FastAPI application entry point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from wedding_photos.config import STATIC_DIR
from wedding_photos.database import create_tables
from wedding_photos.middleware import require_token
from wedding_photos.repositories import GuestRepository
from wedding_photos.routes import api, pages
from wedding_photos import storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure MinIO buckets exist before accepting requests.
    storage.ensure_buckets()
    # Create DB tables and load guest list before accepting requests.
    await create_tables()
    GuestRepository.load()
    yield


app = FastAPI(title="Wedding Photos", lifespan=lifespan)

app.middleware("http")(require_token)

app.include_router(pages.router)
app.include_router(api.router)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
