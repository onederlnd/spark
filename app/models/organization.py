# app/models/organization.py
from app.models import get_db


def create_organization(name, billing_email, created_by):
    db = get_db()
    try:
        db.execute(
            """
            INSERT INTO organizations (name, billing_email, created_by)
            VALUES (?, ?, ?)
            """,
            (name, billing_email, created_by),
        )
        db.commit()
        org = db.execute(
            "SELECT id FROM organizations WHERE name = ? ORDER BY id DESC LIMIT 1",
            (name,),
        ).fetchone()
        return org["id"], None
    except Exception as e:
        return None, str(e)


def get_organization_by_id(org_id):
    db = get_db()
    return db.execute("SELECT * FROM organizations WHERE id = ?", (org_id,)).fetchone()


def get_org_teachers(org_id):
    db = get_db()
    return db.execute(
        """
        SELECT * FROM users
        WHERE org_id = ? AND role = 'teacher'
        ORDER BY display_name ASC
        """,
        (org_id,),  # was missing this!
    ).fetchall()


def get_org_classrooms(org_id):
    db = get_db()
    return db.execute(
        """
        SELECT c.*, u.display_name AS teacher_name,
            COUNT(cm.user_id) AS student_count
        FROM classrooms c
        JOIN users u ON u.id = c.teacher_id
        LEFT JOIN classroom_members cm ON cm.classroom_id = c.id AND cm.role = 'student'
        WHERE u.org_id = ?
        GROUP BY c.id
        ORDER BY c.created_at DESC
        """,
        (org_id,),
    ).fetchall()


def get_org_coppa_pending(org_id):
    db = get_db()
    return db.execute(
        """
        SELECT u.id, u.username, u.display_name, u.dob
        FROM users u
        JOIN classroom_members cm ON cm.user_id = u.id
        JOIN classrooms c ON c.id = cm.classroom_id
        JOIN users t ON t.id = c.teacher_id
        WHERE t.org_id = ? AND u.coppa_status = 'pending' AND u.role = 'student'
        GROUP BY u.id
        """,
        (org_id,),
    ).fetchall()


def deactivate_teacher(user_id, org_id):
    db = get_db()
    db.execute(
        "UPDATE users SET is_active = 0 WHERE id = ? AND org_id = ? AND role = 'teacher'",
        (user_id, org_id),
    )
    db.commit()


def reactivate_teacher(user_id, org_id):
    db = get_db()
    db.execute(
        "UPDATE users SET is_active = 1 WHERE id = ? AND org_id = ? AND role = 'teacher'",
        (user_id, org_id),
    )
    db.commit()
