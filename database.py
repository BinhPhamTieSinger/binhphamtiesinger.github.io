# database.py
import sqlite3
import os

DATABASE_FILE = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn

def init_db():
    if not os.path.exists(DATABASE_FILE):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                oauth_provider TEXT,
                oauth_id TEXT,
                avatar_url TEXT DEFAULT '/static/assets/images/default-avatar.png',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date_created DATE NOT NULL,
                description TEXT NOT NULL, -- Full markdown description
                short_description TEXT NOT NULL,
                type TEXT NOT NULL, -- 'current' or 'future'
                image_url TEXT,
                author_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Create project_comments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                comment_text TEXT NOT NULL,
                parent_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (parent_id) REFERENCES project_comments (id) ON DELETE CASCADE
            )
        """)

        # Create project_reactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                reaction_type TEXT NOT NULL, -- e.g., 'like', 'love', 'wow'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (project_id, user_id), -- A user can only have one reaction per project
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # --- NEW: Password Reset Tokens Table ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        conn.close()
        print(f"Database '{DATABASE_FILE}' initialized with all tables.")
    else:
        print(f"Database '{DATABASE_FILE}' already exists.")

if __name__ == "__main__":
    init_db()