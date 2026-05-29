import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.db import ensure_user, get_connection, get_or_create_board, init_db, update_board
from app.schemas import BoardState

BASE_DIR = Path(__file__).resolve().parent.parent
SESSION_COOKIE_NAME = "pm_session"
DEMO_USERNAME = "user"
DEMO_PASSWORD = "password"


def resolve_static_site_dir() -> Path:
    env_dir = os.getenv("FRONTEND_STATIC_DIR")
    candidates = []

    if env_dir:
        candidates.append(Path(env_dir))

    candidates.extend(
        [
            BASE_DIR.parent / "frontend" / "out",
            BASE_DIR / "static",
        ]
    )

    for candidate in candidates:
        if (candidate / "index.html").exists():
            return candidate

    return BASE_DIR / "static"


SITE_DIR = resolve_static_site_dir()

app = FastAPI(title="Project Management MVP API", version="0.1.0")
init_db()


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello from FastAPI"}


@app.get("/api/auth/session")
def session_status(request: Request) -> dict[str, bool]:
    is_authenticated = request.cookies.get(SESSION_COOKIE_NAME) == "1"
    return {"authenticated": is_authenticated}


@app.post("/api/auth/login")
def login(payload: LoginRequest, response: Response) -> dict[str, bool]:
    is_valid = payload.username == DEMO_USERNAME and payload.password == DEMO_PASSWORD
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value="1",
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 8,
    )
    return {"authenticated": True}


@app.post("/api/auth/logout")
def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return {"authenticated": False}


def require_authenticated_username(request: Request) -> str:
    if request.cookies.get(SESSION_COOKIE_NAME) != "1":
        raise HTTPException(status_code=401, detail="Authentication required")
    return DEMO_USERNAME


@app.get("/api/board")
def read_board(request: Request) -> dict:
    username = require_authenticated_username(request)
    with get_connection() as conn:
        user_id = ensure_user(conn, username)
        board = get_or_create_board(conn, user_id)
    return board.model_dump(by_alias=True)


@app.put("/api/board")
def save_board(payload: BoardState, request: Request) -> dict[str, object]:
    username = require_authenticated_username(request)
    with get_connection() as conn:
        user_id = ensure_user(conn, username)
        saved_board = update_board(conn, user_id, payload)
    return {"saved": True, "board": saved_board.model_dump(by_alias=True)}


app.mount("/", StaticFiles(directory=SITE_DIR, html=True), name="site")
