from app.models import get_db

PER_PAGE = 20


def get_assignments(user_id, page=1):
    """Returns assignments for feed.index"""
    db = get_db()
    offset = (page - 1) * PER_PAGE
    limit = PER_PAGE + 1

    rows = db.execute(
        """
        SELECT
            a.id,
            a.title,
            a.instructions,
            a.due_date,
            a.classroom_id,
            a.post_id,
            c.name AS classroom_name,
            CASE WHEN s.id IS NOT NULL THEN 1 ELSE 0 END AS turned_in,
            s.submitted_at,
            CASE WHEN s.grade IS NOT NULL THEN 1 ELSE 0 END AS graded,
            s.grade,
            s.feedback
        FROM assignments a
        JOIN classrooms c ON c.id = a.classroom_id
        LEFT JOIN submissions s
            ON s.assignment_id = a.id AND s.user_id = ?
        WHERE
            (
                EXISTS (
                    SELECT 1 FROM classroom_members cm
                    WHERE cm.classroom_id = a.classroom_id
                        AND cm.user_id = ?
                )
                OR c.teacher_id = ?
            )
        ORDER BY
            CASE WHEN s.id IS NOT NULL THEN 1 ELSE 0 END ASC,
            CASE WHEN a.due_date IS NULL THEN 1 ELSE 0 END ASC,
            a.due_date ASC,
            a.id DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, user_id, user_id, limit, offset),
    ).fetchall()

    has_next = len(rows) == limit
    return [dict(r) for r in rows[:PER_PAGE]], has_next
