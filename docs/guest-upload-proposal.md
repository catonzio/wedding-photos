# Guest Upload Feature — Implementation Proposal

> Author: Danilo Catone  
> Date: 2026-05-31  
> Status: Draft — pending implementation

---

## Description

Add a guest-facing photo/video upload feature to the wedding app. The homepage gains a tab bar with two tabs: **"I Tavoli"** (existing table grid) and **"Le Foto"** (global upload gallery). Any guest can open the gallery tab, tap an upload button, confirm their identity (name + surname validated against a known guest list), and submit photos or short videos. Uploads are stored in MinIO (S3-compatible object storage) and their metadata in PostgreSQL. The gallery renders immediately after upload — no moderation step.

The feature is intentionally scoped to the wedding day: no admin panel, no CDN, no background processing.

---

## Functional Requirements

### Tab Bar (UI)

- FR-1: The `/menu` page displays a tab bar with two tabs: "I Tavoli" and "Le Foto".
- FR-2: Switching tabs does not navigate to a new page; it shows/hides the two content sections via Alpine.js.

### Gallery Tab

- FR-3: The "Le Foto" tab shows a scrollable grid of all guest-uploaded photos and videos across all tables.
- FR-4: Each grid cell shows the thumbnail and the uploader's first name.
- FR-5: Tapping a cell opens the media in a full-screen overlay (lightbox).
- FR-6: A prominent "Carica una foto" button is always visible in the tab.
- FR-7: Newly uploaded media appears immediately in the grid (immediate visibility, no approval step).

### Upload Dialog

- FR-8: Tapping the upload button opens a modal dialog (not a new page).
- FR-9: The dialog collects **nome** and **cognome** (required fields).
- FR-9b: After a successful validation, **nome** and **cognome** are stored on the client (e.g., localStorage) and pre-used for subsequent uploads, so the guest is asked only once per device/browser.
- FR-10: On submit, the backend validates that the name+surname pair exists in the known guest list (case-insensitive exact match). If not found, an error message is shown inline; the dialog stays open.
- FR-11: After successful name validation, a file picker is shown accepting images (JPEG, PNG, HEIC) and short videos (MP4, MOV). Multiple files can be selected.
- FR-12: Upload progress is shown per file. On completion the dialog closes and the gallery refreshes.
- FR-13: Uploaded files are linked to the guest's identity in the database.

### Guest List

- FR-14: The guest list is stored in a `guests.yaml` file at the project root (editable before the event).
- FR-15: The app loads the guest list at startup and caches it in memory.
- FR-15b: A `POST /api/admin/reload-guests` endpoint reloads the guest list from disk without restarting the container. The endpoint is protected by a separate `ADMIN_TOKEN` (distinct from the guest-facing `SECRET_TOKEN`) passed as a Bearer token in the `Authorization` header.

### Backend API

- FR-16: `POST /api/guests/validate` — validates `{name, surname}`, returns 200 or 422.
- FR-17: `POST /api/uploads` — multipart form: `name`, `surname`, `table_id` (optional), `file`. Re-validates guest. Uploads file to MinIO. Stores metadata in DB. Returns the created upload record.
- FR-18: `GET /api/uploads` — returns all upload records (id, guest name, thumbnail URL, full URL, created_at). Used by the gallery to populate the grid.

### Infrastructure

- FR-19: PostgreSQL added to `compose.yaml` as the `db` service.
- FR-20: MinIO added to `compose.yaml` as the `minio` service with a pre-created bucket.

---

## Non-Functional Requirements

- NFR-1: **Security** — Uploaded file type is validated server-side via MIME type detection (magic bytes), not just extension. Files are stored under a UUID key in MinIO, never executed.
- NFR-2: **Security** — All upload endpoints remain behind the existing `?t=<token>` middleware.
- NFR-3: **File size** — Max 50 MB per file. Enforced at the FastAPI route level.
- NFR-4: **Performance** — MinIO and DB I/O are async (aiobotocore or the minio-py async client; SQLAlchemy async engine with asyncpg).
- NFR-5: **Resilience** — DB tables are created via SQLAlchemy `create_all` at app startup (no Alembic for this single-event use case).
- NFR-6: **Mobile-first** — The dialog and gallery are fully usable on a 375 px wide viewport with touch interactions.
- NFR-7: **No build step** — All frontend additions use Alpine.js and Tailwind CSS via CDN, consistent with the existing stack.
- NFR-8: **Portability** — All new services (PostgreSQL, MinIO) are defined in `compose.yaml`; the app remains deployable with `docker compose up -d`.

---

## Architecture Overview

### New Services (compose.yaml)

```text
db      — postgres:17-alpine, volume-backed
minio   — minio/minio:latest, volume-backed, single node
```

### New Environment Variables (.env)

```text
DATABASE_URL=postgresql+asyncpg://wedding:wedding@db:5432/wedding
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
MINIO_BUCKET=wedding-uploads
GUESTS_YAML=guests.yaml          # path to guest list
ADMIN_TOKEN=...                  # token for admin-only endpoints (reload-guests, etc.)
```

