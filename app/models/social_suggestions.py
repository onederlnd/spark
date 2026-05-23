# app/models/social_suggestions.py

from app.models import get_db


def get_trending_questions(topic_key, limit=5):
    """
    Return the most-asked questions for a topic based on cache hit count.
    Anonymized — question_text only, no user linkage.
    """
    db = get_db()
    return db.execute(
        """
        SELECT question_text FROM curiosity_cache
        WHERE topic_key = ?
        ORDER BY hit_count DESC
        LIMIT ?
        """,
        (topic_key, limit),
    ).fetchall()


def get_discussion_starters(topic_key):
    """
    Return pre-generated discussion prompts for a topic.
    Generated offline by teachers — never live per student request.
    """
    db = get_db()
    return db.execute(
        """
        SELECT * FROM curiosity_social_starters
        WHERE topic_key = ?
        ORDER BY created_at DESC
        """,
        (topic_key,),
    ).fetchall()


def save_discussion_starter(topic_key, prompt_text, created_by, classroom_id=None):
    """
    Store a teacher-approved discussion prompt for a topic.
    classroom_id is optional — None means platform-wide.
    """
    db = get_db()
    db.execute(
        """
        INSERT INTO curiosity_social_starters
            (topic_key, prompt_text, created_by, classroom_id)
        VALUES (?, ?, ?, ?)
        """,
        (topic_key, prompt_text, created_by, classroom_id),
    )
    db.commit()


def get_classmates_on_topic(topic_key, classroom_id):
    """
    Return a count of students active on this topic in a classroom.
    Never returns student identities — count only, COPPA-clean.
    """
    db = get_db()
    result = db.execute(
        """
        SELECT COUNT(DISTINCT cc.user_id) as student_count
        FROM curiosity_conversations cc
        JOIN classroom_members cm ON cc.user_id = cm.user_id
        WHERE cc.topic = ?
        AND cm.classroom_id = ?
        AND cc.classroom_id = ?
        """,
        (topic_key, classroom_id, classroom_id),
    ).fetchone()

    return result["student_count"] if result else 0
