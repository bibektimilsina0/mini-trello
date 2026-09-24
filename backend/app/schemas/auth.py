import uuid

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str
    is_email_verified: bool
    is_2fa_enabled: bool

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """If the user has 2FA enabled, `requires_2fa` is True and no cookies are
    set yet — the frontend must call /verify-2fa next."""
    user: UserOut | None = None
    requires_2fa: bool = False


class VerifyEmailRequest(BaseModel):
    token: str


class Verify2FARequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class Resend2FARequest(BaseModel):
    email: EmailStr


class MessageResponse(BaseModel):
    message: str

class Disable2FARequest(BaseModel):
    password: str  # confirm identity before turning 2FA off