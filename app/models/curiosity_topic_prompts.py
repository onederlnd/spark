# app/models/curiosity_topic_prompts.py

from app.models import get_db


def get_topic_prompt(topic_key):
    """
    Fetch the stored system prompt for a given topic key.
    Returns None if no override exists — caller falls back to BASE_PROMPT.
    """
    db = get_db()
    return db.execute(
        "SELECT * FROM curiosity_topic_prompts WHERE topic_key = ?",
        (topic_key,),
    ).fetchone()


def save_topic_prompt(topic_key, prompt_text, created_by):
    """
    Insert or replace a teacher-written system prompt for a topic.
    Allows teachers to customize how Curiosity talks about their subject.
    """
    db = get_db()
    db.execute(
        """
        INSERT OR REPLACE INTO curiosity_topic_prompts
            (topic_key, prompt_text, created_by)
        VALUES (?, ?, ?)
        """,
        (topic_key, prompt_text, created_by),
    )
    db.commit()


def delete_topic_prompt(topic_key):
    """
    Remove a topic prompt override.
    Reverts Curiosity back to BASE_PROMPT for this topic.
    """
    db = get_db()
    db.execute(
        "DELETE FROM curiosity_topic_prompts WHERE topic_key = ?",
        (topic_key,),
    )
    db.commit()
