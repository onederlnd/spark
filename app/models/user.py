# app/models/user.py

import sqlite3
import hashlib
from app.models import get_db


def create_user(username, password, bio=""):
    db = get_db()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        db.execute(
            "INSERT INTO users (username, password_hash, bio) VALUES (?, ?, ?)",
            (username, password_hash, bio),
        )
        db.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "Username already taken"


def get_user_by_username(username):
    db = get_db()
    return db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def get_user_by_id(user_id):
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def check_password(username, password):
    user = get_user_by_username(username)
    if not user:
        return None
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if user["password_hash"] == password_hash:
        return user
    return None
