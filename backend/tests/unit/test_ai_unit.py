import json
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.ai import AI_MODEL, board_chat, chat
from app.main import app
from app.schemas import BoardState


# --- helpers ---

def _ok_response(content: str) -> MagicMock:
    mock = MagicMock(spec=httpx.Response)
    mock.raise_for_status.return_value = None
    mock.json.return_value = {"choices": [{"message": {"content": content}}]}
    return mock


_MINIMAL_BOARD = {
    "columns": [{"id": "col-1", "title": "Todo", "cardIds": ["card-1"]}],
    "cards": {"card-1": {"id": "card-1", "title": "Task A", "details": "Do it."}},
}

_MINIMAL_BOARD_STATE = BoardState.model_validate(_MINIMAL_BOARD)

_AI_MESSAGE_ONLY = json.dumps({
    "assistantMessage": "You have 1 card in Todo.",
    "applyBoardUpdate": False,
    "updatedBoard": None,
})

_UPDATED_BOARD = {
    "columns": [{"id": "col-1", "title": "Todo", "cardIds": []},
                {"id": "col-done", "title": "Done", "cardIds": ["card-1"]}],
    "cards": {"card-1": {"id": "card-1", "title": "Task A", "details": "Do it."}},
}

_AI_BOARD_UPDATE = json.dumps({
    "assistantMessage": "Moved Task A to Done.",
    "applyBoardUpdate": True,
    "updatedBoard": _UPDATED_BOARD,
})


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


# --- board_chat() unit tests ---

def test_board_chat_returns_message_only_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    with patch("app.ai.httpx.post", return_value=_ok_response(_AI_MESSAGE_ONLY)):
        result = board_chat(_MINIMAL_BOARD_STATE, "How many cards?", [])
    assert result.assistant_message == "You have 1 card in Todo."
    assert result.apply_board_update is False
    assert result.updated_board is None