### New Source Modules

```text
src/wedding_photos/
  database.py          # async SQLAlchemy engine + session factory + create_all lifespan
  db_models.py         # ORM model: Upload (id, guest_name, guest_surname, table_id,
                       #   s3_key, original_filename, mime_type, created_at)
  storage.py           # MinIO client wrapper (upload_file, presigned_url, delete)
  repositories.py      # UploadRepository (create, list_all); GuestRepository (validate)
  routes/
    api.py             # /api/guests/validate, /api/uploads (POST + GET)
```

### Data Flow — Upload

```text
Guest fills dialog → POST /api/guests/validate → 200/422
→ (if 200) file picker shown → POST /api/uploads (multipart)
  → middleware: token check
  → route: re-validate guest | detect MIME | enforce size
  → storage.py: stream file to MinIO under uploads/{uuid}.{ext}
  → repositories.py: insert Upload row in DB
  → return Upload JSON
→ gallery grid refreshed via GET /api/uploads
```

---

## Task List

### Infrastructure and Setup

- [ ] **T-01** — Add `db` (PostgreSQL) and `minio` services to `compose.yaml`; add healthchecks and `depends_on` for the app service.
- [ ] **T-02** — Create `.env.example` with all new environment variables documented.
- [ ] **T-03** — Add new Python dependencies to `pyproject.toml`: `sqlalchemy[asyncio]`, `asyncpg`, `minio`, `python-magic`.

### Backend — Data Layer

- [ ] **T-04** — Create `database.py`: async SQLAlchemy engine (`create_async_engine`), `AsyncSession` factory, `Base` declarative base, and a FastAPI `lifespan` function that calls `Base.metadata.create_all` on startup.
- [ ] **T-05** — Create `db_models.py`: `Upload` ORM model with fields `id` (UUID PK), `guest_name`, `guest_surname`, `table_id` (nullable int), `s3_key`, `original_filename`, `mime_type`, `created_at`.
- [ ] **T-06** — Create `storage.py`: thin MinIO client wrapper with `async upload_file(key, data, content_type) -> str` and `presigned_url(key) -> str`. Read config from env at import time.
- [ ] **T-07** — Create `repositories.py`:
  - `GuestRepository.validate(name, surname) -> bool` — reads from the in-memory cached guest list, case-insensitive match.
  - `GuestRepository.reload() -> int` — re-reads `guests.yaml` from disk, replaces the cache, returns the number of guests loaded.
  - `UploadRepository.create(session, ...) -> Upload` — inserts a row.
  - `UploadRepository.list_all(session) -> list[Upload]` — returns all rows ordered by `created_at DESC`.
- [ ] **T-08** — Create `guests.yaml` at project root with a sample structure `[{name: "Mario", surname: "Rossi"}, ...]`. The `GuestRepository` holds the list in a module-level variable and exposes a `reload()` method so the cache can be replaced without restarting.

### Backend — API Routes

- [ ] **T-09** — Create `routes/api.py` with:
  - `POST /api/guests/validate` — body `{name, surname}`, calls `GuestRepository.validate`, returns 200 `{valid: true}` or 422.
  - `POST /api/uploads` — multipart `name`, `surname`, `table_id?`, `file`; validates guest; detects MIME via `python-magic`; rejects non-image/video types; enforces 50 MB limit; streams to MinIO; inserts DB row; returns upload JSON.
  - `GET /api/uploads` — returns list of all upload records with presigned MinIO URLs.
  - `POST /api/admin/reload-guests` — requires `Authorization: Bearer <ADMIN_TOKEN>`; calls `GuestRepository.reload()`; returns `{loaded: N}`. Not covered by the guest-facing token middleware.
- [ ] **T-10** — Update `main.py`: integrate the new `lifespan` from `database.py`; include `api.py` router; inject `AsyncSession` via FastAPI dependency.

### Frontend

- [ ] **T-11** — Update `menu.html`: add tab bar ("I Tavoli" / "Le Foto") using Alpine.js `x-data` for active tab state; wrap existing table grid in the first tab panel; add gallery panel as the second tab.
- [ ] **T-12** — Build the gallery panel (inline in `menu.html` or a Jinja2 `{% include %}`): responsive CSS grid, populated on tab activation via `fetch('/api/uploads?t=...')`, each cell shows thumbnail + guest first name, tap → full-screen lightbox.
- [ ] **T-13** — Build the upload dialog (Alpine.js component): step 1 — name/surname form + `/api/guests/validate` call; step 2 (on success) — file picker + progress bar + `/api/uploads` POST; step 3 — success state + gallery refresh trigger.

### Validation & Polish

- [ ] **T-14** — Test end-to-end locally with `docker compose up`: guest list validation, file upload to MinIO, DB persistence, gallery display.
- [ ] **T-15** — Verify all new endpoints reject requests without the secret token.
- [ ] **T-16** — Test on a 375 px viewport: tab bar, dialog flow, gallery scroll, lightbox.
