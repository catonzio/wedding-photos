# Wedding Photos — Architecture & Design Decisions

> Author: Danilo Catone  
> Date: 2026-05-27  
> Status: Approved — ready for implementation

---

## Overview

Mobile-first web application to display wedding photos organized by table. Each table has a physical QR code that guests scan to reach the table's page with a photo/video carousel.

The application is intentionally simple: it is used for a single day, deployed as a single container, and requires no database or authentication system.

---

## Requirements

### Functional

- Each table has a dedicated page with: title, description, and a photo/video carousel
- A navigation menu lists all tables with their cover photo
- Access is gated by a secret token embedded in all QR codes
- Requests without the token return an empty/neutral page (no error hint)
- QR codes are generated as printable PNG files before the event

### Non-Functional

- **Mobile-first**: designed for smartphone screens, touch-friendly
- **No build step**: all frontend dependencies loaded via CDN
- **Single container**: deployable with `docker compose up -d`
- **No database**: table metadata stored in a `tables.yaml` file
- **~10–20 tables**, photos pre-loaded before the day

### Out of Scope (for now)

- Guest photo upload (considered for a future iteration — see [Guest Upload](#guest-upload-future))
- Admin panel
- Authentication / user accounts

---

## Tech Stack

| Layer | Choice | Rationale |
| --- | --- | --- |
| Backend | **FastAPI** | Async, lightweight, serves both API and HTML templates |
| Templates | **Jinja2** | Built into FastAPI, zero extra config |
| CSS | **Tailwind CSS** (CDN) | Utility-first, mobile-first, no build step |
| Interactivity | **Alpine.js** (CDN) | Lightweight reactive layer for menu toggling, transitions |
| Carousel | **Swiper.js** (CDN) | Best-in-class mobile carousel, native touch/swipe support |
| Container | **Docker + Docker Compose** | Single-command deploy, portable |
| Reverse proxy | **Nginx** (existing on server) | TLS termination, static file caching |
| Config | **YAML file** | Human-editable, no schema overhead |

### Why not React / Vue / Svelte?

For 4–5 screens with simple interactivity, a full SPA framework adds:

- A build step (Vite/Webpack) that needs to be maintained
- A separate dev server during development
- Bundle optimization concerns
- More complexity for zero visible graphical improvement

CSS transitions + Alpine.js cover all the animation needs. The only gain from an SPA would be client-side routing, which is not needed here.

---

## Project Structure

```text
wedding-photos/
├── src/wedding_photos/
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Settings (token, paths, YAML loading)
│   ├── middleware.py            # Token validation middleware
│   ├── routes/
│   │   ├── pages.py             # HTML page routes (table, menu)
│   │   └── static_media.py      # Media file serving
│   ├── templates/
│   │   ├── base.html            # Base layout (nav, head, Tailwind/Alpine/Swiper CDN)
│   │   ├── table.html           # Table detail page with carousel
│   │   ├── menu.html            # Table list / navigation
│   │   └── denied.html          # Shown when token is missing (neutral, no error)
│   └── static/
│       └── media/
│           ├── table_1/         # Photos and videos for table 1
│           ├── table_2/
│           └── ...
├── tables.yaml                  # Table metadata (see format below)
├── scripts/
│   └── generate_qrcodes.py      # One-shot script to generate QR code PNGs
├── docs/
│   └── architecture.md          # This file
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── pyproject.toml
```

---

## Table Configuration (`tables.yaml`)

```yaml
tables:
  - id: 1
    name: "Tavolo degli Sposi"
    description: "Il tavolo principale, al centro di tutto."
    cover: "table_1/cover.jpg"
    media:
      - "table_1/foto1.jpg"
      - "table_1/foto2.jpg"
      - "table_1/video1.mp4"

  - id: 2
    name: "Tavolo dei Testimoni"
    description: "I migliori amici degli sposi."
    cover: "table_2/cover.jpg"
    media:
      - "table_2/foto1.jpg"
```

FastAPI loads this file at startup. To add photos during the day: copy files to the table folder and restart the container (`docker compose restart app` — takes ~5 seconds).

---

## Token / Access Control

### Strategy: Single global token

All QR codes share the same secret token embedded in the URL:

```text
https://tuodominio.com/table/3?t=<TOKEN>
```

- Token is a cryptographically random UUID generated once and stored in `.env`
- A FastAPI middleware checks for `?t=` on **every** request (HTML pages and media)
- If the token is **missing or incorrect** → serve `denied.html` (blank/neutral page, HTTP 200 to avoid revealing the gate)
- All internal links (menu → table → back) automatically append `?t=<token>` to every href

### Token generation

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Store the output in `.env`:

```env
SECRET_TOKEN=your-generated-token-here
MEDIA_PATH=/app/static/media
```

### Security considerations

- The token is not a substitute for authentication; it is an obscurity gate suitable for a one-day social event
- HTTPS (via Nginx + Let's Encrypt) must be enabled to prevent token interception in transit
- The QR code PNG files should be kept private (do not publish them online)

---

## URL Structure

| Path | Description |
| --- | --- |
| `/` | Redirects to `/menu?t=<token>` |
| `/menu?t=<token>` | Table list with cover photos |
| `/table/{id}?t=<token>` | Table detail with carousel |
| `/static/media/...` | Media files (also token-gated) |
| `*` (no token) | Returns `denied.html` |

---

## QR Code Generation

`scripts/generate_qrcodes.py` is a one-shot script that:

1. Reads `tables.yaml` and the `SECRET_TOKEN` from `.env`
2. Generates one QR code PNG per table pointing to `/table/{id}?t=<token>`
3. Saves them to `qrcodes/table_{id}.png`

Dependencies: `qrcode[pil]`

Each PNG is designed to be printed at ≥ 5×5 cm for reliable scanning. The script optionally adds the table name as a label below the QR code.

---

## Deployment

### Docker

```dockerfile
# Dockerfile (sketch)
FROM python:3.14-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["uvicorn", "wedding_photos.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports:
      - "127.0.0.1:8000:8000"   # only exposed to localhost; Nginx proxies
    volumes:
      - ./static/media:/app/src/wedding_photos/static/media  # media outside image
      - ./tables.yaml:/app/tables.yaml
    env_file: .env
    restart: unless-stopped
```

---

## Guest Upload (Future)

If guest upload is desired, the addition is localized:

1. Add a hidden upload button on the table page (revealed after a long-press or easter egg)
2. `POST /table/{id}/upload?t=<token>` endpoint validates token + file type (images/videos only, strict MIME + extension check)
3. Uploaded files saved to `static/media/table_{id}/uploads/`
4. Decide on **moderation**: files appear immediately (simplest) or require a manual refresh of `tables.yaml`

**Key security concerns for upload:**

- Validate file type server-side (MIME type + magic bytes, not just extension)
- Set a file size limit (e.g. 50 MB per file)
- Never execute uploaded files; store outside the web root or serve via a dedicated route
- Rate-limit the upload endpoint per IP

---

## Implementation Order (suggested)

1. **Project scaffolding** — FastAPI app, Jinja2, config loading from YAML + env
2. **Token middleware** — intercept all requests, check `?t=`, serve `denied.html`
3. **Routes & templates** — `menu.html` and `table.html` with placeholder data
4. **Media serving** — static file route, also token-gated
5. **Carousel** — integrate Swiper.js in `table.html`
6. **QR code script** — `generate_qrcodes.py`
7. **Docker + Compose** — containerize and test locally
8. **Design polish** — animations, transitions, mobile UX refinement
9. *(Optional)* **Guest upload** — form + endpoint + moderation decision
