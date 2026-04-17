# app/models/waitlist.py
import sqlite3
import secrets
from app.models import get_db
from datetime import datetime, timezone


def add_to_waitlist(email):
    if not email or "@" not in email or "." not in email:
        return False, "Please enter a valid email address."
    db = get_db()
    email = email.lower()
    existing = db.execute(
        "SELECT verify_token FROM waitlist WHERE email = ?",
        (email,),
    ).fetchone()
    if existing and "verify_token" in existing.keys():
        return True, existing["verify_token"]

    token = secrets.token_urlsafe(32)

    try:
        db.execute(
            "INSERT INTO waitlist (email, joined_at, verified, verify_token) VALUES (?,?,?,?)",
            (email.lower(), datetime.now(timezone.utc).isoformat(), 0, token),
        )
        db.commit()
        return True, token
    except sqlite3.IntegrityError:
        return False, None


def get_waitlist_summary():
    """Total signups and conversion rate vs registered users."""
    db = get_db()
    return db.execute(
        """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN users.id IS NOT NULL THEN 1 END) as converted,
            ROUND(
                100.0 * COUNT(CASE WHEN users.id IS NOT NULL THEN 1 END)
                / MAX(COUNT(*), 1),
                1
            ) as conversion_rate
        FROM waitlist
        LEFT JOIN users ON LOWER(users.email) = waitlist.email
        """
    ).fetchone()


def get_waitlist_all():
    """All waitlist entries, newest first, with conversion status."""
    db = get_db()
    return db.execute(
        """
        SELECT
            waitlist.id,
            waitlist.email,
            waitlist.joined_at,
            waitlist.invited_at,
            CASE WHEN users.id IS NOT NULL THEN 1 ELSE 0 END as converted
        FROM waitlist
        LEFT JOIN users ON LOWER(users.email) = waitlist.email
        ORDER BY waitlist.joined_at DESC
        """
    ).fetchall()


def get_waitlist_daily(days=14):
    """Daily signup counts for the trend chart."""
    db = get_db()
    return db.execute(
        """
        SELECT
            DATE(joined_at) as day,
            COUNT(*) as count
        FROM waitlist
        WHERE joined_at >= DATE('now', ? || ' days')
        GROUP BY DATE(joined_at)
        ORDER BY day ASC
        """,
        (f"-{days}",),
    ).fetchall()


def verify_waitlist_email(token):
    """Mark the waitlist entery verified"""
    db = get_db()
    row = db.execute(
        "SELECT id, email FROM waitlist WHERE verify_token = ? AND verified = 0",
        (token,),
    ).fetchone()
    if not row:
        return None
    db.execute(
        "UPDATE waitlist SET verified = 1, verify_token = NULL WHERE id = ?",
        (row["id"],),
    )
    db.commit()
    return row["email"]
