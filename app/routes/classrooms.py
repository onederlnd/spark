from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
)
from app.utils.auth import login_required
from app.utils.rate_limit import rate_limit
from app.utils.sanitize import sanitize_plain, sanitize_bbcode
from app.models.classroom import (
    create_classroom,
    get_classroom,
    get_classroom_by_join_code,
    get_classrooms_for_user,
    get_classroom_members,
    get_member_role,
    join_classroom,
    create_assignment,
    get_assignment,
    get_assignments_for_classroom,
    create_submission,
    get_submission,
    get_submission_grid,
    get_submissions_for_assignment,
    save_grade,
)
from app.models.user import get_user_by_id, coppa_required

classrooms_bp = Blueprint("classrooms", __name__, url_prefix="/classrooms")

NAME_MAX = 80
DESC_MAX = 300
TITLE_MAX = 200
INSTRUCTIONS_MAX = 10000
BODY_MAX = 10000


# --- helpers


def _get_role(classroom_id):
    """Return the current user's role in a classroom, or None."""
    return get_member_role(classroom_id, session["user_id"])


def _require_member(classroom_id):
    """Return (classroom, role) or (None, None) if not member."""
    classroom = get_classroom(classroom_id)
    if not classroom:
        return None, None
    role = _get_role(classroom_id)
    return classroom, role


def _is_teacher(user_id):
    user = get_user_by_id(user_id)
    return user and user["role"] == "teacher"


@classrooms_bp.route("/")
@login_required
@coppa_required
def dashboard():
    classrooms = get_classrooms_for_user(session["user_id"])
    is_teacher = _is_teacher(session["user_id"])

    return render_template(
        "classrooms/dashboard.html",
        classrooms=classrooms,
        is_teacher=is_teacher,
    )


@classrooms_bp.route("/new", methods=["GET", "POST"])
@login_required
@coppa_required
def new_classroom():
    if not _is_teacher(session["user_id"]):
        return "Forbidden", 403
    if request.method == "POST":
        name = sanitize_plain(request.form.get("name", ""), max_length=NAME_MAX)
        description = sanitize_plain(
            request.form.get("description", ""), max_length=DESC_MAX
        )
        if not name:
            return render_template(
                "classrooms/new.html", error="Classroom name is required."
            )
        classroom_id = create_classroom(session["user_id"], name, description)
        flash("Classroom created!", "success")
        return redirect(url_for("classrooms.classroom_home", classroom_id=classroom_id))

    return render_template("classrooms/new.html")


# --- join classroom


@classrooms_bp.route("/join", methods=["POST"])
@login_required
@rate_limit(max_requests=10, window_seconds=60)
@coppa_required
def join():
    join_code = request.form.get("join_code", "").strip().upper()

    if not join_code:
        flash("Please enter a join code", "error")
        return redirect(url_for("classrooms.dashboard"))

    classroom = get_classroom_by_join_code(join_code)
    if not classroom:
        flash("Invalid join code.", "error")
        return redirect(url_for("classrooms.dashboard"))

    existing_role = _get_role(classroom["id"])
    if existing_role:
        flash("You're already in this classroom")
        return redirect(
            url_for("classrooms.classroom_home", classroom_id=classroom["id"])
        )

    role = "teacher" if _is_teacher(session["user_id"]) else "student"
    join_classroom(classroom["id"], session["user_id"], role)

    flash(f"Joined {classroom['name']}!", "success")
    return redirect(url_for("classrooms.classroom_home", classroom_id=classroom["id"]))


# --- classroom home


@classrooms_bp.route("/<int:classroom_id>", strict_slashes=False)
@login_required
@coppa_required
def classroom_home(classroom_id):
    classroom, role = _require_member(classroom_id)
    if not classroom:
        return "Classroom not found", 404

    if not role:
        return "Forbidden", 403

    assignments = get_assignments_for_classroom(classroom_id)
    members = get_classroom_members(classroom_id)
    return render_template(
        "classrooms/classroom.html",
        classroom=classroom,
        role=role,
        assignments=assignments,
        members=members,
    )


