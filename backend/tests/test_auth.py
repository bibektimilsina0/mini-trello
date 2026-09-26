import re

import pytest
from httpx import AsyncClient


async def signup_user(client: AsyncClient, email="test@example.com", password="password123"):
    return await client.post(
        "/api/auth/signup", json={"email": email, "name": "Test User", "password": password}
    )


@pytest.mark.asyncio
async def test_signup_creates_user(client: AsyncClient):
    response = await signup_user(client)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "test@example.com"
    assert body["is_email_verified"] is False
    # Password must never leak into any response.
    assert "password" not in body
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_signup_duplicate_email_rejected(client: AsyncClient):
    await signup_user(client)
    response = await signup_user(client)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_blocked_before_email_verified(client: AsyncClient):
    await signup_user(client)
    response = await client.post(
        "/api/auth/login", json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(client: AsyncClient):
    await signup_user(client)
    response = await client.post(
        "/api/auth/login", json={"email": "test@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_full_signup_verify_login_flow(client: AsyncClient, capsys):
    await signup_user(client)

    # The verification token was printed to stdout by the email stub —
    # capsys captures it here instead of us needing a real mail provider.
    captured = capsys.readouterr()
    match = re.search(r"token=([a-f0-9]+)", captured.out)
    assert match, "verification token not found in stub email output"
    token = match.group(1)

    verify_response = await client.get("/api/auth/verify-email", params={"token": token})
    assert verify_response.status_code == 200

    login_response = await client.post(
        "/api/auth/login", json={"email": "test@example.com", "password": "password123"}
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["requires_2fa"] is False
    assert body["user"]["email"] == "test@example.com"

    # Cookies should be set on a successful login.
    assert "access_token" in login_response.cookies
    assert "refresh_token" in login_response.cookies


@pytest.mark.asyncio
async def test_verify_email_rejects_invalid_token(client: AsyncClient):
    response = await client.get("/api/auth/verify-email", params={"token": "not-a-real-token"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_me_requires_authentication(client: AsyncClient):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401