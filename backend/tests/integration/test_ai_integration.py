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


@pytest.mark.anyio
@pytest.mark.skipif(
    not os.getenv("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set",
)
async def test_ai_ping_calls_openrouter_and_returns_response(sqlite_path) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/auth/login", json={"username": "user", "password": "password"})
        response = await client.get("/api/ai/ping")

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["response"]
