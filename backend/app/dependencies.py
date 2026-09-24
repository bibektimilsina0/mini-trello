import uuid

from fastapi import Cookie, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.cookies import set_auth_cookies
from app.database import get_db
from app.models.user import User
from app.security import create_access_token, decode_access_token
from app.services import auth_service


async def get_current_user(
    response: Response,
    access_token: str | None = Cookie(default=None),
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Auth dependency — the FastAPI equivalent of Express authMiddleware.

    1. Try the access_token cookie (fast path).
    2. If missing/expired, fall back to refresh_token: rotate it, mint a new
       access token, silently re-set both cookies on the response — the
       request just succeeds, no frontend refresh call needed.
    3. If refresh token is also missing/invalid/expired, raise 401.
    """
    user = await _try_access_token(access_token, db)
    if user:
        return user

    if not refresh_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    try:
        user, new_refresh_token = await auth_service.rotate_refresh_token(db, refresh_token)
    except HTTPException:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired, please log in again")

    new_access_token = create_access_token(str(user.id))
    set_auth_cookies(response, new_access_token, new_refresh_token)
    return user


async def _try_access_token(access_token: str | None, db: AsyncSession) -> User | None:
    if not access_token:
        return None

    user_id = decode_access_token(access_token)
    if not user_id:
        return None  # expired or invalid signature — fall through to refresh

    return await db.get(User, uuid.UUID(user_id))