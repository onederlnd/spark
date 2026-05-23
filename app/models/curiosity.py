# app/models/curiosity.py

from app.models import get_db


def get_or_create_conversation(user_id, subject, area, category, topic, description):
    """Finds an existing converation for that user+topic or creates one"""
    db = get_db()
    result = db.execute(
        """
        SELECT * FROM curiosity_conversations WHERE user_id = ?
        AND subject = ?
        AND area = ?
        AND category = ?
        AND topic = ?
        """,
        (user_id, subject, area, category, topic),
    ).fetchone()

    if result:
        return result
    else:
        new_id = db.execute(
            """
            INSERT INTO curiosity_conversations (user_id, subject, area, category, topic, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, subject, area, category, topic, description),
        ).lastrowid
        db.commit()

        return db.execute(
            "SELECT * FROM curiosity_conversations WHERE id = ?", (new_id,)
        ).fetchone()


def get_messages(conversation_id):
    """Returns all messages in order"""
    db = get_db()
    result = db.execute(
        """
        SELECT * FROM curiosity_messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
        """,
        (conversation_id,),
    ).fetchall()
    return result


def save_message(conversation_id, role, content):
    """Saves new messages to the database."""
    db = get_db()
    result = db.execute(
        """
        INSERT INTO curiosity_messages (conversation_id, role, content)
        VALUES (?, ?, ?)
        """,
        (conversation_id, role, content),
    )
    db.commit()

    return result


def get_conversations(user_id):
    """Returns all conversations for a user, ordered by most recent."""
    db = get_db()
    results = db.execute(
        "SELECT * FROM curiosity_conversations WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    return results


def get_conversation(conversation_id):
    """Returns a single conversation by ID."""
    db = get_db()
    result = db.execute(
        "SELECT * FROM curiosity_conversations WHERE id = ?", (conversation_id,)
    ).fetchone()
    return result


def update_conversation_topic(
    conversation_id, subject, area, category, topic, description
):
    """Updates the topic fields on an existing conversation."""
    db = get_db()
    db.execute(
        """
        UPDATE curiosity_conversations
        SET
            subject = ?,
            area = ?,
            category = ?,
            topic = ?,
            description = ?
        WHERE id = ?
        """,
        (subject, area, category, topic, description, conversation_id),
    )

    db.commit()

    result = db.execute(
        "SELECT * FROM curiosity_conversations WHERE id = ?", (conversation_id,)
    ).fetchone()

    return result


def delete_conversation(conversation_id):
    """Deletes a conversation and all its messages via cascade."""
    db = get_db()
    db.execute("DELETE FROM curiosity_conversations WHERE id = ?", (conversation_id,))
    db.commit()


def get_active_topics_for_classroom(classroom_id):
    db = get_db()
    rows = db.execute(
        """
        SELECT DISTINCT cc.subject, cc.area, cc.category, cc.topic
        FROM curiosity_conversations cc
        JOIN classroom_members cm ON cm.user_id = cc.user_id
        WHERE cm.classroom_id = ?
        """,
        (classroom_id,),
    ).fetchall()
    return [dict(row) for row in rows]
