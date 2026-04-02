# app/models/parent.py

import secrets
from app.models import get_db


def generate_parent_invite_code(student_id, created_by):
    """Generate a unique invite code for a student. One active code per student"""
    db = get_db()
    code = secrets.token_urlsafe(8)
    db.execute(
        """
        INSERT INTO parent_invite_codes (student_id, code, created_by)
        VALUES (?, ?, ?)
        """,
        (student_id, code, created_by),
    )
    db.commit()
    return code


def get_invite_code_for_student(student_id):
    """Get the active (unclaimed) invite code for a student."""
    db = get_db()
    return db.execute(
        """
        SELECT * FROM parent_invite_codes
        WHERE student_id = ? AND claimed_at IS NULL
        ORDER BY created_at DESC LIMIT 1
        """,
        (student_id,),
    ).fetchone()


def get_invite_code_by_code(code):
    """Look up and invite code row by its code string."""
    db = get_db()
    return db.execute(
        "SELECT * FROM parent_invite_codes WHERE code = ?",
        (code,),
    ).fetchone()


def claim_invite_code(code, parent_id):
    """
    Claim an invite code -- links parent to student and marks code used.
    Returns student_id on success, None if code invalid or already claimed.
    """
    db = get_db()
    row = db.execute(
        "SELECT * FROM parent_invite_codes WHERE code = ? AND claimed_at IS NULL",
        (code,),
    ).fetchone()

    if not row:
        return None

    student_id = row["student_id"]

    # link parent or student (ignore if already linked)
    db.execute(
        """
        INSERT OR IGNORE INTO parent_student (parent_id, student_id)
        VALUES (?, ?)
        """,
        (parent_id, student_id),
    )
    # mark code claimed
    db.execute(
        "UPDATE parent_invite_codes SET claimed_at = CURRENT_TIMESTAMP WHERE code = ?",
        (code,),
    )
    db.commit()
    return student_id


def get_students_for_parent(parent_id):
    """Get all students linked to a parent account"""
    db = get_db()
    return db.execute(
        """
        SELECT u.id, u.username, u.avatar_emoji, u.avatar_bg
        FROM parent_student ps
        JOIN users u ON ps.student_id = u.id
        WHERE ps.parent_id = ?
        """,
        (parent_id,),
    ).fetchall()


def get_parents_for_student(student_id):
    """Get all parent accounts linked to a student."""
    db = get_db()
    return db.execute(
        """
        SELECT u.id, u.username
        FROM parent_student ps
        JOIN users u ON ps.parent_id = u.id
        WHERE ps.student_id = ?
        """,
        (student_id,),
    ).fetchall()


def is_parent_of(parent_id, student_id):
    """Check if a parent account is linked to a specific student"""
    db = get_db()
    return (
        db.execute(
            """
        SELECT 1 FROM parent_student
        WHERE parent_id = ? AND student_id = ?
        """,
            (parent_id, student_id),
        ).fetchone()
        is not None
    )


def get_student_activity_for_parent(student_id):
    """Get recent posts by a student for parent dashboard view"""
    db = get_db()
    return db.execute(
        """
        SELECT p.id, p.title, p.created_at, t.name as topic_name
        FROM posts p
        LEFT JOIN topics t ON p.topic_id = t.id
        WHERE p.user_id = ? AND p.is_hidden = 0
        ORDER BY p.created_at DESC
        LIMIT 20
        """,
        (student_id,),
    ).fetchall()


def get_announcements_for_parent(student_id):
    """Get classroom announcements from classrooms the student belongs to."""
    db = get_db()
    return db.execute(
        """
        SELECT p.id, p.title, p.body, p.created_at,
            u.username as teacher_username,
            c.name as classroom_name
        FROM posts p
        JOIN users u ON p.user_id = u.id
        JOIN classrooms c ON p.classroom_id = c.id
        JOIN classroom_members cm ON cm.classroom_id = c.id
        WHERE cm.user_id = ? AND u.role = 'teacher'
        AND p.is_hidden = 0
        ORDER BY p.created_at DESC
        LIMIT 20
        """,
        (student_id,),
    ).fetchall()
