# app/models/notifications.py

from app.models import get_db


def create_notification(user_id, type, message, link=None):
    """Creates a new notification"""
    db = get_db()
    db.execute(
        """
        INSERT INTO notifications (user_id, type, message, link)
                        VALUES (?,?,?,?)""",
        (user_id, type, message, link),
    )
    db.commit()
    # emit real-time even to the user's room
    try:
        from app.sockets import socketio

        socketio.emit(
            "notification",
            {
                "message": message,
                "link": link or "/notifications/",
                "type": type,
            },
            room=f"user_{user_id}",
        )
    except Exception:
        pass


def get_notification(user_id):
    """Return all notifications for user, newest first"""
    db = get_db()
    return db.execute(
        """
        SELECT notifications.*
               FROM notifications
               WHERE user_id = ?
               ORDER BY created_at DESC
        """,
        (user_id,),
    ).fetchall()


def get_unread_count(user_id):
    """Return a total number of unread notifications for a user"""
    db = get_db()
    return db.execute(
        "SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read = 0", (user_id,)
    ).fetchone()[0]


def mark_all_read(user_id):
    """Mark all notificiations as read for a user"""
    db = get_db()
    db.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
    db.commit()


def notify_mentions(body, post_id, author_id, author_username=None):
    from app.utils.sanitize import extract_mentions
    from app.models.user import get_user_by_username

    usernames = extract_mentions(body)
    for username in usernames:
        user = get_user_by_username(username)
        if not user:
            continue
        if user["id"] == author_id:
            continue

        create_notification(
            user_id=user["id"],
            type="mention",
            message=f"@{author_username} mentioned you in a post",
            link=f"/posts/{post_id}",
        )
