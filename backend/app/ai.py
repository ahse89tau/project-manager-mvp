import json as json_lib
import os

import httpx
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas import AIKanbanResponse, BoardState

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
AI_MODEL = "openai/gpt-oss-120b:free"

_SYSTEM_PROMPT = """\
You are a project management assistant. You help users manage a Kanban board.

Current board state:
{board_json}

Respond with ONLY a JSON object matching this exact structure:
{{
  "assistantMessage": "<your response to the user>",
  "applyBoardUpdate": false,
  "updatedBoard": null
}}

To create, move, edit, or delete cards or columns, set "applyBoardUpdate" to true and provide the complete updated board in "updatedBoard". Include every column and every card, even unchanged ones.

Rules:
- "updatedBoard" must be null when "applyBoardUpdate" is false.
- "updatedBoard" must be the full board object when "applyBoardUpdate" is true.
- Every cardId listed in a column's cardIds must exist in the cards dictionary.
- Preserve existing ids. Use unique ids for new items (e.g. "card-9", "col-new").
- No extra fields. No markdown. No text outside the JSON object."""


def _get_api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key:
        raise HTTPException(status_code=503, detail="OPENROUTER_API_KEY is not configured")
    return key


def chat(prompt: str) -> str:
    api_key = _get_api_key()
    try:
        response = httpx.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": AI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"OpenRouter error: {exc.response.status_code}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"OpenRouter request failed: {exc}",
        ) from exc

    data = response.json()
    return data["choices"][0]["message"]["content"]


def board_chat(
    board: BoardState,
    user_message: str,
    history: list[dict[str, str]],
) -> AIKanbanResponse:
    api_key = _get_api_key()
    board_json = json_lib.dumps(board.model_dump(by_alias=True))
    system_content = _SYSTEM_PROMPT.format(board_json=board_json)

    messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    try:
        response = httpx.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": AI_MODEL,
                "messages": messages,
                "response_format": {"type": "json_object"},
            },
            timeout=60.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"OpenRouter error: {exc.response.status_code}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"OpenRouter request failed: {exc}",
        ) from exc

    raw = response.json()["choices"][0]["message"]["content"]

    try:
        parsed = json_lib.loads(raw)
    except json_lib.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail="AI returned non-JSON response",
        ) from exc

    try:
        return AIKanbanResponse.model_validate(parsed)
    except ValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI response did not match expected schema: {exc.error_count()} error(s)",
        ) from exc
