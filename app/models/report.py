# app/models/report.py

from app.models import get_db
from app.models.post import hide_post


def create_report(post_id, user_id, reason, description):
    db = get_db()

    if prevent_duplicate_reports(post_id, user_id):
        return None
    cursor = db.execute(
        "INSERT INTO reports "
        "(post_id, reported_by_user_id, reason, description, status) "
        "VALUES (?, ?, ?, ?, 'pending')",
        (post_id, user_id, reason, description),
    )

    db.commit()

    if get_report_count(post_id) >= 3:
        hide_post(post_id)

    return cursor.lastrowid


def get_reports_for_classroom(classroom_id):
    db = get_db()

    return db.execute(
        """
        SELECT posts.id as post_id,
                posts.body,
                posts.user_id as author_id,
                author.username as author_username,
                COUNT(reports.id) as report_count,
                MAX(reports.created_at) as last_reported_at
            FROM reports
            JOIN posts ON reports.post_id = posts.id
            JOIN users AS author ON posts.user_id = author.id
            WHERE posts.classroom_id = ?
            AND reports.status = 'pending'
            GROUP BY posts.id
            ORDER BY last_reported_at DESC
        """,
        (classroom_id,),
    ).fetchall()


def get_reports_for_post(post_id):
    db = get_db()

    return db.execute(
        """
        SELECT reports.*, users.username, posts.body, posts.id
            FROM reports
            JOIN users ON reports.reported_by_user_id = users.id
            JOIN posts ON reports.post_id = posts.id
            WHERE reports.post_id = ?
            ORDER BY reports.created_at DESC
        """,
        (post_id,),
    ).fetchall()


def prevent_duplicate_reports(post_id, user_id):
    db = get_db()

    existing = db.execute(
        """
        SELECT 1 FROM reports
        WHERE post_id = ? AND reported_by_user_id = ?
        """,
        (post_id, user_id),
    ).fetchone()

    return existing is not None


def resolve_reports(post_id, teacher_id, status):
    db = get_db()
    db.execute(
        """
        UPDATE reports
        SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
        WHERE post_id = ? AND status = 'pending'
        """,
        (status, teacher_id, post_id),
    )

    db.commit()


def get_report_count(post_id):
    db = get_db()

    return db.execute(
        "SELECT COUNT(*) FROM reports WHERE post_id = ?",
        (post_id,),
    ).fetchone()[0]


def auto_flag_post(post_id, matched_words):
    """Auto-flag a post that matched the content filter.
    Creates a system report and hides the post for teacher review."""
    db = get_db()
    reason = "Auto-flagged by content filter"
    description = f"Matched words: {', '.join(matched_words)}"

    db.execute(
        "INSERT INTO reports "
        "(post_id, reported_by_user_id, reason, description, status) "
        "VALUES (?, NULL, ?, ?, 'pending')",
        (post_id, reason, description),
    )
    db.commit()
    hide_post(post_id)
