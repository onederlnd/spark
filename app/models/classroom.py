import random
import string
from app.models import get_db


# --- helpers
def _generate_join_code():
    """Generate a random 6-character uppercase join code"""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


# --- classroom
def create_classroom(teacher_id, name, description=""):
    db = get_db()
    join_code = _generate_join_code()
    while db.execute(
        "SELECT id from classrooms WHERE join_code=?", (join_code,)
    ).fetchone():
        join_code = _generate_join_code()
    cursor = db.execute(
        """
        INSERT INTO classrooms (teacher_id, name, description, join_code) VALUES (?,?,?,?)""",
        (teacher_id, name, description, join_code),
    )
    db.commit()
    classroom_id = cursor.lastrowid

    db.execute(
        "INSERT INTO classroom_members (classroom_id, user_id, role) VALUES (?, ?, ?)",
        (
            classroom_id,
            teacher_id,
            "teacher",
        ),
    )
    db.commit()
    return classroom_id


def get_classroom(classroom_id):
    db = get_db()
    return db.execute(
        """
                    SELECT classrooms.*, users.username as teacher_name
                    FROM classrooms
                    JOIN users ON classrooms.teacher_id = users.id
                    WHERE classrooms.id = ?
    """,
        (classroom_id,),
    ).fetchone()


def get_classroom_by_join_code(join_code):
    db = get_db()
    return db.execute(
        "SELECT * FROM classrooms WHERE join_code = ?", (join_code,)
    ).fetchone()


def get_classrooms_for_user(user_id):
    """Return all classrooms a user is a member of (any role)"""
    db = get_db()
    return db.execute(
        """
                    SELECT classrooms.*, users.username as teacher_name,
                        classroom_members.role as member_role
                    FROM classroom_members
                    JOIN classrooms ON classroom_members.classroom_id = classrooms.id
                    JOIN users ON classrooms.teacher_id = users.id
                    WHERE classroom_members.user_id = ?
                    ORDER BY classrooms.created_at DESC
        """,
        (user_id,),
    ).fetchall()


def get_classroom_members(classroom_id):
    db = get_db()
    return db.execute(
        """
                    SELECT users.id, users.username, classroom_members.role, classroom_members.joined_at
                    FROM classroom_members
                    JOIN users ON classroom_members.user_id = users.id
                    WHERE classroom_members.classroom_id = ?
                    ORDER BY classroom_members.role DESC, users.username ASC
        """,
        (classroom_id,),
    ).fetchall()


def get_member_role(classroom_id, user_id):
    """Return 'teacher', 'student, or None if not a member."""
    db = get_db()
    row = db.execute(
        "SELECT role FROM classroom_members WHERE classroom_id = ? AND user_id = ?",
        (classroom_id, user_id),
    ).fetchone()
    return row["role"] if row else None


def join_classroom(classroom_id, user_id, role):
    """Add a student to a classroom. Returns False if already a member"""
    db = get_db()
    existing = db.execute(
        "SELECT 1 FROM classroom_members WHERE classroom_id = ? AND user_id = ?",
        (classroom_id, user_id),
    ).fetchone()
    if existing:
        return False
    db.execute(
        """
                    INSERT INTO classroom_members (classroom_id, user_id, role)
                        VALUES (?, ?, ?)
               """,
        (classroom_id, user_id, role),
    )
    db.commit()
    return True


# --- assignments
def create_assignment(classroom_id, title, instructions, due_date=None):
    db = get_db()
    cursor = db.execute(
        """
                    INSERT INTO assignments (classroom_id, title, instructions, due_date)
                            VALUES (?,?,?,?)
                        """,
        (classroom_id, title, instructions, due_date),
    )
    db.commit()
    return cursor.lastrowid


def get_assignment(assignment_id):
    db = get_db()
    return db.execute(
        """
                    SELECT assignments.*, classrooms.name as classroom_name,
                        classrooms.teacher_id
                      FROM assignments
                      JOIN classrooms ON assignments.classroom_id = classrooms.id
                      WHERE assignments.id = ?
                      """,
        (assignment_id,),
    ).fetchone()


def get_assignments_for_classroom(classroom_id):
    db = get_db()
    return db.execute(
        """
                    SELECT * FROM assignments
                      WHERE classroom_id = ?
                      ORDER BY due_date ASC, created_at DESC
                      """,
        (classroom_id,),
    ).fetchall()


# --- submissions
def create_submission(assignment_id, user_id, body):
    db = get_db()
    existing = db.execute(
        """SELECT id FROM submissions
                        WHERE assignment_id = ? AND user_id = ?""",
        (assignment_id, user_id),
    ).fetchone()
    if existing:
        db.execute(
            "UPDATE submissions SET body = ?, submitted_at = CURRENT_TIMESTAMP WHERE id = ?",
            (body, existing["id"]),
        )
        db.commit()
        return existing["id"]
    cursor = db.execute(
        """INSERT INTO submissions (assignment_id, user_id, body)
        VALUES (?,?,?)""",
        (assignment_id, user_id, body),
    )
    db.commit()
    return cursor.lastrowid


def get_submission(assignment_id, user_id):
    """Get a single student's submission for an assignment"""
    db = get_db()
    return db.execute(
        """
        SELECT submissions.*, users.username
        FROM submissions
        JOIN users ON submissions.user_id = users.id
        WHERE submissions.assignment_id = ? AND submissions.user_id = ?
        """,
        (assignment_id, user_id),
    ).fetchone()


def get_submissions_for_assignment(assignment_id):
    """Get all submissions for an assignment (teacher view)"""
    db = get_db()
    return db.execute(
        """
        SELECT submissions.*, users.username
        FROM submissions
        JOIN users ON submissions.user_id = users.id
        WHERE submissions.assignment_id = ?
        ORDER BY users.username ASC
        """,
        (assignment_id,),
    ).fetchall()


def get_submission_grid(assignment_id, classroom_id):
    """
    Return all students in the classrooms with their submission status. Useful for the teachers grid view.
    """
    db = get_db()
    return db.execute(
        """
        SELECT users.id as user_id, users.username,
            submissions.id as submission_id,
            submissions.body,
            submissions.grade,
            submissions.feedback,
            submissions.submitted_at
        FROM classroom_members
        JOIN users on classroom_members.user_id = users.id
        LEFT JOIN submissions
            ON submissions.user_id = users.id
            AND submissions.assignment_id = ?
        WHERE classroom_members.classroom_id = ?
        AND classroom_members.role = 'student'
        ORDER BY users.username ASC
        """,
        (assignment_id, classroom_id),
    ).fetchall()


def get_pending_grades_for_teacher(teacher_id):
    """Return a dict of classroom_id -> ungraded submission count"""
    db = get_db()
    rows = db.execute(
        """
        SELECT assignments.classroom_id, COUNT(submissions.id) as pending
        FROM submissions
        JOIN assignments ON submissions.assignment_id = assignments.id
        JOIN classrooms ON assignments.classroom_id = classrooms.id
        WHERE classrooms.teacher_id = ?
        AND (submissions.grade IS NULL OR submissions.grade = '')
        GROUP BY assignments.classroom_id
        """,
        (teacher_id,),
    ).fetchall()
    return {row["classroom_id"]: row["pending"] for row in rows}


def save_grade(submission_id, grade, feedback=""):
    db = get_db()
    db.execute(
        "UPDATE submissions SET grade = ?, feedback = ? WHERE id = ?",
        (grade, feedback, submission_id),
    )
    db.commit()
