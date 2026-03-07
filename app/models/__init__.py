# app/models/__init__.py
import os
import sqlite3
from datetime import datetime, timezone
from flask import g, current_app

sqlite3.register_adapter(bool, int)
sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))


def time_ago(dt_str):
    if not dt_str:
        return ""
    try:
        if isinstance(dt_str, str):
            dt = datetime.strptime(dt_str[:19], "%Y-%m-%d %H:%M:%S")
        else:
            dt = dt_str
        dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = now - dt
        seconds = int(diff.total_seconds())

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            m = seconds // 60
            return f"{m}m ago"
        elif seconds < 86400:
            h = seconds // 3600
            return f"{h}h ago"
        elif seconds < 604800:
            d = seconds // 86400
            return f"{d}d ago"
        else:
            return dt.strftime("%b %d, %Y")
    except Exception:
        return str(dt_str)


def get_db():
    if "db" not in g:
        db_path = current_app.config.get("DATABASE_URL", "devstack.db")
        # fmt: off
        if db_path.startswith("sqlite:///"):
            db_path = db_path[len("sqlite:///"):]
        # fmt: on
        if db_path != ":memory:" and not os.path.isabs(db_path):
            db_path = os.path.join(current_app.root_path, "..", db_path)
            db_path = os.path.abspath(db_path)

        g.db = sqlite3.connect(
            db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        sqlite3.register_converter("TIMESTAMP", lambda val: val.decode())
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    app.teardown_appcontext(close_db)

    with app.app_context():
        db = get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                bio TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topic_id INTEGER,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                votes INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                parent_id INTEGER DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(topic_id) REFERENCES topics(id),
                FOREIGN KEY(parent_id) REFERENCES posts(id)
            );

            CREATE TABLE IF NOT EXISTS votes (
                user_id INTEGER NOT NULL,
                post_id INTEGER NOT NULL,
                value INTEGER NOT NULL,
                PRIMARY KEY(user_id, post_id)
            );

            CREATE TABLE IF NOT EXISTS bookmarks (
                user_id INTEGER NOT NULL,
                post_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(user_id, post_id)
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts
                USING fts5(title, body, content=posts, content_rowid=10);

            CREATE VIRTUAL TABLE IF NOT EXISTS topics_fts
                USING fts5(name, description, content=topics, content_rowid=id);

            CREATE TABLE IF NOT EXISTS follows (
                follower_id INTEGER NOT NULL, -- user doing the following
                followed_id INTEGER NOT NULL, -- user being followed
                create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (follower_id, followed_id),
                FOREIGN KEY (follower_id) REFERENCES users(id),
                FOREIGN KEY (followed_id) REFERENCES users(id)
            );
        """)
        db.commit()