@classrooms_bp.route("/<int:classroom_id>/assignments/new", methods=["GET", "POST"])
@login_required
@coppa_required
def new_assignment(classroom_id):
    classroom, role = _require_member(classroom_id)
    if not classroom:
        return "Classroom not found", 404
    if role != "teacher":
        return "Forbidden", 403

    if request.method == "POST":
        title = sanitize_plain(request.form.get("title", ""), max_length=TITLE_MAX)
        instructions = sanitize_bbcode(
            request.form.get("instructions", ""), max_length=INSTRUCTIONS_MAX
        )
        due_date = request.form.get("due_date", "").strip() or None

        if not title or not instructions:
            return render_template(
                "classrooms/assignments_new.html",
                classroom=classroom,
                error="Title and instructions are required.",
            )
        assignment_id = create_assignment(classroom_id, title, instructions, due_date)
        flash("Assignment created!", "success")
        return redirect(
            url_for(
                "classrooms.view_assignment",
                classroom_id=classroom_id,
                assignment_id=assignment_id,
            )
        )

    return render_template("classrooms/assignments_new.html", classroom=classroom)


# --- view assignments + submit


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>", methods=["GET", "POST"]
)
@login_required
@coppa_required
def view_assignment(classroom_id, assignment_id):
    classroom, role = _require_member(classroom_id)
    if not classroom:
        return "Classroom not found", 404
    if not role:
        return "Forbidden", 403

    assignment = get_assignment(assignment_id)
    if not assignment or assignment["classroom_id"] != classroom_id:
        return "Assignment not found", 404

    submission = get_submission(assignment_id, session["user_id"])
    submission_count = len(get_submissions_for_assignment(assignment_id))

    if request.method == "POST":
        if role != "student":
            return "Forbidden", 403

        body = sanitize_bbcode(request.form.get("body", ""), max_length=BODY_MAX)
        if not body:
            return render_template(
                "classrooms/assignment.html",
                classroom=classroom,
                assignment=assignment,
                role=role,
                submission=submission,
                submission_count=submission_count,
                error="Submission cannot be empty.",
            )

        create_submission(assignment_id, session["user_id"], body)
        flash("Submission saved!", "success")
        return redirect(
            url_for(
                "classrooms.view_assignment",
                classroom_id=classroom_id,
                assignment_id=assignment_id,
            )
        )
    return render_template(
        "classrooms/assignment.html",
        classroom=classroom,
        assignment=assignment,
        role=role,
        submission=submission,
        submission_count=submission_count,
    )


@classrooms_bp.route("/<int:classroom_id>/assignments/<int:assignment_id>/grade")
@login_required
@coppa_required
def grade_grid(classroom_id, assignment_id):
    classroom, role = _require_member(classroom_id)
    if not classroom:
        return "Classroom not found", 404
    if role != "teacher":
        return "Forbidden", 403

    assignment = get_assignment(assignment_id)
    if not assignment or assignment["classroom_id"] != classroom_id:
        return "Assignment not found", 404

    grid = get_submission_grid(assignment_id, classroom_id)
    return render_template(
        "classrooms/grade.html",
        classroom=classroom,
        assignment=assignment,
        grid=grid,
    )


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>/grade/<int:student_id>",
    methods=["GET", "POST"],
)
@login_required
@coppa_required
def grade_submission(classroom_id, assignment_id, student_id):
    classroom, role = _require_member(classroom_id)
    if not classroom:
        return "Classroom not found", 404
    if role != "teacher":
        return "Forbidden", 403

    assignment = get_assignment(assignment_id)
    if not assignment or assignment["classroom_id"] != classroom_id:
        return "Assignment not found", 404

    student = get_user_by_id(student_id)
    member_role = get_member_role(classroom_id, student_id)
    if not student or not member_role:
        return "Student not found in classroom", 404
    submission = get_submission(assignment_id, student_id)

    if request.method == "POST":
        grade = sanitize_plain(request.form.get("grade", ""), max_length=20)
        feedback = sanitize_plain(request.form.get("feedback"), max_length=1000)

        if not submission:
            submission_id = create_submission(assignment_id, student_id, "")
            save_grade(submission_id, grade, feedback)
        else:
            save_grade(submission["id"], grade, feedback)

        flash("Grade saved.", "success")
        return redirect(
            url_for(
                "classrooms.grade_grid",
                classroom_id=classroom_id,
                assignment_id=assignment_id,
            )
        )

    return render_template(
        "classrooms/grade_submission.html",
        classroom=classroom,
        assignment=assignment,
        submission=submission,
    )
