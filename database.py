"""
database.py — AI Study Platform
================================
Senior Engineer: Complete SQLite database layer
Tables: users, chat_history, pdfs, pdf_chunks, quizzes,
        quiz_scores, flashcards, study_plans, analytics,
        audio_summaries, leaderboard_cache
"""

import sqlite3
import bcrypt
import json
import os
import numpy as np
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

DB_PATH = os.getenv("DB_PATH", "studyai.db")


# ─────────────────────────────────────────────
# CONNECTION MANAGER
# ─────────────────────────────────────────────

@contextmanager
def get_connection():
    """
    Thread-safe context manager for SQLite connections.
    Always use this — never open bare sqlite3.connect() calls.

    Usage:
        with get_connection() as conn:
            conn.execute("SELECT ...")
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row          # Rows behave like dicts
    conn.execute("PRAGMA journal_mode=WAL") # Better concurrent read/write
    conn.execute("PRAGMA foreign_keys=ON")  # Enforce FK constraints
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────
# TABLE CREATION — run once on startup
# ─────────────────────────────────────────────

def create_tables() -> None:
    """
    Creates all tables if they don't exist.
    Call this at the top of app.py before anything else.
    """
    with get_connection() as conn:

        # ── USERS ──────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    UNIQUE NOT NULL,
                email         TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                full_name     TEXT    DEFAULT '',
                avatar_color  TEXT    DEFAULT '#6C63FF',
                theme         TEXT    DEFAULT 'dark',
                created_at    TEXT    DEFAULT (datetime('now')),
                last_login    TEXT
            )
        """)

        # ── CHAT HISTORY ───────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                session_id TEXT    NOT NULL,
                role       TEXT    NOT NULL CHECK(role IN ('user','assistant')),
                content    TEXT    NOT NULL,
                topic      TEXT    DEFAULT '',
                timestamp  TEXT    DEFAULT (datetime('now'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_history(user_id, session_id)")

        # ── PDFs ────────────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pdfs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                filename    TEXT    NOT NULL,
                file_path   TEXT    DEFAULT '',
                total_pages INTEGER DEFAULT 0,
                subject     TEXT    DEFAULT '',
                uploaded_at TEXT    DEFAULT (datetime('now'))
            )
        """)

        # ── PDF CHUNKS (RAG) ────────────────────────
        # embedding stored as JSON-encoded float list e.g. "[0.12, -0.34, ...]"
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pdf_chunks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                pdf_id      INTEGER NOT NULL REFERENCES pdfs(id) ON DELETE CASCADE,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                chunk_text  TEXT    NOT NULL,
                chunk_index INTEGER NOT NULL,
                page_number INTEGER DEFAULT 0,
                embedding   TEXT    DEFAULT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_pdf ON pdf_chunks(pdf_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_user ON pdf_chunks(user_id)")

        # ── QUIZZES ─────────────────────────────────
        # questions_json: JSON array of {question, type, options, answer, topic}
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quizzes (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title          TEXT    DEFAULT 'Untitled Quiz',
                subject        TEXT    DEFAULT '',
                questions_json TEXT    NOT NULL,
                difficulty     TEXT    DEFAULT 'medium' CHECK(difficulty IN ('easy','medium','hard')),
                source_type    TEXT    DEFAULT 'topic',  -- 'topic' | 'pdf' | 'notes'
                source_ref     TEXT    DEFAULT '',       -- topic name or pdf filename
                created_at     TEXT    DEFAULT (datetime('now'))
            )
        """)

        # ── QUIZ SCORES ─────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_scores (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                quiz_id         INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
                score           REAL    NOT NULL,   -- percentage 0-100
                total_questions INTEGER NOT NULL,
                correct_answers INTEGER NOT NULL,
                time_taken_sec  INTEGER DEFAULT 0,
                weak_topics     TEXT    DEFAULT '[]', -- JSON array of topic strings
                answers_json    TEXT    DEFAULT '{}', -- JSON: {q_index: user_answer}
                taken_at        TEXT    DEFAULT (datetime('now'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scores_user ON quiz_scores(user_id)")

        # ── FLASHCARDS ──────────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS flashcards (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                subject       TEXT    DEFAULT '',
                front         TEXT    NOT NULL,
                back          TEXT    NOT NULL,
                difficulty    TEXT    DEFAULT 'medium',
                times_reviewed INTEGER DEFAULT 0,
                last_reviewed TEXT    DEFAULT NULL,
                next_review   TEXT    DEFAULT NULL,   -- spaced repetition date
                ease_factor   REAL    DEFAULT 2.5,    -- SM-2 algorithm factor
                source_pdf_id INTEGER DEFAULT NULL REFERENCES pdfs(id) ON DELETE SET NULL,
                created_at    TEXT    DEFAULT (datetime('now'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_flash_user ON flashcards(user_id)")

        # ── STUDY PLANS ─────────────────────────────
        # schedule_json: Gemini-generated day-by-day plan as JSON
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_plans (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                exam_name      TEXT    NOT NULL,
                exam_date      TEXT    NOT NULL,   -- ISO date string YYYY-MM-DD
                subjects_json  TEXT    NOT NULL,   -- JSON: [{name, weight, weak}]
                daily_hours    REAL    DEFAULT 2.0,
                schedule_json  TEXT    DEFAULT '{}', -- Gemini output
                is_active      INTEGER DEFAULT 1,
                created_at     TEXT    DEFAULT (datetime('now'))
            )
        """)

        # ── ANALYTICS EVENTS ────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                event_type    TEXT    NOT NULL,  -- 'quiz'|'chat'|'pdf'|'flashcard'|'audio'
                subject       TEXT    DEFAULT '',
                score         REAL    DEFAULT NULL,
                duration_min  REAL    DEFAULT 0,
                metadata_json TEXT    DEFAULT '{}',
                recorded_at   TEXT    DEFAULT (datetime('now'))
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_analytics_user ON analytics(user_id)")

        # ── AUDIO SUMMARIES ─────────────────────────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audio_summaries (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                pdf_id          INTEGER DEFAULT NULL REFERENCES pdfs(id) ON DELETE SET NULL,
                title           TEXT    DEFAULT 'Audio Summary',
                summary_text    TEXT    NOT NULL,
                audio_file_path TEXT    DEFAULT '',
                duration_sec    INTEGER DEFAULT 0,
                language        TEXT    DEFAULT 'en',
                created_at      TEXT    DEFAULT (datetime('now'))
            )
        """)

        # ── LEADERBOARD CACHE ───────────────────────
        # Refreshed on demand — avoids expensive GROUP BY on every page load
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard_cache (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                username     TEXT    NOT NULL,
                total_score  REAL    DEFAULT 0,   -- sum of all quiz scores
                quizzes_taken INTEGER DEFAULT 0,
                avg_score    REAL    DEFAULT 0,
                best_subject TEXT    DEFAULT '',
                rank         INTEGER DEFAULT 0,
                updated_at   TEXT    DEFAULT (datetime('now'))
            )
        """)

    print(f"[DB] All tables ready → {DB_PATH}")


# ─────────────────────────────────────────────
# AUTH — USERS
# ─────────────────────────────────────────────

def register_user(username: str, email: str, password: str, full_name: str = "") -> Dict:
    """
    Register a new user. Returns {success, user_id, error}.
    Password is bcrypt-hashed — never store plaintext.
    """
    try:
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        with get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO users (username, email, password_hash, full_name)
                   VALUES (?, ?, ?, ?)""",
                (username.strip().lower(), email.strip().lower(), password_hash, full_name.strip())
            )
            return {"success": True, "user_id": cursor.lastrowid, "error": None}
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return {"success": False, "user_id": None, "error": "Username already taken"}
        if "email" in str(e):
            return {"success": False, "user_id": None, "error": "Email already registered"}
        return {"success": False, "user_id": None, "error": str(e)}


def login_user(username: str, password: str) -> Dict:
    """
    Verify credentials. Returns {success, user, error}.
    user dict includes id, username, email, full_name, avatar_color, theme.
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username.strip().lower(),)
        ).fetchone()

    if not row:
        return {"success": False, "user": None, "error": "Username not found"}

    if not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return {"success": False, "user": None, "error": "Incorrect password"}

    # Update last_login
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET last_login = datetime('now') WHERE id = ?",
            (row["id"],)
        )

    return {
        "success": True,
        "user": {
            "id":           row["id"],
            "username":     row["username"],
            "email":        row["email"],
            "full_name":    row["full_name"],
            "avatar_color": row["avatar_color"],
            "theme":        row["theme"],
            "created_at":   row["created_at"],
        },
        "error": None,
    }


def get_user_by_id(user_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def update_user_settings(user_id: int, full_name: str = None, avatar_color: str = None, theme: str = None) -> bool:
    fields, values = [], []
    if full_name    is not None: fields.append("full_name = ?");    values.append(full_name)
    if avatar_color is not None: fields.append("avatar_color = ?"); values.append(avatar_color)
    if theme        is not None: fields.append("theme = ?");        values.append(theme)
    if not fields:
        return False
    values.append(user_id)
    with get_connection() as conn:
        conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
    return True


def change_password(user_id: int, old_password: str, new_password: str) -> Dict:
    user_row = get_user_by_id(user_id)
    if not user_row:
        return {"success": False, "error": "User not found"}
    with get_connection() as conn:
        row = conn.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()
    if not bcrypt.checkpw(old_password.encode(), row["password_hash"].encode()):
        return {"success": False, "error": "Current password is incorrect"}
    new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    with get_connection() as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
    return {"success": True, "error": None}


# ─────────────────────────────────────────────
# CHAT HISTORY
# ─────────────────────────────────────────────

def save_message(user_id: int, session_id: str, role: str, content: str, topic: str = "") -> int:
    """Save a single chat message. Returns the new message id."""
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO chat_history (user_id, session_id, role, content, topic)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, session_id, role, content, topic)
        )
        return cursor.lastrowid


def get_chat_history(user_id: int, session_id: str, limit: int = 50) -> List[Dict]:
    """
    Returns list of {role, content, topic, timestamp} for a session.
    Ordered oldest-first so it can be fed directly into Gemini chat history.
    """
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT role, content, topic, timestamp
               FROM chat_history
               WHERE user_id = ? AND session_id = ?
               ORDER BY id ASC
               LIMIT ?""",
            (user_id, session_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_sessions(user_id: int) -> List[Dict]:
    """Returns summary of all chat sessions for a user (for history sidebar)."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT session_id,
                      MIN(timestamp) as started_at,
                      COUNT(*) as message_count,
                      MAX(topic) as last_topic
               FROM chat_history
               WHERE user_id = ?
               GROUP BY session_id
               ORDER BY started_at DESC""",
            (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def delete_session(user_id: int, session_id: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM chat_history WHERE user_id = ? AND session_id = ?",
            (user_id, session_id)
        )


# ─────────────────────────────────────────────
# PDFs
# ─────────────────────────────────────────────

def save_pdf(user_id: int, filename: str, file_path: str, total_pages: int, subject: str = "") -> int:
    """Register an uploaded PDF. Returns pdf_id."""
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO pdfs (user_id, filename, file_path, total_pages, subject)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, filename, file_path, total_pages, subject)
        )
        return cursor.lastrowid


def get_user_pdfs(user_id: int) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM pdfs WHERE user_id = ? ORDER BY uploaded_at DESC",
            (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_pdf(pdf_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM pdfs WHERE id = ?", (pdf_id,)).fetchone()
    return dict(row) if row else None


def delete_pdf(user_id: int, pdf_id: int) -> None:
    """Deletes pdf + cascades to pdf_chunks automatically."""
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM pdfs WHERE id = ? AND user_id = ?",
            (pdf_id, user_id)
        )


# ─────────────────────────────────────────────
# PDF CHUNKS  (RAG pipeline)
# ─────────────────────────────────────────────

def save_chunks(pdf_id: int, user_id: int, chunks: List[Dict]) -> None:
    """
    Bulk-insert text chunks.
    Each chunk dict: {chunk_text, chunk_index, page_number, embedding (list[float])}
    embedding is stored as JSON string.
    """
    rows = [
        (
            pdf_id,
            user_id,
            c["chunk_text"],
            c["chunk_index"],
            c.get("page_number", 0),
            json.dumps(c["embedding"]) if c.get("embedding") else None,
        )
        for c in chunks
    ]
    with get_connection() as conn:
        conn.executemany(
            """INSERT INTO pdf_chunks
               (pdf_id, user_id, chunk_text, chunk_index, page_number, embedding)
               VALUES (?, ?, ?, ?, ?, ?)""",
            rows
        )


def update_chunk_embedding(chunk_id: int, embedding: List[float]) -> None:
    """Update a single chunk's embedding after generation."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE pdf_chunks SET embedding = ? WHERE id = ?",
            (json.dumps(embedding), chunk_id)
        )


def get_chunks_for_pdf(pdf_id: int) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM pdf_chunks WHERE pdf_id = ? ORDER BY chunk_index",
            (pdf_id,)
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["embedding"] = json.loads(d["embedding"]) if d["embedding"] else None
        result.append(d)
    return result


def get_chunks_with_embeddings(user_id: int, pdf_id: int = None) -> List[Dict]:
    """
    Returns chunks that have embeddings, optionally filtered to one PDF.
    Used by the RAG similarity search.
    """
    with get_connection() as conn:
        if pdf_id:
            rows = conn.execute(
                """SELECT id, chunk_text, page_number, embedding
                   FROM pdf_chunks
                   WHERE user_id = ? AND pdf_id = ? AND embedding IS NOT NULL""",
                (user_id, pdf_id)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT id, chunk_text, page_number, embedding
                   FROM pdf_chunks
                   WHERE user_id = ? AND embedding IS NOT NULL""",
                (user_id,)
            ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["embedding"] = json.loads(d["embedding"])
        result.append(d)
    return result


def pdf_has_embeddings(pdf_id: int) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM pdf_chunks WHERE pdf_id = ? AND embedding IS NOT NULL",
            (pdf_id,)
        ).fetchone()
    return row["cnt"] > 0


def delete_chunks_for_pdf(pdf_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM pdf_chunks WHERE pdf_id = ?", (pdf_id,))


# ─────────────────────────────────────────────
# QUIZZES
# ─────────────────────────────────────────────

def save_quiz(
    user_id: int,
    title: str,
    subject: str,
    questions: List[Dict],
    difficulty: str = "medium",
    source_type: str = "topic",
    source_ref: str = "",
) -> int:
    """
    Save a generated quiz. questions is a Python list — stored as JSON.
    Returns quiz_id.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO quizzes
               (user_id, title, subject, questions_json, difficulty, source_type, source_ref)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, title, subject, json.dumps(questions), difficulty, source_type, source_ref)
        )
        return cursor.lastrowid


def get_quiz(quiz_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["questions"] = json.loads(d["questions_json"])
    return d


def get_user_quizzes(user_id: int, limit: int = 20) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT q.*, COUNT(qs.id) as attempt_count,
                      MAX(qs.score) as best_score
               FROM quizzes q
               LEFT JOIN quiz_scores qs ON q.id = qs.quiz_id
               WHERE q.user_id = ?
               GROUP BY q.id
               ORDER BY q.created_at DESC
               LIMIT ?""",
            (user_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]


def delete_quiz(user_id: int, quiz_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM quizzes WHERE id = ? AND user_id = ?",
            (quiz_id, user_id)
        )


# ─────────────────────────────────────────────
# QUIZ SCORES
# ─────────────────────────────────────────────

def save_quiz_score(
    user_id: int,
    quiz_id: int,
    score: float,
    total_questions: int,
    correct_answers: int,
    time_taken_sec: int = 0,
    weak_topics: List[str] = None,
    answers: Dict = None,
) -> int:
    """Save a quiz attempt result. Returns score_id."""
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO quiz_scores
               (user_id, quiz_id, score, total_questions, correct_answers,
                time_taken_sec, weak_topics, answers_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id, quiz_id, round(score, 2),
                total_questions, correct_answers, time_taken_sec,
                json.dumps(weak_topics or []),
                json.dumps(answers or {}),
            )
        )
        score_id = cursor.lastrowid

    # Log to analytics
    log_analytics_event(user_id, "quiz", score=score)
    # Rebuild leaderboard cache
    refresh_leaderboard_for_user(user_id)

    return score_id


def get_user_scores(user_id: int, limit: int = 50) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT qs.*, q.title, q.subject, q.difficulty
               FROM quiz_scores qs
               JOIN quizzes q ON q.id = qs.quiz_id
               WHERE qs.user_id = ?
               ORDER BY qs.taken_at DESC
               LIMIT ?""",
            (user_id, limit)
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["weak_topics"] = json.loads(d["weak_topics"])
        result.append(d)
    return result


def get_weak_topics(user_id: int, top_n: int = 5) -> List[Tuple[str, int]]:
    """
    Aggregates weak topics across all quiz attempts.
    Returns [(topic, count), ...] sorted by frequency.
    """
    rows = get_user_scores(user_id, limit=200)
    topic_count: Dict[str, int] = {}
    for r in rows:
        for t in r["weak_topics"]:
            topic_count[t] = topic_count.get(t, 0) + 1
    return sorted(topic_count.items(), key=lambda x: x[1], reverse=True)[:top_n]


def get_score_trend(user_id: int, last_n: int = 10) -> List[Dict]:
    """Returns last N quiz scores with date — used for trend charts."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT qs.score, qs.taken_at, q.subject
               FROM quiz_scores qs
               JOIN quizzes q ON q.id = qs.quiz_id
               WHERE qs.user_id = ?
               ORDER BY qs.taken_at DESC
               LIMIT ?""",
            (user_id, last_n)
        ).fetchall()
    return [dict(r) for r in reversed(rows)]  # chronological order


def get_subject_performance(user_id: int) -> List[Dict]:
    """Average score per subject — for radar/bar charts."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT q.subject,
                      COUNT(qs.id)       as attempts,
                      AVG(qs.score)      as avg_score,
                      MAX(qs.score)      as best_score,
                      MIN(qs.score)      as worst_score
               FROM quiz_scores qs
               JOIN quizzes q ON q.id = qs.quiz_id
               WHERE qs.user_id = ?
               GROUP BY q.subject
               ORDER BY avg_score DESC""",
            (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────
# FLASHCARDS
# ─────────────────────────────────────────────

def save_flashcard(
    user_id: int,
    front: str,
    back: str,
    subject: str = "",
    difficulty: str = "medium",
    source_pdf_id: int = None,
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO flashcards
               (user_id, front, back, subject, difficulty, source_pdf_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, front, back, subject, difficulty, source_pdf_id)
        )
        return cursor.lastrowid


def save_flashcards_bulk(user_id: int, cards: List[Dict], source_pdf_id: int = None) -> int:
    """
    Bulk-insert flashcards. Each card dict: {front, back, subject, difficulty}
    Returns count inserted.
    """
    rows = [
        (user_id, c["front"], c["back"],
         c.get("subject", ""), c.get("difficulty", "medium"), source_pdf_id)
        for c in cards
    ]
    with get_connection() as conn:
        conn.executemany(
            """INSERT INTO flashcards (user_id, front, back, subject, difficulty, source_pdf_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            rows
        )
    return len(rows)


def get_flashcards(user_id: int, subject: str = None, due_only: bool = False) -> List[Dict]:
    today = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        if due_only:
            query = """SELECT * FROM flashcards
                       WHERE user_id = ? AND (next_review IS NULL OR next_review <= ?)"""
            params = [user_id, today]
        else:
            query = "SELECT * FROM flashcards WHERE user_id = ?"
            params = [user_id]

        if subject:
            query += " AND subject = ?"
            params.append(subject)

        query += " ORDER BY created_at DESC"
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def update_flashcard_review(card_id: int, ease: str) -> None:
    """
    SM-2 spaced repetition update.
    ease: 'easy' (5), 'medium' (3), 'hard' (1)
    Updates ease_factor and next_review date.
    """
    ease_map = {"easy": 5, "medium": 3, "hard": 1}
    q = ease_map.get(ease, 3)

    with get_connection() as conn:
        row = conn.execute(
            "SELECT ease_factor, times_reviewed FROM flashcards WHERE id = ?",
            (card_id,)
        ).fetchone()
        if not row:
            return

        ef = row["ease_factor"]
        n  = row["times_reviewed"] + 1

        # SM-2 formula
        ef_new = max(1.3, ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))
        if   n == 1: interval = 1
        elif n == 2: interval = 6
        else:        interval = round((n - 1) * ef_new)

        from datetime import timedelta
        next_review = (datetime.now() + timedelta(days=interval)).strftime("%Y-%m-%d")

        conn.execute(
            """UPDATE flashcards
               SET times_reviewed = ?, ease_factor = ?, last_reviewed = datetime('now'),
                   next_review = ?, difficulty = ?
               WHERE id = ?""",
            (n, round(ef_new, 3), next_review, ease, card_id)
        )


def delete_flashcard(user_id: int, card_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM flashcards WHERE id = ? AND user_id = ?",
            (card_id, user_id)
        )


def get_flashcard_subjects(user_id: int) -> List[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT subject FROM flashcards WHERE user_id = ? ORDER BY subject",
            (user_id,)
        ).fetchall()
    return [r["subject"] for r in rows if r["subject"]]


# ─────────────────────────────────────────────
# STUDY PLANS
# ─────────────────────────────────────────────

def save_study_plan(
    user_id: int,
    exam_name: str,
    exam_date: str,
    subjects: List[Dict],
    daily_hours: float,
    schedule: Dict,
) -> int:
    """Save a Gemini-generated study plan. Returns plan_id."""
    # Deactivate previous plans
    with get_connection() as conn:
        conn.execute(
            "UPDATE study_plans SET is_active = 0 WHERE user_id = ?",
            (user_id,)
        )
        cursor = conn.execute(
            """INSERT INTO study_plans
               (user_id, exam_name, exam_date, subjects_json, daily_hours, schedule_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, exam_name, exam_date,
             json.dumps(subjects), daily_hours, json.dumps(schedule))
        )
        return cursor.lastrowid


def get_active_study_plan(user_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute(
            """SELECT * FROM study_plans
               WHERE user_id = ? AND is_active = 1
               ORDER BY created_at DESC LIMIT 1""",
            (user_id,)
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["subjects"]  = json.loads(d["subjects_json"])
    d["schedule"]  = json.loads(d["schedule_json"])
    return d


def get_all_study_plans(user_id: int) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM study_plans WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["subjects"] = json.loads(d["subjects_json"])
        d["schedule"] = json.loads(d["schedule_json"])
        result.append(d)
    return result


# ─────────────────────────────────────────────
# ANALYTICS EVENTS
# ─────────────────────────────────────────────

def log_analytics_event(
    user_id: int,
    event_type: str,
    subject: str = "",
    score: float = None,
    duration_min: float = 0,
    metadata: Dict = None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO analytics
               (user_id, event_type, subject, score, duration_min, metadata_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, event_type, subject, score, duration_min,
             json.dumps(metadata or {}))
        )


def get_study_summary(user_id: int) -> Dict:
    """
    Aggregated stats for the dashboard:
    total quizzes, avg score, total study minutes, flashcards reviewed.
    """
    with get_connection() as conn:
        quiz_row = conn.execute(
            """SELECT COUNT(*) as count, AVG(score) as avg_score
               FROM quiz_scores WHERE user_id = ?""",
            (user_id,)
        ).fetchone()

        time_row = conn.execute(
            """SELECT SUM(duration_min) as total_min
               FROM analytics WHERE user_id = ?""",
            (user_id,)
        ).fetchone()

        flash_row = conn.execute(
            """SELECT SUM(times_reviewed) as total
               FROM flashcards WHERE user_id = ?""",
            (user_id,)
        ).fetchone()

        pdf_row = conn.execute(
            "SELECT COUNT(*) as count FROM pdfs WHERE user_id = ?",
            (user_id,)
        ).fetchone()

    return {
        "quizzes_taken":      quiz_row["count"] or 0,
        "avg_quiz_score":     round(quiz_row["avg_score"] or 0, 1),
        "total_study_min":    round(time_row["total_min"] or 0, 0),
        "flashcards_reviewed": flash_row["total"] or 0,
        "pdfs_uploaded":      pdf_row["count"] or 0,
    }


def get_daily_activity(user_id: int, days: int = 30) -> List[Dict]:
    """Returns study activity per day — used for calendar heatmap."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT DATE(recorded_at) as day,
                      COUNT(*) as events,
                      SUM(duration_min) as minutes
               FROM analytics
               WHERE user_id = ?
                 AND recorded_at >= datetime('now', '-{} days')
               GROUP BY day
               ORDER BY day ASC""".format(days),
            (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────
# AUDIO SUMMARIES
# ─────────────────────────────────────────────

def save_audio_summary(
    user_id: int,
    summary_text: str,
    audio_file_path: str,
    title: str = "Audio Summary",
    pdf_id: int = None,
    duration_sec: int = 0,
    language: str = "en",
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO audio_summaries
               (user_id, pdf_id, title, summary_text, audio_file_path, duration_sec, language)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, pdf_id, title, summary_text, audio_file_path, duration_sec, language)
        )
        return cursor.lastrowid


def get_audio_summaries(user_id: int) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT a.*, p.filename as pdf_filename
               FROM audio_summaries a
               LEFT JOIN pdfs p ON p.id = a.pdf_id
               WHERE a.user_id = ?
               ORDER BY a.created_at DESC""",
            (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def delete_audio_summary(user_id: int, summary_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM audio_summaries WHERE id = ? AND user_id = ?",
            (summary_id, user_id)
        )


# ─────────────────────────────────────────────
# LEADERBOARD
# ─────────────────────────────────────────────

def refresh_leaderboard_for_user(user_id: int) -> None:
    """
    Rebuild leaderboard cache entry for a single user.
    Called automatically after every quiz score save.
    """
    with get_connection() as conn:
        row = conn.execute(
            """SELECT u.username,
                      COUNT(qs.id)    as quizzes_taken,
                      SUM(qs.score)   as total_score,
                      AVG(qs.score)   as avg_score
               FROM users u
               LEFT JOIN quiz_scores qs ON qs.user_id = u.id
               WHERE u.id = ?
               GROUP BY u.id""",
            (user_id,)
        ).fetchone()

        if not row:
            return

        # Best subject
        subj_row = conn.execute(
            """SELECT q.subject, AVG(qs.score) as avg
               FROM quiz_scores qs
               JOIN quizzes q ON q.id = qs.quiz_id
               WHERE qs.user_id = ?
               GROUP BY q.subject
               ORDER BY avg DESC
               LIMIT 1""",
            (user_id,)
        ).fetchone()

        best_subject = subj_row["subject"] if subj_row else ""

        # Upsert leaderboard cache
        conn.execute(
            """INSERT INTO leaderboard_cache
               (user_id, username, total_score, quizzes_taken, avg_score, best_subject, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
               ON CONFLICT(user_id) DO UPDATE SET
                 username=excluded.username,
                 total_score=excluded.total_score,
                 quizzes_taken=excluded.quizzes_taken,
                 avg_score=excluded.avg_score,
                 best_subject=excluded.best_subject,
                 updated_at=excluded.updated_at""",
            (
                user_id, row["username"],
                round(row["total_score"] or 0, 2),
                row["quizzes_taken"] or 0,
                round(row["avg_score"] or 0, 2),
                best_subject,
            )
        )

    # Recalculate ranks for everyone
    _update_ranks()


def _update_ranks() -> None:
    """Recompute rank column for all users based on avg_score."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT user_id FROM leaderboard_cache ORDER BY avg_score DESC, total_score DESC"
        ).fetchall()
        for rank, row in enumerate(rows, start=1):
            conn.execute(
                "UPDATE leaderboard_cache SET rank = ? WHERE user_id = ?",
                (rank, row["user_id"])
            )


def get_leaderboard(limit: int = 20) -> List[Dict]:
    """Returns top N students sorted by rank."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM leaderboard_cache
               ORDER BY rank ASC
               LIMIT ?""",
            (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_user_rank(user_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM leaderboard_cache WHERE user_id = ?",
            (user_id,)
        ).fetchone()
    return dict(row) if row else None


# ─────────────────────────────────────────────
# RAG UTILITY — cosine similarity search
# ─────────────────────────────────────────────

def find_similar_chunks(
    query_embedding: List[float],
    user_id: int,
    pdf_id: int = None,
    top_k: int = 3,
) -> List[Dict]:
    """
    Pure-Python cosine similarity search over stored embeddings.
    No external vector DB required.

    Returns top_k chunks with keys: chunk_text, page_number, similarity
    """
    chunks = get_chunks_with_embeddings(user_id, pdf_id)
    if not chunks:
        return []

    q = np.array(query_embedding, dtype=np.float32)
    q_norm = np.linalg.norm(q)
    if q_norm == 0:
        return []

    scored = []
    for c in chunks:
        v = np.array(c["embedding"], dtype=np.float32)
        v_norm = np.linalg.norm(v)
        if v_norm == 0:
            continue
        sim = float(np.dot(q, v) / (q_norm * v_norm))
        scored.append({
            "chunk_text":  c["chunk_text"],
            "page_number": c["page_number"],
            "similarity":  sim,
        })

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_k]


# ─────────────────────────────────────────────
# DATABASE MAINTENANCE
# ─────────────────────────────────────────────

def get_db_stats() -> Dict:
    """Admin overview — row counts for each table."""
    tables = [
        "users", "chat_history", "pdfs", "pdf_chunks",
        "quizzes", "quiz_scores", "flashcards",
        "study_plans", "analytics", "audio_summaries",
        "leaderboard_cache",
    ]
    stats = {}
    with get_connection() as conn:
        for t in tables:
            row = conn.execute(f"SELECT COUNT(*) as cnt FROM {t}").fetchone()
            stats[t] = row["cnt"]
    return stats


def rebuild_full_leaderboard() -> None:
    """Full rebuild — call after restoring a backup or bulk import."""
    with get_connection() as conn:
        user_ids = [r["id"] for r in conn.execute("SELECT id FROM users").fetchall()]
    for uid in user_ids:
        refresh_leaderboard_for_user(uid)


# ─────────────────────────────────────────────
# ENTRY POINT (for testing / first run)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    create_tables()

    # Quick smoke test
    result = register_user("testuser", "test@example.com", "password123", "Test User")
    print("Register:", result)

    auth = login_user("testuser", "password123")
    print("Login:", auth["success"], auth["user"]["username"] if auth["success"] else auth["error"])

    stats = get_db_stats()
    print("DB Stats:", stats)