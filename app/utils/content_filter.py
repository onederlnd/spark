import re
from better_profanity import profanity
from app.models import get_db

profanity.load_censor_words()


def get_custom_words():
    """Return teacher-added words from the database"""
    db = get_db()
    rows = db.execute("SELECT word FROM filtered_words").fetchall()
    return [r["word"].lower() for r in rows]


def get_filtered_words():
    """Return all filtered words from the database"""
    db = get_db()
    rows = db.execute("SELECT word FROM filtered_words").fetchall()
    return [r["word"].lower() for r in rows]


def check_content(text, user_id=None):
    """Check text against filtered word list. Returns list of matched words, empty list if clean"""
    if not text:
        return []

    matched = []
    text_lower = text.lower()

    if profanity.contains_profanity(text):
        matched.append("profanity detected")
        db = get_db()
        db.execute(
            "INSERT INTO filter_hits (word, user_id, context) VALUES (?, ?, ?)",
            ("profanity detected", user_id, text[:200]),
        )
        db.commit()

    custom_words = get_custom_words()
    for word in custom_words:
        pattern = r"\b" + re.escape(word) + r"\b"
        if re.search(pattern, text_lower):
            matched.append(word)
            db = get_db()
            db.execute(
                "INSERT INTO filter_hits (word, user_id, context) VALUES (?, ?, ?)",
                (word, user_id, text[:200]),
            )
            db.commit()

    return matched


def add_word(word, user_id):
    db = get_db()
    try:
        db.execute(
            "INSERT INTO filtered_words (word, added_by) VALUES (?, ?)",
            (word.lower().strip(), user_id),
        )
        db.commit()
        return True
    except Exception:
        return False


def remove_word(word):
    """Remove a word from the filter list"""
    db = get_db()
    db.execute("DELETE FROM filtered_words WHERE word = ?", (word.lower().strip(),))
    db.commit()


def get_all_words():
    """Return custom words from database for di splay in the filter management UI"""
    db = get_db()
    rows = db.execute(
        "SELECT word, added_by, created_at FROM filtered_words ORDER BY created_at DESC"
    ).fetchall()
    return rows
