from datetime import timedelta

from fastapi import Response

from app.config import settings

ACCESS_COOKIE_KWARGS = dict(
    httponly=True,
    secure=settings.cookie_secure,
    samesite=settings.cookie_samesite,
)


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        "access_token",
        access_token,
        max_age=int(timedelta(minutes=settings.access_token_expire_minutes).total_seconds()),
        **ACCESS_COOKIE_KWARGS,
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        max_age=int(timedelta(days=settings.refresh_token_expire_days).total_seconds()),
        path="/",  # must be reachable on every route, since get_current_user auto-refreshes here
        **ACCESS_COOKIE_KWARGS,
    )