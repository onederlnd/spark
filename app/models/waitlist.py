import sqlite3
from app.models import get_db
from datetime import datetime, timezone


def add_to_waitlist(email):
    db = get_db()
    try:
        db.execute(
            "INSERT INTO waitlist (email, joined_at) VALUES (?,?)",
            (email.lower(), datetime.now(timezone.utc).isoformat()),
        )
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False


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
