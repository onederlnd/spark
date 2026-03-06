# app/models/__init__.py
import os
import sqlite3
from flask import g, current_app

sqlite3.register_adapter(bool, int)
sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))


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
        """)
        db.commit()
