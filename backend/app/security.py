import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# --- Passwords: bcrypt (slow on purpose, defends against offline guessing) ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# --- Random tokens (refresh tokens, email verification tokens): SHA-256 ---
# These are already high-entropy random values, not user-guessable passwords,
# so a plain fast digest is enough — bcrypt's slowness buys nothing here and
# would make refresh-token lookups on every request expensive.
def generate_raw_token() -> str:
    return secrets.token_hex(32)  # 256 bits of randomness


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


# --- 2FA OTP: 6-digit numeric code, stored as SHA-256 hash like other tokens ---
def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


# --- JWT access tokens (short-lived, stateless) ---
def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": user_id, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.access_token_secret, algorithm="HS256")


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.access_token_secret, algorithms=["HS256"])
        if payload.get("type") != "access":
            return None
        return payload.get("sub")
    except JWTError:
        return None
