import re
import unicodedata
import random
import string
from app.models import get_db
from app.models.user import generate_qr_token


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
                    SELECT users.id, users.username, users.provisional,
                        classroom_members.role, classroom_members.joined_at
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


# --- provisioning helpers

_WORDS = [
    "sunny",
    "windy",
    "rainy",
    "cloud",
    "maple",
    "river",
    "stone",
    "frost",
    "bloom",
    "creek",
    "tiger",
    "eagle",
    "panda",
    "koala",
    "finch",
    "robin",
    "cedar",
    "birch",
    "ember",
    "coral",
    "lunar",
    "solar",
    "misty",
    "sandy",
    "brave",
    "swift",
    "quiet",
    "jolly",
    "lucky",
    "fuzzy",
    "witty",
    "stormy",
]


def _slugify(text):
    """Convert a name to a lowercase ASCII slug"""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]", "", text)
    return text


def generate_username(first_name, last_name):
    """
    Generate a unique username as firstname.lastname, with a numeric suffix to resolve collisions (e.g. john.smith2, john.smith3).
    """
    db = get_db()
    first = _slugify(first_name)
    last = _slugify(last_name)
    if not first or not last:
        raise ValueError(
            "First and last name just contain at least one ASCII character"
        )

    base = f"{first}.{last}"
    username = base
    counter = 2
    while db.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
        username = f"{base}{counter}"
        counter += 1
    return username


def generate_password():
    word1, word2 = random.sample(_WORDS, 2)
    digits = random.randint(10, 99)
    return f"{word1}{word2}{digits}"


def provision_student(first_name, last_name, dob, join_codes=None, created_by=None):
    """
    Create a provisioned student account. Returns a dict with account info and a list of classroom names the student was enrolled in. join_codes is an optional list of strings. Provisioned students are always coppa_status='approved' (school official exception)
    """
    import bcrypt
    from flask import current_app
    from datetime import datetime

    db = get_db()
    rounds = current_app.config.get("BCRYPT_ROUNDS", 12)

    try:
        dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(
            f"Invalid date format for {first_name} {last_name}: must be YYYY-MM-DD"
        )

    username = generate_username(first_name, last_name)
    password = generate_password()
    password_hash = bcrypt.hashpw(
        password.encode(), bcrypt.gensalt(rounds=rounds)
    ).decode()
    qr_token = generate_qr_token()

    cursor = db.execute(
        """
        INSERT INTO users (username, password_hash, dob, bio, role, coppa_status, onboarded, provisional, qr_token, created_by)
        VALUES (?, ?, ?, '', 'student', 'approved', 0, 1, ?, ?)
        """,
        (username, password_hash, dob_date.isoformat(), qr_token, created_by),
    )
    db.commit()
    user_id = cursor.lastrowid

    enrolled_classrooms = []
    invalid_codes = []

    if join_codes:
        for code in join_codes:
            code = code.strip().upper()
            if not code:
                continue
            classroom = get_classroom_by_join_code(code)
            if not classroom:
                invalid_codes.append(code)
                continue
            join_classroom(classroom["id"], user_id, "student")
            enrolled_classrooms.append(classroom["name"])

    return {
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "password": password,
        "dob": dob_date.isoformat(),
        "classrooms": enrolled_classrooms,
        "invalid_codes": invalid_codes,
        "qr_token": qr_token,
    }


def provision_students_bulk(rows, created_by=None):
    """
    Provision multiple students form a list of dicts with keys:
    first_name, last_name, dob, join_codes (optional, comma-separated string).
    Returns (student, skipped) where students is a list of result dicts and skipped is a list of error strings.
    """
    students = []
    errors = []

    for i, row in enumerate(rows, start=1):
        first_name = row.get("first_name", "").strip()
        last_name = row.get("last_name", "").strip()
        dob = row.get("dob", "").strip()
        join_codes_raw = row.get("join_codes", "")
        join_codes = (
            [c.strip() for c in join_codes_raw.split(",") if c.strip()]
            if join_codes_raw
            else []
        )

        if not first_name or not last_name:
            errors.append(f"Row {i}: missing first or last name")
        if not dob:
            errors.append(f"Row {i} ({first_name} {last_name}): missing date of birth")
        if not join_codes:
            errors.append(f"Row {i} ({first_name} {last_name}): no join code provided")
    if errors:
        raise ValueError(errors)

    for i, row in enumerate(rows, start=1):
        first_name = row.get("first_name", "").strip()
        last_name = row.get("last_name", "").strip()
        dob = row.get("dob", "").strip()
        join_codes_raw = row.get("join_codes", "")
        join_codes = (
            [c.strip() for c in join_codes_raw.split(",") if c.strip()]
            if join_codes_raw
            else []
        )

        try:
            result = provision_student(
                first_name, last_name, dob, join_codes, created_by=created_by
            )
            students.append(result)
        except ValueError as e:
            errors.append(str(e))

    if errors:
        raise ValueError(errors)

    return students


def get_provisioned_students_for_teacher(teacher_id):
    """Return all provisional students created by this teacher."""
    db = get_db()
    rows = db.execute(
        """
        SELECT users.id, users.username, users.dob, users.created_at,
               GROUP_CONCAT(classrooms.name, ', ') as classroom_names
        FROM users
        LEFT JOIN classroom_members ON classroom_members.user_id = users.id
        LEFT JOIN classrooms ON classroom_members.classroom_id = classrooms.id
        WHERE users.provisional = 1
          AND users.created_by = ?
        GROUP BY users.id
        ORDER BY users.created_at DESC
        """,
        (teacher_id,),
    ).fetchall()
    return rows


def enroll_student_by_codes(student_id, join_codes):
    """
    Enroll an existing provisional student in classrooms by join code.
    Returns (enrolled, invalid_codes).
    """
    enrolled = []
    invalid_codes = []
    for code in join_codes:
        code = code.strip().upper()
        if not code:
            continue
        classroom = get_classroom_by_join_code(code)
        if not classroom:
            invalid_codes.append(code)
            continue
        join_classroom(classroom["id"], student_id, "student")
        enrolled.append(classroom["name"])
    return enrolled, invalid_codes
