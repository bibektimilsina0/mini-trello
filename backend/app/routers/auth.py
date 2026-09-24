from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.cookies import set_auth_cookies
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    Disable2FARequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    Resend2FARequest,
    SignupRequest,
    UserOut,
    Verify2FARequest,
    VerifyEmailRequest,
)
from app.security import create_access_token
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


async def _log_user_in(db: AsyncSession, user: User, response: Response) -> UserOut:
    access_token = create_access_token(str(user.id))
    refresh_token = await auth_service.issue_refresh_token(db, user.id)
    set_auth_cookies(response, access_token, refresh_token)
    return UserOut.model_validate(user)


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.signup(db, body.email, body.name, body.password)
    return UserOut.model_validate(user)


@router.get("/verify-email", response_model=MessageResponse)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    await auth_service.verify_email(db, token)
    return MessageResponse(message="Email verified — you can now log in")


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate(db, body.email, body.password)

    if user.is_2fa_enabled:
        await auth_service.start_2fa_challenge(db, user)
        return LoginResponse(requires_2fa=True)

    user_out = await _log_user_in(db, user, response)
    return LoginResponse(user=user_out, requires_2fa=False)


@router.post("/verify-2fa", response_model=LoginResponse)
async def verify_2fa(body: Verify2FARequest, response: Response, db: AsyncSession = Depends(get_db)):
    user = await auth_service.verify_2fa_code(db, body.email, body.code)
    user_out = await _log_user_in(db, user, response)
    return LoginResponse(user=user_out, requires_2fa=False)


@router.post("/resend-2fa", response_model=MessageResponse)
async def resend_2fa(body: Resend2FARequest, db: AsyncSession = Depends(get_db)):
    await auth_service.resend_2fa_code(db, body.email)
    return MessageResponse(message="If an account with 2FA enabled exists, a new code was sent")


# Optional manual refresh — no longer required for normal requests, since
# get_current_user now refreshes automatically. Kept for an explicit
# "keep me logged in" ping on app load if you want one.
@router.post("/refresh", response_model=MessageResponse)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No refresh token")

    user, new_refresh_token = await auth_service.rotate_refresh_token(db, refresh_token)
    new_access_token = create_access_token(str(user.id))
    set_auth_cookies(response, new_access_token, new_refresh_token)
    return MessageResponse(message="Token refreshed")


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if refresh_token:
        await auth_service.revoke_refresh_token(db, refresh_token)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/")
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.post("/2fa/enable", response_model=MessageResponse)
async def enable_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await auth_service.enable_2fa_for_user(db, current_user)
    return MessageResponse(message="Two-factor authentication enabled")


@router.post("/2fa/disable", response_model=MessageResponse)
async def disable_2fa(
    body: Disable2FARequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await auth_service.disable_2fa_for_user(db, current_user, body.password)
    return MessageResponse(message="Two-factor authentication disabled")