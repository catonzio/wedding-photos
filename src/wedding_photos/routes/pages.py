"""
HTML page routes — menu and table detail.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from wedding_photos.database import get_session
from wedding_photos.repositories import TableRepository
from wedding_photos.templates import templates

router = APIRouter()


def _token_from(request: Request) -> str:
    from wedding_photos.config import SECRET_TOKEN

    return request.query_params.get("t", SECRET_TOKEN)


def _base_context(
    request: Request, all_tables: list, current_table_id: int | None = None
) -> dict[str, Any]:
    return {
        "request": request,
        "token": _token_from(request),
        "all_tables": all_tables,
        "current_table_id": current_table_id,
    }


@router.get("/", response_class=HTMLResponse)
async def root(request: Request) -> RedirectResponse:
    token = _token_from(request)
    return RedirectResponse(url=f"/menu?t={token}", status_code=302)


@router.get("/menu", response_class=HTMLResponse, name="menu_page")
async def menu_page(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    tables = await TableRepository.list_all(session)
    ctx = _base_context(request, tables)
    ctx["tables"] = tables
    return templates.TemplateResponse(
        request=request, name="menu/menu.html", context=ctx
    )


@router.get("/table/{table_id}", response_class=HTMLResponse, name="table_page")
async def table_page(
    request: Request,
    table_id: int,
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    tables = await TableRepository.list_all(session)
    table = await TableRepository.get_by_id(session, table_id)
    if table is None:
        return HTMLResponse("Tavolo non trovato", status_code=404)
    ctx = _base_context(request, tables, current_table_id=table_id)
    ctx["table"] = table
    return templates.TemplateResponse(request=request, name="table.html", context=ctx)
