# database.py
import sqlite3
import os
from datetime import datetime # Import datetime for default timestamps

DATABASE_FILE = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # --- Existing Tables (Ensuring they are created if they don't exist) ---
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

    # --- NEW FORUM TABLES ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forum_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            display_order INTEGER NOT NULL UNIQUE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forum_boards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            display_order INTEGER NOT NULL,
            FOREIGN KEY (category_id) REFERENCES forum_categories (id) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forum_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            views INTEGER DEFAULT 0,
            FOREIGN KEY (board_id) REFERENCES forum_boards (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forum_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            post_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (topic_id) REFERENCES forum_topics (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            user_ip TEXT NOT NULL,
            last_viewed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (topic_id) REFERENCES forum_topics (id) ON DELETE CASCADE,
            UNIQUE(topic_id, user_ip)
        );
    """)

    # Add notifications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,  -- 'mention', 'reply', etc.
            content TEXT NOT NULL,
            link TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source_id INTEGER,  -- ID of the post/comment that triggered notification
            source_type TEXT,   -- 'forum_post', 'project_comment', etc.
            source_user_id INTEGER, -- User who triggered the notification
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (source_user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)

    conn.commit()

    # Now, only close the connection after ensuring all queries are done
    conn.close()

    # Optional: Initial data for forum categories and boards if the DB is new
    # if not os.path.exists(DATABASE_FILE):
    _insert_initial_forum_data()


def _insert_initial_forum_data():
    """Inserts initial categories and boards if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if categories exist
        if cursor.execute("SELECT COUNT(*) FROM forum_categories WHERE name = 'Community'").fetchone()[0] == 0:
            cursor.execute("INSERT INTO forum_categories (name, display_order) VALUES (?, ?)", ("Community", 1))
            community_id = cursor.lastrowid
            cursor.execute("INSERT INTO forum_categories (name, display_order) VALUES (?, ?)", ("Developer", 2))
            developer_id = cursor.lastrowid

            # Insert boards for Community
            cursor.execute("INSERT INTO forum_boards (category_id, name, description, display_order) VALUES (?, ?, ?, ?)",
                           (community_id, "Townhall", "Discuss forum policy and announce your games/kickstarters here.", 1))
            cursor.execute("INSERT INTO forum_boards (category_id, name, description, display_order) VALUES (?, ?, ?, ?)",
                           (community_id, "DevLogs", "This forum is for charting your game's progress with a development log.", 2))
            cursor.execute("INSERT INTO forum_boards (category_id, name, description, display_order) VALUES (?, ?, ?, ?)",
                           (community_id, "Jams & Events", "Organizing meetups and hangouts with your fellow indies!", 3))

            # Insert boards for Developer
            cursor.execute("INSERT INTO forum_boards (category_id, name, description, display_order) VALUES (?, ?, ?, ?)",
                           (developer_id, "Playtesting", "Developers, post your games here for critical feedback about bugs and design.", 1))
            cursor.execute("INSERT INTO forum_boards (category_id, name, description, display_order) VALUES (?, ?, ?, ?)",
                           (developer_id, "Art", "Graphics, visuals and pictures!", 2))
            cursor.execute("INSERT INTO forum_boards (category_id, name, description, display_order) VALUES (?, ?, ?, ?)",
                           (developer_id, "Audio", "Music and sound design for games", 3))

            conn.commit()
            print("Initial forum categories and boards inserted.")
    except Exception as e:
        conn.rollback()
        print(f"Error inserting initial forum data: {e}")
    finally:
        conn.close()



if __name__ == "__main__":
    init_db()
    # You might want to remove the specific `if __name__ == "__main__":` block for init_db
    # in a larger application and ensure `init_db()` is called once during app startup.