"""API for platform access credentials (username/password + encrypted session)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.platform_credential import CredentialStatus, PlatformCredential
from app.models.source import Platform
from app.services.credential_crypto import decrypt_secret, encrypt_secret
from app.services.platform_sessions import (
    SESSION_PLATFORMS,
    cookies_from_paste,
    has_auth_cookies,
    storage_state_from_cookies,
)

router = APIRouter()

AUTH_PLATFORMS: list[Platform] = list(Platform)


class CredentialCreate(BaseModel):
    platform: Platform
    username: str = Field(..., min_length=1, max_length=512)
    password: str = Field(..., min_length=1, max_length=512)


class CredentialUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=512)
    password: str | None = Field(default=None, min_length=1, max_length=512)


class CredentialResponse(BaseModel):
    id: uuid.UUID
    platform: str
    username: str
    has_password: bool = True
    has_session: bool = False
    status: str
    last_error: str | None = None
    last_verified_at: datetime | None = None
    updated_at: datetime | None = None


class CredentialListResponse(BaseModel):
    items: list[CredentialResponse]


class FacebookSessionImport(BaseModel):
    """Browser cookies from a real Facebook login (Application → Cookies)."""

    c_user: str | None = Field(default=None, max_length=128)
    xs: str | None = Field(default=None, max_length=2048)
    cookies: str | None = Field(default=None, min_length=8)
    username: str | None = Field(default=None, max_length=512)


class PlatformSessionImport(BaseModel):
    """Paste Netscape cookies, Cookie header, or JSON cookie array from DevTools."""

    cookies: str = Field(..., min_length=8)
    username: str | None = Field(default=None, max_length=512)


class ConnectRequest(BaseModel):
    """Optional cookie attach for Facebook Connect (preferred over Playwright)."""

    c_user: str | None = Field(default=None, max_length=128)
    xs: str | None = Field(default=None, max_length=512)
    username: str | None = Field(default=None, max_length=512)


def _to_response(row: PlatformCredential) -> CredentialResponse:
    platform = row.platform.value if hasattr(row.platform, "value") else str(row.platform)
    has_auth = has_auth_cookies(platform, row.session_json if isinstance(row.session_json, dict) else None)
    raw_status = row.status.value if hasattr(row.status, "value") else str(row.status)
    if has_auth:
        status_out = "connected"
    elif raw_status == "connected":
        status_out = "error"
    else:
        status_out = raw_status
    return CredentialResponse(
        id=row.id,
        platform=platform,
        username=row.username,
        has_password=bool(row.password_encrypted),
        has_session=has_auth,
        status=status_out,
        last_error=(
            row.last_error
            if has_auth or raw_status != "connected"
            else "Session missing auth cookies — paste a fresh browser session."
        ),
        last_verified_at=row.last_verified_at,
        updated_at=row.updated_at,
    )


def _storage_state_from_fb_cookies(c_user: str, xs: str) -> dict:
    # Playwright treats expires=-1 oddly for some flows; use a far-future expiry.
    far = 4102444800.0  # 2100-01-01
    return storage_state_from_cookies(
        [
            {
                "name": "c_user",
                "value": c_user.strip(),
                "domain": ".facebook.com",
                "path": "/",
                "expires": far,
                "httpOnly": False,
                "secure": True,
                "sameSite": "None",
            },
            {
                "name": "xs",
                "value": xs.strip(),
                "domain": ".facebook.com",
                "path": "/",
                "expires": far,
                "httpOnly": True,
                "secure": True,
                "sameSite": "None",
            },
        ]
    )


async def _upsert_session(
    db: AsyncSession,
    *,
    platform: Platform,
    username: str,
    session_json: dict,
) -> PlatformCredential:
    rows = (
        await db.scalars(
            select(PlatformCredential).where(PlatformCredential.platform == platform)
        )
    ).all()
    row: PlatformCredential | None = None
    for candidate in rows:
        if candidate.username == username:
            row = candidate
            break
    if row is None and len(rows) == 1:
        row = rows[0]
    if row is None:
        row = PlatformCredential(
            platform=platform,
            username=username,
            password_encrypted=encrypt_secret(f"session-import:{platform.value}"),
            status=CredentialStatus.saved,
        )
        db.add(row)
        await db.flush()

    row.username = username
    row.session_json = session_json
    row.status = CredentialStatus.connected
    row.last_error = None
    row.last_verified_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(row)
    return row


@router.get("", response_model=CredentialListResponse)
async def list_credentials(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.scalars(
            select(PlatformCredential).order_by(
                PlatformCredential.platform.asc(),
                PlatformCredential.username.asc(),
            )
        )
    ).all()
    return CredentialListResponse(items=[_to_response(r) for r in rows])


@router.post("", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(payload: CredentialCreate, db: AsyncSession = Depends(get_db)):
    if payload.platform not in AUTH_PLATFORMS:
        raise HTTPException(status_code=400, detail="Platform does not use stored credentials.")

    username = payload.username.strip()
    existing = await db.scalar(
        select(PlatformCredential).where(
            PlatformCredential.platform == payload.platform,
            PlatformCredential.username == username,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="That platform + username already exists.")

    row = PlatformCredential(
        platform=payload.platform,
        username=username,
        password_encrypted=encrypt_secret(payload.password),
        status=CredentialStatus.saved,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return _to_response(row)


# Static paths MUST be declared before /{credential_id} or they 404 behind stale workers.
@router.post("/facebook/session", response_model=CredentialResponse)
@router.post("/session/facebook", response_model=CredentialResponse)
async def import_facebook_session(payload: FacebookSessionImport, db: AsyncSession = Depends(get_db)):
    """Upsert Facebook session from full cookie paste or c_user + xs."""
    if payload.cookies and payload.cookies.strip():
        return await _import_named_platform_session(
            Platform.facebook,
            PlatformSessionImport(cookies=payload.cookies, username=payload.username),
            db,
        )

    c_user = (payload.c_user or "").strip()
    xs = (payload.xs or "").strip()
    if not c_user or not xs:
        raise HTTPException(
            status_code=400,
            detail="Paste full facebook.com cookies, or both c_user and xs.",
        )

    username = (payload.username or "").strip() or f"fb:{c_user}"
    row = await _upsert_session(
        db,
        platform=Platform.facebook,
        username=username,
        session_json=_storage_state_from_fb_cookies(c_user, xs),
    )
    return _to_response(row)


async def _import_named_platform_session(
    platform: Platform,
    payload: PlatformSessionImport,
    db: AsyncSession,
) -> CredentialResponse:
    if platform not in SESSION_PLATFORMS:
        raise HTTPException(status_code=400, detail="Session import is not enabled for this platform.")
    cookies = cookies_from_paste(payload.cookies, platform)
    if not cookies:
        raise HTTPException(status_code=400, detail="No cookies found in paste.")
    state = storage_state_from_cookies(cookies)
    if not has_auth_cookies(platform, state):
        needed = {
            Platform.facebook: "c_user and xs",
            Platform.youtube: "SID / __Secure-1PSID / LOGIN_INFO",
            Platform.instagram: "sessionid",
            Platform.tiktok: "sessionid or sid_tt",
            Platform.x: "auth_token",
        }.get(platform, "login cookies")
        raise HTTPException(
            status_code=400,
            detail=f"Paste does not include required auth cookies ({needed}).",
        )
    username = (payload.username or "").strip() or f"{platform.value}-session"
    row = await _upsert_session(db, platform=platform, username=username, session_json=state)
    return _to_response(row)


@router.post("/youtube/session", response_model=CredentialResponse)
async def import_youtube_session(payload: PlatformSessionImport, db: AsyncSession = Depends(get_db)):
    return await _import_named_platform_session(Platform.youtube, payload, db)


@router.post("/instagram/session", response_model=CredentialResponse)
async def import_instagram_session(payload: PlatformSessionImport, db: AsyncSession = Depends(get_db)):
    return await _import_named_platform_session(Platform.instagram, payload, db)


@router.post("/tiktok/session", response_model=CredentialResponse)
async def import_tiktok_session(payload: PlatformSessionImport, db: AsyncSession = Depends(get_db)):
    return await _import_named_platform_session(Platform.tiktok, payload, db)


@router.post("/x/session", response_model=CredentialResponse)
async def import_x_session(payload: PlatformSessionImport, db: AsyncSession = Depends(get_db)):
    return await _import_named_platform_session(Platform.x, payload, db)


@router.patch("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: uuid.UUID,
    payload: CredentialUpdate,
    db: AsyncSession = Depends(get_db),
):
    row = await db.get(PlatformCredential, credential_id)
    if not row:
        raise HTTPException(status_code=404, detail="Credential not found.")

    if payload.username is not None:
        row.username = payload.username.strip()
    if payload.password is not None:
        row.password_encrypted = encrypt_secret(payload.password)
        row.session_json = None
        row.status = CredentialStatus.saved
        row.last_error = None
        row.last_verified_at = None

    await db.flush()
    await db.refresh(row)
    return _to_response(row)


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(credential_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    row = await db.get(PlatformCredential, credential_id)
    if not row:
        raise HTTPException(status_code=404, detail="Credential not found.")
    await db.delete(row)


@router.post("/{credential_id}/session", response_model=CredentialResponse)
async def import_credential_session(
    credential_id: uuid.UUID,
    payload: FacebookSessionImport,
    db: AsyncSession = Depends(get_db),
):
    row = await db.get(PlatformCredential, credential_id)
    if not row:
        raise HTTPException(status_code=404, detail="Credential not found.")
    if row.platform != Platform.facebook:
        raise HTTPException(
            status_code=400,
            detail="Use /credentials/youtube|instagram|tiktok|x/session for this platform.",
        )

    c_user = payload.c_user.strip()
    row.session_json = _storage_state_from_fb_cookies(c_user, payload.xs)
    row.username = (payload.username or "").strip() or f"fb:{c_user}"
    row.status = CredentialStatus.connected
    row.last_error = None
    row.last_verified_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(row)
    return _to_response(row)


@router.post("/{credential_id}/connect", response_model=CredentialResponse)
async def connect_credential(
    credential_id: uuid.UUID,
    payload: ConnectRequest = Body(default_factory=ConnectRequest),
    interactive: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """Connect a credential.

    Preferred for Facebook: send JSON body ``{"c_user": "...", "xs": "..."}``
    (paste from browser cookies). Skips Playwright entirely.

    Without cookie body: attempts Playwright login (usually blocked by Facebook).
    """
    row = await db.get(PlatformCredential, credential_id)
    if not row:
        raise HTTPException(status_code=404, detail="Credential not found.")

    if payload and (payload.c_user or "").strip() and (payload.xs or "").strip():
        if row.platform != Platform.facebook:
            raise HTTPException(status_code=400, detail="Cookie session attach is for Facebook only.")
        c_user = payload.c_user.strip()
        row.session_json = _storage_state_from_fb_cookies(c_user, payload.xs.strip())
        if payload.username:
            row.username = payload.username.strip()
        elif not str(row.username).startswith("fb:"):
            row.username = f"fb:{c_user}"
        row.status = CredentialStatus.connected
        row.last_error = None
        row.last_verified_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(row)
        return _to_response(row)

    try:
        password = decrypt_secret(row.password_encrypted)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    platform = row.platform.value if hasattr(row.platform, "value") else str(row.platform)

    def _login() -> dict:
        from app.services.platform_login import login_and_capture_session

        return login_and_capture_session(
            platform, row.username, password, interactive=interactive
        )

    loop = asyncio.get_running_loop()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            session = await loop.run_in_executor(pool, _login)
        row.session_json = session
        row.status = CredentialStatus.connected
        row.last_error = None
        row.last_verified_at = datetime.now(timezone.utc)
    except Exception as exc:
        row.status = CredentialStatus.error
        row.last_error = str(exc)[:1000]
        row.session_json = None
        await db.flush()
        raise HTTPException(status_code=422, detail=f"Login failed: {exc}") from exc

    await db.flush()
    await db.refresh(row)
    return _to_response(row)
