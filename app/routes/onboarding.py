import csv
import io
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    request,
    jsonify,
)
from app.models import get_db
from app.models.topic import create_topic
from app.models.classroom import (
    create_classroom,
    provision_student,
)
from app.utils.auth import login_required
from app.utils.sanitize import sanitize_plain


onboarding_bp = Blueprint("onboarding", __name__)

NAME_MAX = 80
DESC_MAX = 300


@onboarding_bp.route("/welcome")
@login_required
def welcome():
    # Only teachers and admins should access this
    if session.get("role") not in ("teacher", "admin"):
        return redirect(url_for("feed.index"))

    db = get_db()
    classrooms = db.execute(
        "SELECT * FROM classrooms WHERE teacher_id = ?", (session["user_id"],)
    ).fetchall()

    return render_template("onboarding/welcome.html", classrooms=classrooms)


@onboarding_bp.route("/welcome/complete", methods=["POST"])
@login_required
def complete():
    """Mark onboarding as seen and redirect to feed."""
    db = get_db()
    db.execute(
        "UPDATE users SET tour_seen = 1 WHERE id = ?",
        (session["user_id"],),
    )
    db.commit()
    session["tour_seen"] = True
    # If ?tour=1 was passed, redirect to feed with flag so JS can open the tour
    if request.args.get("tour") == "1":
        return redirect(url_for("feed.index") + "?tour=1")
    return redirect(url_for("feed.index"))


@onboarding_bp.route("/welcome/create_classroom", methods=["POST"])
@login_required
def create_classroom_inline():
    """AJAX endpoint -- create a classroom and return its details as JSON"""
    if session.get("role") not in ("teacher", "admin"):
        return jsonify({"error": "Forbidden"}), 403

    name = sanitize_plain(request.form.get("name", "").strip(), max_length=NAME_MAX)
    description = sanitize_plain(
        request.form.get("description", "").strip(), max_length=NAME_MAX
    )

    if not name:
        return jsonify({"error": "Classroom name is required."}), 400

    classroom_id = create_classroom(session["user_id"], name, description)

    from app.models import get_db

    db = get_db()
    row = db.execute(
        "SELECT * FROM classrooms WHERE id = ?", (classroom_id,)
    ).fetchone()

    return jsonify(
        {
            "id": classroom_id,
            "name": name,
            "join_code": row["join_code"] if row else "",
        }
    )


@onboarding_bp.route("/welcome/provision-student", methods=["POST"])
@login_required
def provision_student_inline():
    """AJAX endpoint -- provision a student and return credentials as json"""
    if session.get("role") not in ("teacher", "admin"):
        return jsonify({"error": "Forbidden"}), 403

    first_name = sanitize_plain(
        request.form.get("first_name", "").strip(), max_length=50
    )
    last_name = sanitize_plain(request.form.get("last_name", "").strip(), max_length=50)
    dob = request.form.get("dob", "").strip()
    join_codes_raw = request.form.get("join_codes", "").strip()
    join_codes = [c.strip().upper() for c in join_codes_raw.split(",") if c.strip()]

    if not first_name or not last_name or not dob:
        return jsonify(
            {"error": "first name, last name, and date of birth are required."}
        ), 400

    try:
        result = provision_student(
            first_name, last_name, dob, join_codes, created_by=session["user_id"]
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(
        {
            "username": result["username"],
            "password": result["password"],
            "first_name": result["first_name"],
            "last_name": result["last_name"],
            "invalid_codes": result.get("invalid_codes", []),
        }
    )


@onboarding_bp.route("/welcome/create_topic", methods=["POST"])
@login_required
def create_topic_inline():
    """AJAX endpoint — create a topic and return its details as JSON."""
    if session.get("role") not in ("teacher", "admin"):
        return jsonify({"error": "Forbidden"}), 403

    name = sanitize_plain(request.form.get("name", "").strip(), max_length=NAME_MAX)
    description = sanitize_plain(
        request.form.get("description", "").strip(), max_length=DESC_MAX
    )

    if not name:
        return jsonify({"error": "Topic name is required."}), 400

    # Check for duplicate before creating
    from app.models.topic import get_topic_by_name

    if get_topic_by_name(name):
        return jsonify({"error": f'A topic named "{name}" already exists.'}), 409

    success, error = create_topic(name, description)
    if not success:
        return jsonify({"error": error or "Could not create topic."}), 500

    return jsonify({"name": name, "description": description})


@onboarding_bp.route("/welcome/provision-students-bulk", methods=["POST"])
@login_required
def provision_students_bulk_inline():
    if session.get("role") not in ("teacher", "admin"):
        return jsonify({"error": "FOrbidden"}), 400

    file = request.files.get("csv_file")
    if not file:
        return jsonify({"error": "No file updated."}), 400

    try:
        stream = io.StringIO(file.stream().decode("utf-8-sig"))
        reader = csv.DictReader(stream)
        rows = list(reader)
    except Exception:
        return jsonify({"error": "Could not parse CSV."}), 400

    if not rows:
        return jsonify({"error": "CSV is empty"}), 400

    from app.models.classroom import provision_students_bulk

    try:
        students = provision_students_bulk(rows, created_by=session["user_id"])
    except ValueError as e:
        return jsonify({"error": list(e.args[0])}), 400

    return jsonify(
        {
            "students": [
                {
                    "first_name": s["first_name"],
                    "last_name": s["last_name"],
                    "username": s["username"],
                    "password": s["password"],
                }
                for s in students
            ]
        }
    )
