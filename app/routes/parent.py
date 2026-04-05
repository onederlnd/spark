# app/routes/parent.py

from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from app.models.parent import (
    claim_invite_code,
    get_invite_code_by_code,
    get_students_for_parent,
    get_student_activity_for_parent,
    get_announcements_for_parent,
    generate_parent_invite_code,
    get_invite_code_for_student,
)
from app.models.user import get_user_by_username, create_user
from app.models import get_db
from app.utils.sanitize import sanitize_plain

parent_bp = Blueprint("parent", __name__, url_prefix="/parent")


def _require_parent():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    if session.get("role") != "parent":
        return "Forbidden", 403
    return None


def _require_teacher():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    if session.get("role") != "teacher":
        return "Forbidden", 403
    return None


def _enroll_in_shared_classroom(app, teacher_client, student_id):
    """Put the student in a classroom the teacher owns."""
    with app.app_context():
        from app.models import get_db
        from app.models.classroom import join_classroom, create_classroom

        db = get_db()
        teacher = db.execute(
            "SELECT id FROM users WHERE username = 'teacher1'"
        ).fetchone()
        classroom = db.execute(
            "SELECT id FROM classrooms WHERE teacher_id = ?", (teacher["id"],)
        ).fetchone()
        if not classroom:
            classroom_id = create_classroom("Test Class", teacher["id"])
        else:
            classroom_id = classroom["id"]
        join_classroom(classroom_id, student_id, role="student")


@parent_bp.route("/join", methods=["GET", "POST"])
def join():
    """Parent enters invite code"""
    if request.method == "POST":
        code = sanitize_plain(request.form.get("code", "").strip(), max_length=20)
        if not code:
            flash("Please enter an invite code.", "error")
            return render_template("parent/join.html")

        row = get_invite_code_by_code(code)
        if not row:
            flash("Invalid invite code.", "error")
            return render_template("parent/join.html")

        if row["claimed_at"]:
            flash("This code has already been used.", "error")
            return render_template("parent/join.html")

        # store code in sesson and move to registration or login
        session["pending_parent_code"] = code
        return redirect(url_for("parent.register"))

    return render_template("parent/join.html")


@parent_bp.route("/register", methods=["GET", "POST"])
def register():
    "Parent creates an account"
    code = session.get("pending_parent_code")
    if not code:
        flash("Please enter an nvite code first.", "error")
        return redirect(url_for("parent.join"))

    if request.method == "POST":
        first_name = sanitize_plain(
            request.form.get("first_name", "").strip(), max_length=50
        )
        last_name = sanitize_plain(
            request.form.get("last_name", "").strip(), max_length=50
        )
        password = request.form.get("password", "")

        if not first_name or not last_name or not password:
            flash("All fields are required.", "error")
            return render_template("parent/register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("parent/register.html")

        base = f"parent.{first_name.lower()}.{last_name.lower()}"
        username = base
        db = get_db()
        counter = 1

        while db.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone():
            username = f"{base}{counter}"
            counter += 1

        display_name = f"{first_name} {last_name}"

        success, error = create_user(
            username=username,
            password=password,
            role="parent",
            bio="",
            dob="1980-01-01",
        )
        if not success:
            flash(error or "Could not create account", "error")
            return render_template("parent/register.html")

        user = get_user_by_username(username)
        user_id = user["id"]

        db.execute(
            "UPDATE users SET display_name = ? WHERE id = ?", (display_name, user_id)
        )
        db.commit()

        student_id = claim_invite_code(code, user_id)
        if not student_id:
            flash("Invite code expired or already used")
            return render_template("parent/register.html")

        session.pop("pending_parent_code", None)
        session["user_id"] = user_id
        session["username"] = username
        session["role"] = "parent"

        flash("Account created! You're now connected to your child.", "success")
        return redirect(url_for("parent.dashboard"))

    return render_template("parent/register.html")


@parent_bp.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    guard = _require_parent()
    if guard is not None:
        return guard

    parent_id = session["user_id"]
    students = get_students_for_parent(parent_id)

    children = []
    for student in students:
        children.append(
            {
                "student": student,
                "activity": get_student_activity_for_parent(student["id"]),
                "announcements": get_announcements_for_parent(student["id"]),
            }
        )

    return render_template("parent/dashboard.html", children=children)


@parent_bp.route("/invite/<int:student_id>", methods=["POST"])
def generate_code(student_id):
    guard = _require_teacher()
    if guard is not None:
        return guard

    db = get_db()
    student = db.execute(
        "SELECT * FROM users WHERE id = ? AND role = 'student'",
        (student_id,),
    ).fetchone()

    if not student:
        flash("Student not found", "error")
        return redirect(request.referrer or url_for("classrooms.join"))

    shared_classroom = db.execute(
        """
        SELECT 1 FROM classroom_members cm1
        JOIN classroom_members cm2 ON cm1.classroom_id = cm2.classroom_id
        WHERE cm1.user_id = ? AND cm2.user_id = ?
        """,
        (session["user_id"], student_id),
    ).fetchone()

    if not shared_classroom:
        return "Forbidden", 403

    existing = get_invite_code_for_student(student_id)
    if existing:
        code = existing["code"]
    else:
        code = generate_parent_invite_code(student_id, session["user_id"])

    flash(f"Invite code for {student['username']}: {code}", "success")
    return redirect(request.referrer or url_for("classrooms.join"))
