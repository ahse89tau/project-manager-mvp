import pytest
from httpx import ASGITransport, AsyncClient

from app import db
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


@pytest.fixture
def sqlite_path(tmp_path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "pm-integration.db"
    monkeypatch.setenv(db.DB_PATH_ENV, str(path))
    return path


@pytest.mark.anyio
async def test_board_routes_require_auth(sqlite_path) -> None:
    valid_payload = {
        "columns": [
            {"id": "col-a", "title": "A", "cardIds": ["card-1"]},
        ],
        "cards": {
            "card-1": {"id": "card-1", "title": "Card", "details": "Details"},
        },
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        board = await client.get("/api/board")
        save = await client.put("/api/board", json=valid_payload)

    assert board.status_code == 401
    assert save.status_code == 401


@pytest.mark.anyio
async def test_board_read_and_update_flow(sqlite_path) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login = await client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )
        board_response = await client.get("/api/board")
        board_payload = board_response.json()
        board_payload["columns"][0]["title"] = "Ideas"
        save = await client.put("/api/board", json=board_payload)
        round_trip = await client.get("/api/board")

    assert login.status_code == 200

    assert board_response.status_code == 200
    assert board_payload["columns"][0]["id"] == "col-backlog"

    assert save.status_code == 200
    assert save.json()["saved"] is True
    assert save.json()["board"]["columns"][0]["title"] == "Ideas"

    assert round_trip.status_code == 200
    assert round_trip.json()["columns"][0]["title"] == "Ideas"


@pytest.mark.anyio
async def test_board_update_rejects_invalid_payload(sqlite_path) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )
        board_response = await client.get("/api/board")
        invalid_payload = board_response.json()
        invalid_payload["columns"][0]["cardIds"] = ["missing-card"]
        response = await client.put("/api/board", json=invalid_payload)

    assert response.status_code == 422
