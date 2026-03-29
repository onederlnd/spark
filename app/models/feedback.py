# app/models/feedback.py

from app.models import get_db
from datetime import datetime, timezone


def submit_feedback(
    user_id,
    page_url,
    page_context,
    classroom_experience,
    student_engagement,
    ease_of_use,
    assignment_workflow,
    safety_moderation,
    open_suggestions,
):
    db = get_db()
    db.execute(
        """
        INSERT INTO feedback(
            user_id, page_url, page_context,
            classroom_experience, student_engagement, ease_of_use,
            assignment_workflow, safety_moderation, open_suggestions,
            created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            page_url,
            page_context,
            classroom_experience,
            student_engagement,
            ease_of_use,
            assignment_workflow,
            safety_moderation,
            open_suggestions,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    db.commit()


def get_all_feedback():
    db = get_db()
    return db.execute(
        """
        SELECT feedback.*, users.username
        FROM feedback
        JOIN users ON feedback.user_id = users.id
        ORDER BY feedback.created_at DESC
        """
    ).fetchall()


def get_feedback_summary():
    """Returns average ratings across all submissions"""
    db = get_db()
    return db.execute(
        """
        SELECT
            COUNT(*) as total,
            ROUND(AVG(classroom_experience), 1) as avg_classroom,
            ROUND(AVG(student_engagement), 1) as avg_engagement,
            ROUND(AVG(ease_of_use), 1) as avg_ease,
            ROUND(AVG(assignment_workflow), 1) as avg_assignments,
            ROUND(AVG(safety_moderation), 1) as avg_safety
        FROM feedback
        """
    ).fetchone()


def get_feedback_daily(days=30):
    """Returns daily average ratings for the trend chart."""
    db = get_db()
    return db.execute(
        """
        SELECT
            DATE(created_at) as day,
            COUNT(*) as submissions,
            ROUND(AVG(classroom_experience), 1) as avg_classroom,
            ROUND(AVG(student_engagement), 1)   as avg_engagement,
            ROUND(AVG(ease_of_use), 1)           as avg_ease,
            ROUND(AVG(assignment_workflow), 1)   as avg_assignments,
            ROUND(AVG(safety_moderation), 1)     as avg_safety
        FROM feedback
        WHERE created_at >= DATE('now', ? || ' days')
        ORDER BY day ASC
        """,
        (f"-{days}",),
    ).fetchall()
