# app/models/reactions.py

from app.models import get_db
from datetime import datetime, timezone

VALID_REACTIONS = {"lit", "thinking", "question", "like"}

REACTION_EMOJI = {
    "lit": "🔥",
    "thinking": "💡",
    "question": "🤔",
    "like": "❤️",
}


def add_or_update_reaction(post_id, user_id, reaction):
    """Add or Update a users reaction depending on if it already has a reaction or not."""
    if reaction not in VALID_REACTIONS:
        return False
    db = get_db()
    existing = db.execute(
        "SELECT reaction FROM reactions WHERE post_id=? AND user_id=?",
        (post_id, user_id),
    ).fetchone()

    if existing:
        if existing["reaction"] == reaction:
            db.execute(
                "DELETE FROM reactions WHERE post_id=? AND user_id=?",
                (post_id, user_id),
            )
            db.commit()
            return None
        else:
            db.execute(
                "UPDATE reactions SET reaction=?, created_at=? WHERE post_id=? AND user_id=?",
                (reaction, datetime.now(timezone.utc).isoformat(), post_id, user_id),
            )
            db.commit()
            return reaction
    else:
        db.execute(
            "INSERT INTO reactions (post_id, user_id, reaction, created_at) VALUES (?,?,?,?)",
            (post_id, user_id, reaction, datetime.now(timezone.utc).isoformat()),
        )
        db.commit()
        return reaction


def get_reaction(post_id, user_id):
    """Returns the raction string the user left, or None"""
    db = get_db()
    row = db.execute(
        "SELECT reaction FROM reactions WHERE post_id=? AND user_id=?",
        (post_id, user_id),
    ).fetchone()
    return row["reaction"] if row else None


def get_reaction_counts(post_id):
    """Return dict of reaction (count for teacher dashboard)"""
    db = get_db()
    rows = db.execute(
        "SELECT reaction, COUNT(*) as count FROM reactions WHERE post_id=? GROUP BY reaction",
        (post_id,),
    ).fetchall()
    counts = {r: 0 for r in VALID_REACTIONS}
    for row in rows:
        counts[row["reaction"]] = row["count"]
    return counts
