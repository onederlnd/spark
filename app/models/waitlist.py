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
