import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_health_returns_ok() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.anyio
async def test_hello_returns_message() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from FastAPI"}


@pytest.mark.anyio
async def test_login_rejects_invalid_credentials() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": "user", "password": "wrong-password"},
        )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}


@pytest.mark.anyio
async def test_login_accepts_valid_credentials_and_sets_cookie() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )
    assert response.status_code == 200
    assert response.json() == {"authenticated": True}
    assert "pm_session=1" in response.headers.get("set-cookie", "")
