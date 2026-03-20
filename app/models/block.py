from app.models import get_db


def block_user(blocker_id, blocked_id):
    """Block a user. Returns else if the user is already blocked"""
    db = get_db()
    existing = db.execute(
        "SELECT 1 FROM blocks WHERE blocker_id = ? AND blocked_id = ?",
        (
            blocker_id,
            blocked_id,
        ),
    ).fetchone()

    if existing:
        return False

    db.execute(
        "INSERT INTO blocks (blocked_id, blocker_id) VALUES (?,?)",
        (blocked_id, blocker_id),
    )
    db.commit()
    return True


def unblock_user(blocker_id, blocked_id):
    db = get_db()
    db.execute(
        "DELETE FROM blocks WHERE blocker_id = ? AND blocked_id = ?",
        (blocker_id, blocked_id),
    )
    db.commit()


def is_blocked(blocker_id, blocked_id):
    """Check if a user is blocked"""
    db = get_db()
    return (
        db.execute(
            "SELECT 1 FROM blocks WHERE blocker_id = ? AND blocked_id = ?",
            (blocker_id, blocked_id),
        ).fetchone()
        is not None
    )


def get_blocked_ids(user_id):
    """Return list of user IDs taht this user has blocked"""
    db = get_db()
    rows = db.execute(
        "SELECT blocked_id FROM blocks WHERE blocker_id = ?",
        (user_id,),
    ).fetchall()
    return [r["blocked_id"] for r in rows]
