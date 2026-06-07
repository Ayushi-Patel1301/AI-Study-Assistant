import sqlite3

# =========================
# CONNECTION
# =========================
def create_connection():
    conn = sqlite3.connect("study_assistant.db")
    return conn


# =========================
# USERS TABLE
# =========================
def create_users_table():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

    print("Users table created successfully!")


# =========================
# DEFAULT USER
# =========================
def create_default_user():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO users (id, name, email, password_hash)
    VALUES (1, 'Demo User', 'demo@app.com', 'none')
    """)

    conn.commit()
    conn.close()

    print("Default user ready!")


# =========================
# DOCUMENTS TABLE
# =========================
def create_documents_table():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT DEFAULT 'pdf',
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    conn.commit()
    conn.close()

    print("Documents table created successfully!")


# =========================
# CHAT HISTORY TABLE
# =========================
def create_chat_history_table():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        response TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    conn.commit()
    conn.close()

    print("Chat history table created successfully!")


# =========================
# FLASHCARDS TABLE
# =========================
def create_flashcards_table():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS flashcards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        front TEXT NOT NULL,
        back TEXT NOT NULL,
        topic TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    conn.commit()
    conn.close()

    print("Flashcards table created successfully!")


# =========================
# QUIZZES TABLE
# =========================
def create_quizzes_table():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        topic TEXT NOT NULL,
        questions_json TEXT NOT NULL,
        score INTEGER DEFAULT NULL,
        total_marks INTEGER DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    conn.commit()
    conn.close()

    print("Quizzes table created successfully!")


# =========================
# STUDY PLANNER TABLE
# =========================
def create_study_planner_table():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS study_planner (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        task_title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    conn.commit()
    conn.close()

    print("Study planner table created successfully!")


# =========================
# MAIN EXECUTION
# =========================
if __name__ == "__main__":
    create_users_table()
    create_default_user()
    create_documents_table()
    create_chat_history_table()
    create_flashcards_table()
    create_quizzes_table()
    create_study_planner_table()