def test_board_chat_returns_board_update(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    with patch("app.ai.httpx.post", return_value=_ok_response(_AI_BOARD_UPDATE)):
        result = board_chat(_MINIMAL_BOARD_STATE, "Move Task A to Done.", [])
    assert result.assistant_message == "Moved Task A to Done."
    assert result.apply_board_update is True
    assert result.updated_board is not None
    col_ids = [c.id for c in result.updated_board.columns]
    assert "col-done" in col_ids


def test_board_chat_sends_system_and_history_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    history = [
        {"role": "user", "content": "First message"},
        {"role": "assistant", "content": "First reply"},
    ]
    with patch("app.ai.httpx.post", return_value=_ok_response(_AI_MESSAGE_ONLY)) as mock_post:
        board_chat(_MINIMAL_BOARD_STATE, "Second message", history)
    sent_messages = mock_post.call_args.kwargs["json"]["messages"]
    assert sent_messages[0]["role"] == "system"
    assert sent_messages[1] == {"role": "user", "content": "First message"}
    assert sent_messages[2] == {"role": "assistant", "content": "First reply"}
    assert sent_messages[3] == {"role": "user", "content": "Second message"}


def test_board_chat_raises_502_on_non_json_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    with patch("app.ai.httpx.post", return_value=_ok_response("Sure, here is my answer!")):
        with pytest.raises(HTTPException) as exc_info:
            board_chat(_MINIMAL_BOARD_STATE, "hello", [])
    assert exc_info.value.status_code == 502
    assert "non-JSON" in exc_info.value.detail


def test_board_chat_raises_502_on_schema_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    bad_json = json.dumps({"wrongField": "oops"})
    with patch("app.ai.httpx.post", return_value=_ok_response(bad_json)):
        with pytest.raises(HTTPException) as exc_info:
            board_chat(_MINIMAL_BOARD_STATE, "hello", [])
    assert exc_info.value.status_code == 502
    assert "schema" in exc_info.value.detail


def test_board_chat_raises_502_when_apply_true_but_board_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    bad_json = json.dumps({
        "assistantMessage": "Done.",
        "applyBoardUpdate": True,
        "updatedBoard": None,
    })
    with patch("app.ai.httpx.post", return_value=_ok_response(bad_json)):
        with pytest.raises(HTTPException) as exc_info:
            board_chat(_MINIMAL_BOARD_STATE, "move it", [])
    assert exc_info.value.status_code == 502


def test_board_chat_raises_502_when_board_has_missing_card_ref(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    bad_board = {
        "columns": [{"id": "col-1", "title": "Todo", "cardIds": ["card-999"]}],
        "cards": {},
    }
    bad_json = json.dumps({
        "assistantMessage": "Done.",
        "applyBoardUpdate": True,
        "updatedBoard": bad_board,
    })
    with patch("app.ai.httpx.post", return_value=_ok_response(bad_json)):
        with pytest.raises(HTTPException) as exc_info:
            board_chat(_MINIMAL_BOARD_STATE, "move it", [])
    assert exc_info.value.status_code == 502


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


# --- /api/ai/chat route unit tests ---

@pytest.mark.anyio
async def test_ai_chat_requires_auth() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/ai/chat", json={"message": "hi"})
    assert response.status_code == 401


@pytest.mark.anyio
async def test_ai_chat_returns_message_only(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("PM_SQLITE_PATH", str(tmp_path / "test.db"))
    from app.schemas import AIKanbanResponse
    ai_resp = AIKanbanResponse.model_validate({
        "assistantMessage": "You have 1 card.",
        "applyBoardUpdate": False,
        "updatedBoard": None,
    })
    with patch("app.main.ai_board_chat", return_value=ai_resp):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/auth/login", json={"username": "user", "password": "password"})
            response = await client.post("/api/ai/chat", json={"message": "How many cards?"})
    assert response.status_code == 200
    data = response.json()
    assert data["assistantMessage"] == "You have 1 card."
    assert data["applyBoardUpdate"] is False
    assert data["boardUpdated"] is False


@pytest.mark.anyio
async def test_ai_chat_applies_board_update(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("PM_SQLITE_PATH", str(tmp_path / "test.db"))
    from app.schemas import AIKanbanResponse, BoardState
    updated = BoardState.model_validate(_UPDATED_BOARD)
    ai_resp = AIKanbanResponse.model_validate({
        "assistantMessage": "Moved Task A to Done.",
        "applyBoardUpdate": True,
        "updatedBoard": _UPDATED_BOARD,
    })
    with patch("app.main.ai_board_chat", return_value=ai_resp):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/auth/login", json={"username": "user", "password": "password"})
            response = await client.post("/api/ai/chat", json={"message": "Move Task A to Done."})
    assert response.status_code == 200
    data = response.json()
    assert data["assistantMessage"] == "Moved Task A to Done."
    assert data["applyBoardUpdate"] is True
    assert data["boardUpdated"] is True


@pytest.mark.anyio
async def test_ai_chat_propagates_502_on_ai_failure(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("PM_SQLITE_PATH", str(tmp_path / "test.db"))
    with patch("app.main.ai_board_chat", side_effect=HTTPException(status_code=502, detail="AI error")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/auth/login", json={"username": "user", "password": "password"})
            response = await client.post("/api/ai/chat", json={"message": "hello"})
    assert response.status_code == 502


@pytest.mark.anyio
async def test_ai_chat_passes_history_to_board_chat(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("PM_SQLITE_PATH", str(tmp_path / "test.db"))
    from app.schemas import AIKanbanResponse
    ai_resp = AIKanbanResponse.model_validate({
        "assistantMessage": "OK.",
        "applyBoardUpdate": False,
        "updatedBoard": None,
    })
    with patch("app.main.ai_board_chat", return_value=ai_resp) as mock_fn:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/auth/login", json={"username": "user", "password": "password"})
            await client.post("/api/ai/chat", json={
                "message": "second",
                "history": [
                    {"role": "user", "content": "first"},
                    {"role": "assistant", "content": "first reply"},
                ],
            })
    _, call_user_msg, call_history = mock_fn.call_args.args
    assert call_user_msg == "second"
    assert call_history == [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "first reply"},
    ]
