from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    access_token_secret: str
    refresh_token_secret: str
    email_token_secret: str  # used for verification token + 2FA OTP hashing context

    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    frontend_url: str = "http://localhost:5173"
    cors_origin: str = "http://localhost:5173"

    cookie_secure: bool = False  # set True in production (https)
    cookie_samesite: str = "lax"

    class Config:
        env_file = ".env"


settings = Settings()
