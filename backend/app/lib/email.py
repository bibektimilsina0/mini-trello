"""Stub email sender. Logs to console instead of sending — same approach as
the original repo, so the demo works with zero mail provider configured.

One place to swap in a real provider later (Resend, SES, etc.) plus, when you
add the queue, one place to enqueue instead of calling directly."""

from app.config import settings


def send_verification_email(to: str, name: str, raw_token: str) -> None:
    verification_url = f"{settings.frontend_url}/verify-email?token={raw_token}"
    print(
        "[INFO] Verification email (not sent — no mail provider configured) "
        f"{{ to: '{to}', name: '{name}', verificationUrl: '{verification_url}' }}"
    )


def send_2fa_code_email(to: str, name: str, code: str) -> None:
    print(
        f"\nTo: {to}\n\n"
        f"Hello {name},\n\n"
        f"Your verification code is:\n\n"
        f"{code}\n\n"
        f"This code expires in 5 minutes.\n"
    )
