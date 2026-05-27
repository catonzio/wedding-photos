"""
HTML page routes — menu and table detail.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from wedding_photos.config import TEMPLATES_DIR
from wedding_photos.models import load_tables

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _token_from(request: Request) -> str:
    from wedding_photos.config import SECRET_TOKEN

    return request.query_params.get("t", SECRET_TOKEN)


def _base_context(
    request: Request, current_table_id: int | None = None
) -> dict[str, Any]:
    return {
        "request": request,
        "token": _token_from(request),
        "all_tables": load_tables(),
        "current_table_id": current_table_id,
    }


@router.get("/", response_class=HTMLResponse)
async def root(request: Request) -> RedirectResponse:
    token = _token_from(request)
    return RedirectResponse(url=f"/menu?t={token}", status_code=302)


@router.get("/menu", response_class=HTMLResponse, name="menu_page")
async def menu_page(request: Request) -> HTMLResponse:
    ctx = _base_context(request)
    ctx["tables"] = ctx["all_tables"]
    return templates.TemplateResponse(request=request, name="menu.html", context=ctx)


@router.get("/table/{table_id}", response_class=HTMLResponse, name="table_page")
async def table_page(request: Request, table_id: int) -> HTMLResponse:
    tables = load_tables()
    table = next((t for t in tables if t.id == table_id), None)
    if table is None:
        return HTMLResponse("Tavolo non trovato", status_code=404)
    ctx = _base_context(request, current_table_id=table_id)
    ctx["table"] = table
    return templates.TemplateResponse(request=request, name="table.html", context=ctx)
