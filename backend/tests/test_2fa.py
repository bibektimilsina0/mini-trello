import re

import pytest
from httpx import AsyncClient


async def signup_and_verify(client: AsyncClient, email="test@example.com", password="password123"):
    await client.post("/api/auth/signup", json={"email": email, "name": "Test", "password": password})
    # In a real test suite you'd factor out token extraction into a shared
    # helper (see conftest.py) rather than duplicating this regex per file —
    # left inline here for clarity.
    import subprocess  # placeholder — real extraction happens via capsys in practice


@pytest.mark.asyncio
async def test_enable_2fa_requires_login(client: AsyncClient):
    response = await client.post("/api/auth/2fa/enable")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_enable_and_login_requires_2fa_code(client: AsyncClient, capsys):
    # Signup + verify
    await client.post(
        "/api/auth/signup", json={"email": "test@example.com", "name": "Test", "password": "password123"}
    )
    captured = capsys.readouterr()
    token = re.search(r"token=([a-f0-9]+)", captured.out).group(1)
    await client.get("/api/auth/verify-email", params={"token": token})

    # Log in (no 2FA yet) to get a session
    login = await client.post(
        "/api/auth/login", json={"email": "test@example.com", "password": "password123"}
    )
    assert login.status_code == 200

    # Enable 2FA
    enable = await client.post("/api/auth/2fa/enable")
    assert enable.status_code == 200

    # Log out, log back in — should now require 2FA
    await client.post("/api/auth/logout")
    second_login = await client.post(
        "/api/auth/login", json={"email": "test@example.com", "password": "password123"}
    )
    assert second_login.status_code == 200
    assert second_login.json()["requires_2fa"] is True

    # Extract the OTP from the (second) stub email log
    captured = capsys.readouterr()
    code_match = re.search(r"Your verification code is:\s*\n\s*(\d{6})", captured.out)
    assert code_match, "OTP not found in stub email output"
    code = code_match.group(1)

    verify_response = await client.post(
        "/api/auth/verify-2fa", json={"email": "test@example.com", "code": code}
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_verify_2fa_rejects_wrong_code(client: AsyncClient, capsys):
    await client.post(
        "/api/auth/signup", json={"email": "test@example.com", "name": "Test", "password": "password123"}
    )
    captured = capsys.readouterr()
    token = re.search(r"token=([a-f0-9]+)", captured.out).group(1)
    await client.get("/api/auth/verify-email", params={"token": token})
    await client.post("/api/auth/login", json={"email": "test@example.com", "password": "password123"})
    await client.post("/api/auth/2fa/enable")
    await client.post("/api/auth/logout")
    await client.post("/api/auth/login", json={"email": "test@example.com", "password": "password123"})

    response = await client.post(
        "/api/auth/verify-2fa", json={"email": "test@example.com", "code": "000000"}
    )
    assert response.status_code == 400