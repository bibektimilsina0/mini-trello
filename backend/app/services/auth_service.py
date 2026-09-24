import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.lib.email import send_2fa_code_email, send_verification_email
from app.models.token import EmailVerificationToken, RefreshToken, TwoFactorCode
from app.models.user import User
from app.security import (
    generate_otp,
    generate_raw_token,
    hash_password,
    hash_token,
    verify_password,
)

EMAIL_TOKEN_EXPIRE_HOURS = 24
OTP_EXPIRE_MINUTES = 5
OTP_MAX_ATTEMPTS = 5
REFRESH_TOKEN_EXPIRE_DAYS = 7


# ---------------------------------------------------------------- signup ---
async def signup(db: AsyncSession, email: str, name: str, password: str) -> User:
    existing = await db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(email=email, name=name, hashed_password=hash_password(password))
    db.add(user)
    await db.flush()  # get user.id before commit, single transaction

    raw_token = generate_raw_token()
    verification = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=EMAIL_TOKEN_EXPIRE_HOURS),
    )
    db.add(verification)
    await db.commit()
    await db.refresh(user)

    send_verification_email(to=user.email, name=user.name, raw_token=raw_token)
    return user


# ------------------------------------------------------- email verification -
async def verify_email(db: AsyncSession, raw_token: str) -> None:
    token_hash = hash_token(raw_token)
    record = await db.scalar(
        select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
    )
    if not record or record.used or record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired verification token")

    record.used = True
    user = await db.get(User, record.user_id)
    user.is_email_verified = True
    await db.commit()


# ------------------------------------------------------------------ login ---
async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    user = await db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_email_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Please verify your email before logging in")
    return user


async def start_2fa_challenge(db: AsyncSession, user: User) -> None:
    """Invalidate any previous unused code, issue a fresh one."""
    await _invalidate_pending_otps(db, user.id)

    code = generate_otp()
    record = TwoFactorCode(
        user_id=user.id,
        code_hash=hash_token(code),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES),
    )
    db.add(record)
    await db.commit()

    send_2fa_code_email(to=user.email, name=user.name, code=code)


async def resend_2fa_code(db: AsyncSession, email: str) -> None:
    user = await db.scalar(select(User).where(User.email == email))
    if not user or not user.is_2fa_enabled:
        # Don't reveal whether the account exists or has 2FA — respond the same either way.
        return
    await start_2fa_challenge(db, user)


async def verify_2fa_code(db: AsyncSession, email: str, code: str) -> User:
    user = await db.scalar(select(User).where(User.email == email))
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid code")

    record = await db.scalar(
        select(TwoFactorCode)
        .where(TwoFactorCode.user_id == user.id, TwoFactorCode.used == False)  # noqa: E712
        .order_by(TwoFactorCode.expires_at.desc())
    )
    if not record or record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Code expired — request a new one")

    if record.attempts >= OTP_MAX_ATTEMPTS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts — request a new code")

    if hash_token(code) != record.code_hash:
        record.attempts += 1
        await db.commit()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect code")

    record.used = True
    await db.commit()
    return user

async def enable_2fa_for_user(db: AsyncSession, user: User) -> None:
    if user.is_2fa_enabled:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "2FA is already enabled")
    user.is_2fa_enabled = True
    await db.commit()


async def disable_2fa_for_user(db: AsyncSession, user: User, password: str) -> None:
    if not user.is_2fa_enabled:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "2FA is not enabled")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect password")

    user.is_2fa_enabled = False
    await db.commit()
    await _invalidate_pending_otps(db, user.id)
    await db.commit()
    
async def _invalidate_pending_otps(db: AsyncSession, user_id: uuid.UUID) -> None:
    pending = await db.scalars(
        select(TwoFactorCode).where(TwoFactorCode.user_id == user_id, TwoFactorCode.used == False)  # noqa: E712
    )
    for row in pending:
        row.used = True


# ------------------------------------------------------------ refresh flow -
async def issue_refresh_token(db: AsyncSession, user_id: uuid.UUID) -> str:
    raw_token = generate_raw_token()
    record = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    await db.commit()
    return raw_token


async def rotate_refresh_token(db: AsyncSession, raw_token: str) -> tuple[User, str]:
    """Validates the presented refresh token, revokes it, and issues a new one.
    A replayed (already-revoked) token is rejected outright."""
    token_hash = hash_token(raw_token)
    record = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))

    if not record or record.revoked or record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    record.revoked = True
    user = await db.get(User, record.user_id)
    new_raw_token = await issue_refresh_token(db, user.id)
    return user, new_raw_token


async def revoke_refresh_token(db: AsyncSession, raw_token: str) -> None:
    token_hash = hash_token(raw_token)
    record = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if record:
        record.revoked = True
        await db.commit()
