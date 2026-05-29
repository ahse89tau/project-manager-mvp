import pytest
from pydantic import ValidationError

from app.schemas import AIKanbanResponse, BoardState


def sample_board() -> dict:
    return {
        "columns": [
            {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"]},
            {"id": "col-done", "title": "Done", "cardIds": []},
        ],
        "cards": {
            "card-1": {
                "id": "card-1",
                "title": "Task",
                "details": "Test details",
            }
        },
    }


def test_board_state_parses_and_serializes() -> None:
    board = BoardState.model_validate(sample_board())
    dumped = board.model_dump(by_alias=True)

    assert dumped["columns"][0]["cardIds"] == ["card-1"]
    assert dumped["cards"]["card-1"]["title"] == "Task"


def test_board_state_rejects_missing_card_reference() -> None:
    payload = sample_board()
    payload["columns"][0]["cardIds"] = ["missing-card"]

    with pytest.raises(ValidationError):
        BoardState.model_validate(payload)


def test_ai_response_allows_message_only() -> None:
    parsed = AIKanbanResponse.model_validate(
        {
            "assistantMessage": "No board changes required.",
            "applyBoardUpdate": False,
            "updatedBoard": None,
        }
    )
    assert parsed.apply_board_update is False
    assert parsed.updated_board is None


def test_ai_response_requires_board_when_update_true() -> None:
    with pytest.raises(ValidationError):
        AIKanbanResponse.model_validate(
            {
                "assistantMessage": "I updated your board.",
                "applyBoardUpdate": True,
                "updatedBoard": None,
            }
        )


def test_ai_response_with_board_update() -> None:
    parsed = AIKanbanResponse.model_validate(
        {
            "assistantMessage": "Moved one card to Done.",
            "applyBoardUpdate": True,
            "updatedBoard": sample_board(),
        }
    )
    dumped = parsed.model_dump(by_alias=True)
    assert dumped["applyBoardUpdate"] is True
    assert dumped["updatedBoard"]["columns"][0]["id"] == "col-backlog"
