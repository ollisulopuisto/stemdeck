"""Serves the bundled CHANGELOG.md for the in-app What's New panel.

The changelog lives at the repository root in development and is copied
into backend/static/ by the make-portable scripts, mirroring how
static/version.json reaches packaged builds. A missing file yields 404 and
the client stays silent: the What's New panel is additive, never a crash.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.core.config import ROOT, STATIC_DIR

router = APIRouter()


def _changelog_path():
    for candidate in (STATIC_DIR / "CHANGELOG.md", ROOT / "CHANGELOG.md"):
        if candidate.is_file():
            return candidate
    return None


@router.get("/whats-new")
def get_whats_new() -> PlainTextResponse:
    path = _changelog_path()
    if path is None:
        raise HTTPException(status_code=404, detail="changelog not bundled")
    return PlainTextResponse(path.read_text(encoding="utf-8"))
