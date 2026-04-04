# app/models/user.py

import sqlite3
import bcrypt
import secrets

from functools import wraps
from app.models import get_db
from app.models.notifications import create_notification
from app.utils.coppa import is_coppa_approved
from flask import current_app, session, redirect, url_for, flash
from datetime import datetime


def calculate_age(dob):

    today = datetime.today()

    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def notify_teachers_coppa_pending(student):
    db = get_db()

    teachers = db.execute("SELECT id FROM users WHERE role='teacher'").fetchall()

    for teacher in teachers:
        create_notification(
            user_id=teacher["id"],
            message=f"{student['username']} has pending COPPA approval",
            type="coppa",
            link="/auth/coppa/approve",
        )


def coppa_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            flash("You must be logged in", "error")
            return redirect(url_for("auth.login"))

        user = get_user_by_id(user_id)
        if not is_coppa_approved(user):
            flash("Your account is restricted until COPPA approval", "warning")
            return redirect(url_for("auth.coppa_notice"))
        return f(*args, **kwargs)

    return decorated_function


def create_user(username, password, bio="", role="student", dob=None, email=None):
    if dob is None:
        return False, "Date of birth required"

    db = get_db()
    rounds = current_app.config.get("BCRYPT_ROUNDS", 12)

    try:
        dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
    except ValueError:
        return False, "Invalid date format, must be YYYY-MM-DD"

    # Determine COPPA status
    age = calculate_age(dob_date)
    coppa_status = "pending" if age < 13 else "approved"

    dob_str = dob_date.isoformat()

    password_hash = bcrypt.hashpw(
        password.encode(), bcrypt.gensalt(rounds=rounds)
    ).decode()
    try:
        db.execute(
            "INSERT INTO users "
            "(username, email, password_hash, dob, bio, role, coppa_status, onboarded) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (username, email, password_hash, dob_str, bio, role, coppa_status, 0),
        )
        db.commit()
        if role == "student" and coppa_status == "pending":
            student = get_user_by_username(username)
            notify_teachers_coppa_pending(student)
        return True, None
    except sqlite3.IntegrityError:
        return False, "Username already taken"


def get_user_by_username(username):
    db = get_db()
    return db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def get_user_by_id(user_id):
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_user_by_email(email):
    db = get_db()
    return db.execute(
        "SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email,)
    ).fetchone()


def check_password(username, password):
    user = get_user_by_username(username)
    if not user:
        return None
    if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return user
    return None


def update_user_password(user_id, new_password):
    """Update a user's password with bcrypt hash"""
    from flask import current_app

    rounds = current_app.config.get("BCRYPT_ROUNDS", 12)
    password_hash = bcrypt.hashpw(
        new_password.encode(), bcrypt.gensalt(rounds=rounds)
    ).decode()
    db = get_db()
    db.execute("UPDATE users SET password_hash=? WHERE id=?", (password_hash, user_id))
    db.commit()


# --- following
def follow_user(follower_id, followed_id):
    """Insert a follow relationship, returns False if already following"""
    db = get_db()
    try:
        db.execute(
            "INSERT INTO follows (follower_id, followed_id) VALUES (?, ?)",
            (follower_id, followed_id),
        )
        db.commit()
        return True
    except Exception:
        # composite PK prevents duplicates
        return False


def unfollow_user(follower_id, followed_id):
    """Removes a follow relationship"""
    db = get_db()
    db.execute(
        "DELETE FROM follows WHERE follower_id=? AND followed_id=?",
        (follower_id, followed_id),
    )
    db.commit()


def is_following(follower_id, followed_id):
    """Returns True if follower_id follows followed_id"""
    db = get_db()
    result = db.execute(
        "SELECT 1 FROM follows WHERE follower_id=? AND followed_id=?",
        (follower_id, followed_id),
    ).fetchone()
    return result is not None


def get_followers_count(user_id):
    """Returns number of users following user_id"""
    db = get_db()
    return db.execute(
        "SELECT COUNT(*) FROM follows WHERE follower_id=?", (user_id,)
    ).fetchone()[0]


def get_following_count(user_id):
    """Returns the number of users user_id is following."""
    db = get_db()
    return db.execute(
        "SELECT COUNT(*) FROM follows WHERE followed_id=?", (user_id,)
    ).fetchone()[0]


# --- update bio
def update_user_bio(user_id, bio):
    db = get_db()
    db.execute("UPDATE users SET bio=? WHERE id=?", (bio, user_id))
    db.commit()


def get_db_followers(user_id):
    """Return list of users follow user_id"""
    db = get_db()
    return db.execute(
        """
        SELECT users.id, users.username, users.bio
                      FROM follows
                      JOIN users ON follows.follower_id = users.id
                      WHERE follows.followed_id = ?
                      ORDER BY users.username
                      """,
        (user_id,),
    ).fetchall()


def get_db_following(user_id):
    """Return list of users that user_id is following"""
    db = get_db()
    return db.execute(
        """
                      SELECT users.id, users.username, users.bio
                      FROM follows
                      JOIN users ON follows.followed_id = users.id
                      WHERE follows.follower_id = ?
                      ORDER BY users.username
                      """,
        (user_id,),
    ).fetchall()


def mark_onboarded(user_id):
    db = get_db()
    db.execute("UPDATE users SET onboarded = 1 WHERE id = ?", (user_id,))
    db.commit()


def generate_qr_token():
    return secrets.token_urlsafe(32)


def regenerate_qr_token(user_id):
    token = generate_qr_token()
    db = get_db()
    db.execute("UPDATE users SET qr_token = ? WHERE id = ?", (token, user_id))
    db.commit()
    return token
