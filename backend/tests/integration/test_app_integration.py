import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_root_serves_static_html_and_page_can_call_api_contract() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        page = await client.get("/")
        hello = await client.get("/api/hello")

    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]
    assert "Kanban Studio" in page.text
    assert "/_next/static/" in page.text

    assert hello.status_code == 200
    assert hello.json() == {"message": "Hello from FastAPI"}


@pytest.mark.anyio
async def test_login_session_logout_flow() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        before = await client.get("/api/auth/session")
        login = await client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )
        during = await client.get("/api/auth/session")
        logout = await client.post("/api/auth/logout")
        after = await client.get("/api/auth/session")

    assert before.status_code == 200
    assert before.json() == {"authenticated": False}

    assert login.status_code == 200
    assert login.json() == {"authenticated": True}

    assert during.status_code == 200
    assert during.json() == {"authenticated": True}

    assert logout.status_code == 200
    assert logout.json() == {"authenticated": False}

    assert after.status_code == 200
    assert after.json() == {"authenticated": False}
