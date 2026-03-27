"""SQLite database operations for users, scores, answers, and skips."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

import bcrypt

from constants import DB_PATH


def _get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    with _get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS question_skips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                UNIQUE (user_id, question_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                correct_count INTEGER NOT NULL,
                total_count INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                user_answer TEXT,
                is_correct INTEGER NOT NULL,
                difficulty TEXT NOT NULL,
                topic TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )


def _hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def get_user_by_username(username: str, db_path: str = DB_PATH) -> dict[str, Any] | None:
    with _get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?;",
            (username,),
        ).fetchone()
    return dict(row) if row else None


def create_user(username: str, password: str, db_path: str = DB_PATH) -> int:
    password_hash = _hash_password(password)
    with _get_connection(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO users(username, password_hash) VALUES (?, ?);",
            (username, password_hash),
        )
    return int(cursor.lastrowid)


def authenticate_user(username: str, password: str, db_path: str = DB_PATH) -> int | None:
    user = get_user_by_username(username, db_path)
    if user is None:
        return None
    if _verify_password(password, str(user["password_hash"])):
        return int(user["id"])
    return None


def add_permanent_skip(user_id: int, question_id: str, db_path: str = DB_PATH) -> None:
    with _get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO question_skips(user_id, question_id)
            VALUES (?, ?);
            """,
            (user_id, question_id),
        )


def is_permanently_skipped(user_id: int, question_id: str, db_path: str = DB_PATH) -> bool:
    with _get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT 1 FROM question_skips
            WHERE user_id = ? AND question_id = ?
            LIMIT 1;
            """,
            (user_id, question_id),
        ).fetchone()
    return row is not None


def get_permanently_skipped_question_ids(
    user_id: int, db_path: str = DB_PATH
) -> set[str]:
    with _get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT question_id FROM question_skips WHERE user_id = ?;",
            (user_id,),
        ).fetchall()
    return {str(row["question_id"]) for row in rows}


def record_answer(
    user_id: int,
    question_id: str,
    user_answer: str,
    is_correct: bool,
    difficulty: str,
    topic: str,
    db_path: str = DB_PATH,
) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    with _get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO user_answers(
                user_id, question_id, user_answer, is_correct, difficulty, topic, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (user_id, question_id, user_answer, int(is_correct), difficulty, topic, timestamp),
        )


def record_score(
    user_id: int, correct_count: int, total_count: int, db_path: str = DB_PATH
) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    with _get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO scores(user_id, correct_count, total_count, created_at)
            VALUES (?, ?, ?, ?);
            """,
            (user_id, correct_count, total_count, timestamp),
        )


def get_scores_for_user(user_id: int, db_path: str = DB_PATH) -> list[dict[str, Any]]:
    with _get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, correct_count, total_count, created_at
            FROM scores
            WHERE user_id = ?
            ORDER BY created_at DESC;
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_stored_password_hash(username: str, db_path: str = DB_PATH) -> str | None:
    user = get_user_by_username(username, db_path)
    if not user:
        return None
    return str(user["password_hash"])
