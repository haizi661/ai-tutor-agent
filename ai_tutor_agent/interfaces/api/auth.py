import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from .runtime import get_runtime


router = APIRouter(prefix="/api/auth", tags=["auth"])

TOKEN_TTL_DAYS = 30
PBKDF2_ROUNDS = 260000


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def _validate_credentials(username: str, password: str) -> None:
    if not username or len(username) < 3:
        raise HTTPException(status_code=400, detail="用户名至少 3 个字符。")
    if len(username) > 64:
        raise HTTPException(status_code=400, detail="用户名过长。")
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 个字符。")


def _hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PBKDF2_ROUNDS,
    )
    return digest.hex()


def build_password_record(password: str) -> str:
    salt = secrets.token_hex(16)
    password_hash = _hash_password(password, salt)
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt}${password_hash}"


def verify_password(password: str, stored_record: str) -> bool:
    try:
        algorithm, rounds_str, salt, expected_hash = stored_record.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        rounds = int(rounds_str)
    except Exception:
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        rounds,
    ).hex()
    return hmac.compare_digest(digest, expected_hash)


def ensure_auth_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS auth_tokens (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS thread_owners (
            thread_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_id ON auth_tokens(user_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_thread_owners_user_id ON thread_owners(user_id)"
    )
    conn.commit()


def _extract_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    query_token = request.query_params.get("access_token", "").strip()
    if query_token:
        return query_token

    raise HTTPException(status_code=401, detail="未登录或登录已失效。")


def _issue_token(conn: sqlite3.Connection, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    created_at = _utc_now().isoformat()
    expires_at = (_utc_now() + timedelta(days=TOKEN_TTL_DAYS)).isoformat()
    conn.execute(
        """
        INSERT INTO auth_tokens (token, user_id, created_at, expires_at)
        VALUES (?, ?, ?, ?)
        """,
        (token, user_id, created_at, expires_at),
    )
    conn.commit()
    return token


def get_current_user(request: Request) -> dict:
    runtime = get_runtime(request)
    db_path = runtime.settings.memory_db_path
    token = _extract_bearer_token(request)

    with sqlite3.connect(db_path) as conn:
        ensure_auth_tables(conn)
        row = conn.execute(
            """
            SELECT u.id, u.username, t.expires_at
            FROM auth_tokens t
            JOIN users u ON u.id = t.user_id
            WHERE t.token = ?
            """,
            (token,),
        ).fetchone()

        if row is None:
            raise HTTPException(status_code=401, detail="登录状态无效，请重新登录。")

        user_id, username, expires_at_raw = row
        try:
            expires_at = datetime.fromisoformat(expires_at_raw)
        except ValueError:
            conn.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
            conn.commit()
            raise HTTPException(status_code=401, detail="登录状态无效，请重新登录。")

        if _utc_now() >= expires_at:
            conn.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
            conn.commit()
            raise HTTPException(status_code=401, detail="登录已过期，请重新登录。")

        return {"id": int(user_id), "username": str(username), "token": token}


def ensure_thread_access(
    request: Request,
    user_id: int,
    thread_id: str,
    *,
    auto_bind: bool,
) -> None:
    runtime = get_runtime(request)
    db_path = runtime.settings.memory_db_path
    with sqlite3.connect(db_path) as conn:
        ensure_auth_tables(conn)
        row = conn.execute(
            "SELECT user_id FROM thread_owners WHERE thread_id = ?",
            (thread_id,),
        ).fetchone()

        if row is None:
            if not auto_bind:
                raise HTTPException(status_code=404, detail=f"Unknown thread_id: {thread_id}")
            conn.execute(
                """
                INSERT INTO thread_owners (thread_id, user_id, created_at)
                VALUES (?, ?, ?)
                """,
                (thread_id, user_id, _utc_now().isoformat()),
            )
            conn.commit()
            return

        owner_id = int(row[0])
        if owner_id != int(user_id):
            raise HTTPException(status_code=403, detail="你没有权限访问该会话。")


def remove_thread_owner(request: Request, thread_id: str) -> None:
    runtime = get_runtime(request)
    db_path = runtime.settings.memory_db_path
    with sqlite3.connect(db_path) as conn:
        ensure_auth_tables(conn)
        conn.execute("DELETE FROM thread_owners WHERE thread_id = ?", (thread_id,))
        conn.commit()


def list_user_thread_ids(request: Request, user_id: int, *, limit: int = 50) -> list[str]:
    runtime = get_runtime(request)
    db_path = runtime.settings.memory_db_path
    with sqlite3.connect(db_path) as conn:
        ensure_auth_tables(conn)
        rows = conn.execute(
            """
            SELECT c.thread_id
            FROM checkpoints c
            JOIN thread_owners o ON o.thread_id = c.thread_id
            WHERE o.user_id = ?
            GROUP BY c.thread_id
            ORDER BY MAX(c.rowid) DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [str(row[0]) for row in rows]


@router.post("/register")
async def register(req: RegisterRequest, request: Request):
    runtime = get_runtime(request)
    db_path = runtime.settings.memory_db_path
    username = _normalize_username(req.username)
    _validate_credentials(username, req.password)

    with sqlite3.connect(db_path) as conn:
        ensure_auth_tables(conn)
        exists = conn.execute(
            "SELECT 1 FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="用户名已存在。")

        conn.execute(
            """
            INSERT INTO users (username, password_hash, created_at)
            VALUES (?, ?, ?)
            """,
            (username, build_password_record(req.password), _utc_now().isoformat()),
        )
        user_id = int(conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()[0])
        token = _issue_token(conn, user_id)

    return {
        "status": "ok",
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user_id, "username": username},
    }


@router.post("/login")
async def login(req: LoginRequest, request: Request):
    runtime = get_runtime(request)
    db_path = runtime.settings.memory_db_path
    username = _normalize_username(req.username)
    _validate_credentials(username, req.password)

    with sqlite3.connect(db_path) as conn:
        ensure_auth_tables(conn)
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail="用户名或密码错误。")

        user_id, password_hash = row
        if not verify_password(req.password, str(password_hash)):
            raise HTTPException(status_code=401, detail="用户名或密码错误。")

        token = _issue_token(conn, int(user_id))

    return {
        "status": "ok",
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": int(user_id), "username": username},
    }


@router.get("/me")
async def me(request: Request):
    user = get_current_user(request)
    return {"status": "ok", "user": {"id": user["id"], "username": user["username"]}}


@router.post("/logout")
async def logout(request: Request):
    user = get_current_user(request)
    runtime = get_runtime(request)
    db_path = runtime.settings.memory_db_path
    with sqlite3.connect(db_path) as conn:
        ensure_auth_tables(conn)
        conn.execute("DELETE FROM auth_tokens WHERE token = ?", (user["token"],))
        conn.commit()
    return {"status": "ok"}
