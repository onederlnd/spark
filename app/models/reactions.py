# app/models/reactions.py

from app.models import get_db
from datetime import datetime, timezone

VALID_REACTIONS = {
    "love",
    "idea",
    "thinking",
    "nailed_it",
    "lit",
    "star",
    "fire",
}

REACTION_EMOJI = {
    "love": "❤️",
    "idea": "💡",
    "thinking": "🤔",
    "nailed_it": "🎯",
    "lit": "⚡",
    "star": "🌟",
    "fire": "🔥",
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


def get_reaction_users(post_id):
    db = get_db()
    rows = db.execute(
        """
        SELECT reactions.reaction, users.username
        FROM reactions
        JOIN users ON reactions.user_id = users.id
        WHERE reactions.post_id = ?
        ORDER BY reactions.created_at ASC
        """,
        (post_id,),
    ).fetchall()

    result = {}
    for row in rows:
        result.setdefault(row["reaction"], []).append(row["username"])
    return result


def format_reactor_names(usernames):
    """
    Return display names - first name only unless there's a duplicate, then first name + last initial.
    username format: firstname.lastname or demo.firstname.lastname
    """

    def parse(username):
        parts = username.split(".")

        if len(parts) >= 3 and parts[0] == "demo":
            return parts[1].capitalize(), parts[2][0].upper() if parts[2] else ""
        elif len(parts) >= 2:
            return parts[0].capitalize(), parts[1][0].upper() if parts[1] else ""
        return username.capitalize(), ""

    parsed = [parse(u) for u in usernames]

    first_names = [p[0] for p in parsed]
    result = []
    for first, last_initial in parsed:
        if first_names.count(first) > 1 and last_initial:
            result.append(f"{first} {last_initial}.")
        else:
            result.append(first)

    return result
