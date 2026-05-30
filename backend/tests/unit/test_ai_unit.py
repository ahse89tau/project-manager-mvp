from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.ai import AI_MODEL, chat
from app.main import app


def _ok_response(content: str) -> MagicMock:
    mock = MagicMock(spec=httpx.Response)
    mock.raise_for_status.return_value = None
    mock.json.return_value = {"choices": [{"message": {"content": content}}]}
    return mock


# --- chat() unit tests ---

def test_chat_returns_ai_content(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    with patch("app.ai.httpx.post", return_value=_ok_response("4")) as mock_post:
        result = chat("What is 2+2?")
    assert result == "4"
    assert mock_post.call_args.kwargs["json"]["model"] == AI_MODEL
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer test-key"


def test_chat_raises_503_when_no_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    with pytest.raises(HTTPException) as exc_info:
        chat("hello")
    assert exc_info.value.status_code == 503
    assert "OPENROUTER_API_KEY" in exc_info.value.detail


def test_chat_raises_502_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    error_response = MagicMock(spec=httpx.Response)
    error_response.status_code = 401
    http_error = httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=error_response)
    with patch("app.ai.httpx.post", side_effect=http_error):
        with pytest.raises(HTTPException) as exc_info:
            chat("hello")
    assert exc_info.value.status_code == 502
    assert "401" in exc_info.value.detail


def test_chat_raises_502_on_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    with patch("app.ai.httpx.post", side_effect=httpx.ConnectError("timeout")):
        with pytest.raises(HTTPException) as exc_info:
            chat("hello")
    assert exc_info.value.status_code == 502
    assert "request failed" in exc_info.value.detail


# --- /api/ai/ping route unit tests ---

@pytest.mark.anyio
async def test_ai_ping_requires_auth() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/ai/ping")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_ai_ping_returns_ai_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    with patch("app.main.ai_chat", return_value="4"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/auth/login", json={"username": "user", "password": "password"})
            response = await client.get("/api/ai/ping")
    assert response.status_code == 200
    assert response.json() == {"response": "4"}


@pytest.mark.anyio
async def test_ai_ping_propagates_503_when_no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/auth/login", json={"username": "user", "password": "password"})
        response = await client.get("/api/ai/ping")
    assert response.status_code == 503
