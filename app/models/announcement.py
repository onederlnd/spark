from app.models import get_db

PER_PAGE = 20


def create_announcement(classroom_id, user_id, title, body):
    db = get_db()
    db.execute(
        """
        INSERT INTO posts (title, body, user_id, classroom_id, post_type, parent_id, is_hidden)
        VALUES (?, ?, ?, ?, 'announcement', NULL, 0)
        """,
        (title, body, user_id, classroom_id),
    )
    db.commit()


def get_announcements(user_id, page=1):
    """
    Return classroom announcements visibile to this user.
    Vislble requires the user to be a classroom_member
    OR the classroom's teacher.
    Announcements never appear in regular feed - they are only surfaced here.
    """
    db = get_db()
    offset = (page - 1) * PER_PAGE
    limit = PER_PAGE + 1

    rows = db.execute(
        """
        SELECT
            p.id, p.title, p.body, p.created_at, p.reply_count,
            u.username, u.avatar_emoji, u.avatar_bg,
            c.name AS classroom_name,
            c.id AS classroom_id
            FROM posts p
            JOIN users u ON u.id = p.user_id
            JOIN classrooms c ON c.id = p.classroom_id
            WHERE p.post_type = 'announcement'
                AND p.classroom_id IS NOT NULL
                AND p.is_hidden = 0
                AND p.parent_id IS NULL
                AND (
                    EXISTS (
                        SELECT 1 FROM classroom_members cm
                        WHERE cm.classroom_id = p.classroom_id
                            AND cm.user_id = ?)
                    OR c.teacher_id = ?
                )
            ORDER BY p.created_at DESC
            LIMIT ? OFFSET ?
        """,
        (user_id, user_id, limit, offset),
    ).fetchall()

    has_next = len(rows) == limit
    return [dict(r) for r in rows[:PER_PAGE]], has_next
