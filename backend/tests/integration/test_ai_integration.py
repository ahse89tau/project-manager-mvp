import os

import pytest
from httpx import ASGITransport, AsyncClient

from app import db
from app.main import app


@pytest.fixture
def sqlite_path(tmp_path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "pm-ai-integration.db"
    monkeypatch.setenv(db.DB_PATH_ENV, str(path))
    return path


skip_no_key = pytest.mark.skipif(
    not os.getenv("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set",
)


@pytest.mark.anyio
@skip_no_key
async def test_ai_ping_calls_openrouter_and_returns_response(sqlite_path) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/auth/login", json={"username": "user", "password": "password"})
        response = await client.get("/api/ai/ping")

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["response"]


@pytest.mark.anyio
@skip_no_key
async def test_ai_chat_message_only_response(sqlite_path) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/auth/login", json={"username": "user", "password": "password"})
        response = await client.post("/api/ai/chat", json={
            "message": "How many cards are on the board? Just tell me the count."
        })

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["assistantMessage"], str)
    assert data["assistantMessage"]
    assert isinstance(data["applyBoardUpdate"], bool)
    assert isinstance(data["boardUpdated"], bool)


@pytest.mark.anyio
@skip_no_key
async def test_ai_chat_board_update_response(sqlite_path) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/auth/login", json={"username": "user", "password": "password"})

        board_before = (await client.get("/api/board")).json()

        response = await client.post("/api/ai/chat", json={
            "message": (
                "Move the card titled 'Align roadmap themes' to the Done column. "
                "Apply the board change."
            )
        })

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["assistantMessage"], str)

    if data["boardUpdated"]:
        board_after = (await client.get("/api/board")).json()
        done_col = next(
            (c for c in board_after["columns"] if c["title"] == "Done"), None
        )
        assert done_col is not None
        card_in_done = any(
            board_after["cards"].get(cid, {}).get("title") == "Align roadmap themes"
            for cid in done_col["cardIds"]
        )
        assert card_in_done, "Expected 'Align roadmap themes' to be in the Done column"


@pytest.mark.anyio
@skip_no_key
async def test_ai_chat_preserves_board_on_message_only(sqlite_path) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/auth/login", json={"username": "user", "password": "password"})

        board_before = (await client.get("/api/board")).json()

        await client.post("/api/ai/chat", json={
            "message": "What columns exist on the board? Do not change anything."
        })

        board_after = (await client.get("/api/board")).json()

    assert board_before == board_after
