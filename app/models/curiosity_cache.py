from app.models import get_db

CACHE_TTL_DAYS = 30


def get_cached_response(topic_key, question_hash):
    """
    First stop in the Curiosity pipeline.
    Returns a cache row or None — a hit skips the Claude API call entirely.
    """
    db = get_db()
    row = db.execute(
        """
        SELECT * FROM curiosity_cache
        WHERE topic_key = ?
        AND question_hash = ?
        AND (julianday('now') - julianday(cached_at)) < ?
        """,
        (topic_key, question_hash, CACHE_TTL_DAYS),
    ).fetchone()

    if row:
        db.execute(
            "UPDATE curiosity_cache SET hit_count = hit_count + 1 WHERE id = ?",
            (row["id"],),
        )
        db.commit()

    return row


def save_cached_response(topic_key, question_hash, question_text, response_text):
    """
    Store a Claude response after a live API call.
    Only call this after the response passes the quality check.
    """
    db = get_db()
    db.execute(
        """
        INSERT OR REPLACE INTO curiosity_cache
            (topic_key, question_hash, question_text, response_text, hit_count, cached_at)
        VALUES (?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
        """,
        (topic_key, question_hash, question_text, response_text),
    )
    db.commit()


def invalidate_cache_entry(cache_id):
    """
    Hard delete a cache entry by ID.
    Forces the next matching question to go live to Claude.
    """
    db = get_db()
    db.execute("DELETE FROM curiosity_cache WHERE id = ?", (cache_id,))
    db.commit()


def get_cache_entries_by_topic(topic_key):
    """
    Return all cached entries for a topic.
    Used by teacher review dashboard and social suggestion layer.
    """
    db = get_db()
    return db.execute(
        """
        SELECT * FROM curiosity_cache
        WHERE topic_key = ?
        ORDER BY hit_count DESC
        """,
        (topic_key,),
    ).fetchall()


def record_feedback(cache_id, signal):
    """
    Store a single thumbs up/down against a cached response.
    No user_id — anonymous by design, COPPA-clean.
    """
    db = get_db()
    db.execute(
        "INSERT INTO curiosity_cache_feedback (cache_id, signal) VALUES (?, ?)",
        (cache_id, signal),
    )
    db.commit()


def get_feedback_summary(cache_id):
    """
    Return aggregate feedback counts for a cache entry.
    # Returns dict: {positive: int, negative: int}
    """
    db = get_db()
    result = db.execute(
        """
        SELECT
            SUM(CASE WHEN signal = 'positive' THEN 1 ELSE 0 END) AS positive,
            SUM(CASE WHEN signal = 'negative' THEN 1 ELSE 0 END) AS negative
        FROM curiosity_cache_feedback
        WHERE cache_id = ?
        """,
        (cache_id,),
    ).fetchone()

    return {
        "positive": result["positive"] or 0,
        "negative": result["negative"] or 0,
    }
