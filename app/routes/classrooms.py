import csv
import os
import io
from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    Response,
    current_app,
    send_from_directory,
)
from app.utils.auth import login_required, teacher_required
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
    get_pending_grades_for_teacher,
    provision_student,
    provision_students_bulk,
    get_provisioned_students_for_teacher,
    enroll_student_by_codes,
)
from app.models.user import (
    get_user_by_id,
    coppa_required,
    mark_onboarded,
    regenerate_qr_token,
)
from app.models.report import get_reports_for_classroom
from app.utils.content_filter import add_word, remove_word, get_all_words
from app.models.attachments import (
    get_assignment_attachments,
    add_assignment_attachment,
    delete_assignment_attachment,
    get_submission_attachments,
    add_submission_attachment,
    delete_submission_attachment,
    get_upload_dir,
)
from app.models.resources import (
    add_resource_link,
    add_resource_file,
    delete_resource,
    get_resource,
    get_resources_for_classroom,
    get_resources_for_assignment,
    attach_resources_to_assignment,
    detach_resource_from_assignment,
)

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
    pending_grades = (
        get_pending_grades_for_teacher(session["user_id"]) if is_teacher else {}
    )
    classroom_names = {c["id"]: c["name"] for c in classrooms}
    user = get_user_by_id(session["user_id"])
    show_onboarding = is_teacher and not user["onboarded"]

    return render_template(
        "classrooms/dashboard.html",
        classrooms=classrooms,
        is_teacher=is_teacher,
        pending_grades=pending_grades,
        classroom_names=classroom_names,
        show_onboarding=show_onboarding,
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
                "classrooms/new.html", errors="Classroom name is required."
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
    pending_reports = (
        len(get_reports_for_classroom(classroom_id)) if role == "teacher" else 0
    )
    return render_template(
        "classrooms/classroom.html",
        classroom=classroom,
        role=role,
        assignments=assignments,
        members=members,
        pending_reports=pending_reports,
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

    resources = get_resources_for_classroom(classroom_id)

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
                resources=resources,
                error="Title and instructions are required.",
            )
        assignment_id = create_assignment(classroom_id, title, instructions, due_date)

        resource_ids = request.form.getlist("resource_ids", type=int)
        if resource_ids:
            attach_resources_to_assignment(assignment_id, resource_ids)
        flash("Assignment created!", "success")
        return redirect(
            url_for(
                "classrooms.view_assignment",
                classroom_id=classroom_id,
                assignment_id=assignment_id,
            )
        )
    return render_template(
        "classrooms/assignments_new.html",
        classroom=classroom,
        resources=resources,
    )


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
    assignment_attachments = get_assignment_attachments(assignment_id)
    submission_attachments = (
        get_submission_attachments(submission["id"]) if submission else []
    )
    assignment_resources = get_resources_for_assignment(assignment_id)
    classroom_resources = (
        get_resources_for_classroom(classroom_id) if role == "teacher" else []
    )
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
                assignment_attachments=assignment_attachments,
                submission_attachments=submission_attachments,
                assignment_resources=assignment_resources,
                classroom_resources=classroom_resources,
                error="Submission cannot be empty.",
            )
        create_submission(assignment_id, session["user_id"], body)
        submission = get_submission(assignment_id, session["user_id"])
        files = request.files.getlist("files")
        errors = []
        for file in files:
            if file and file.filename:
                try:
                    add_submission_attachment(
                        submission["id"],
                        file,
                        session["user_id"],
                        current_app._get_current_object(),
                    )
                except ValueError as e:
                    errors.append(str(e))

        if errors:
            flash(" ".join(errors), "error")

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
        assignment_attachments=assignment_attachments,
        submission_attachments=submission_attachments,
        assignment_resources=assignment_resources,
        classroom_resources=classroom_resources,
    )


@classrooms_bp.route("/<int:classroom_id>/resources")
@login_required
@teacher_required
def resource_library(classroom_id):
    classroom, role = _require_member(classroom_id)
    if not classroom:
        return "Classroom not found", 404
    if role != "teacher":
        return "Forbidden", 403

    resources = get_resources_for_classroom(classroom_id)
    return render_template(
        "classrooms/resources.html",
        classroom=classroom,
        resources=resources,
    )


@classrooms_bp.route("/<int:classroom_id>/resources/add-link", methods=["POST"])
@login_required
@teacher_required
def add_resource_link_route(classroom_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or role != "teacher":
        return "Forbidden", 403

    title = sanitize_plain(request.form.get("title", "").strip(), max_length=200)
    url = request.form.get("url", "").strip()

    try:
        add_resource_link(classroom_id, session["user_id"], title, url)
        flash("Link added to resource library.", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(
        url_for(
            "classrooms.resource_library",
            classroom_id=classroom_id,
        )
    )


@classrooms_bp.route("/<int:classroom_id>/resources/add-file", methods=["POST"])
@login_required
@teacher_required
def add_resource_file_route(classroom_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or role != "teacher":
        return "Forbidden", 403

    title = sanitize_plain(request.form.get("title", "").strip(), max_length=200)
    file = request.files.get("file")

    try:
        add_resource_file(
            classroom_id,
            session["user_id"],
            title,
            file,
            current_app._get_current_object(),
        )
        flash("File added to resource library.", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("classrooms.resource_library", classroom_id=classroom_id))


@classrooms_bp.route(
    "/<int:classroom_id>/resources/<int:resource_id>/delete", methods=["POST"]
)
@login_required
@teacher_required
def delete_resource_route(classroom_id, resource_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or role != "teacher":
        return "Forbidden", 403
    resource = get_resource(resource_id)
    if not resource or resource["classroom_id"] != classroom_id:
        return "Resource not found", 404
    if resource["teacher_id"] != session["user_id"]:
        return "Forbidden", 403
    delete_resource(resource_id, current_app._get_current_object())
    flash("Resource deleted.", "success")
    return redirect(url_for("classrooms.resource_library", classroom_id=classroom_id))


@classrooms_bp.route(
    "/<int:classroom_id>/resources/<int:resource_id>/attach", methods=["POST"]
)
@login_required
@teacher_required
def attach_resource_route(classroom_id, resource_id):  # DEBUG:
    classroom, role = _require_member(classroom_id)
    if not classroom or role != "teacher":
        return "Forbidden", 403

    assignment_id = request.form.get("assignment_id", type=int)
    assignment = get_assignment(assignment_id)

    if not assignment or assignment["classroom_id"] != classroom_id:
        return "Assignment not found", 404

    resource = get_resource(resource_id)
    if not resource or resource["classroom_id"] != classroom_id:
        return "Resource not found", 404

    attach_resources_to_assignment(assignment_id, [resource_id])

    flash("Resource attached.", "success")
    return redirect(
        url_for(
            "classrooms.view_assignment",
            classroom_id=classroom_id,
            assignment_id=assignment_id,
        )
    )


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>/resources/<int:resource_id>/detach",
    methods=["POST"],
)
@login_required
@teacher_required
def detach_resource_route(classroom_id, assignment_id, resource_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or role != "teacher":
        return "Forbidden", 403

    assignment = get_assignment(assignment_id)

    if not assignment or assignment["classroom_id"] != classroom_id:
        return "Assignment not found", 404

    detach_resource_from_assignment(assignment_id, resource_id)
    flash("Resource removed.", "success")
    return redirect(
        url_for(
            "classrooms.view_assignment",
            classroom_id=classroom_id,
            assignment_id=assignment_id,
            resource_id=resource_id,
        )
    )


@classrooms_bp.route(
    "/<int:classroom_id>/resources/<int:resource_id>/download", methods=["POST"]
)
@login_required
@teacher_required
def download_resources(classroom_id, resource_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or role != "teacher":
        return "Forbidden", 403

    resource = get_resource(resource_id)
    if (
        not resource
        or resource["classroom_id"] != classroom_id
        or resource["type"] != "file"
    ):
        return "Resource not found", 404

    upload_dir = get_upload_dir(current_app._get_current_object())
    folder = os.path.join(upload_dir, f"resources/{classroom_id}")
    return send_from_directory(
        folder,
        resource["filename"],
        as_attachment=True,
        download_name=resource["original_filename"],
    )


@classrooms_bp.route("/<int:classroom_id>/assignments/<int:assignment_id>/grade")
@login_required
@teacher_required
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
    submission_attachments = (
        get_submission_attachments(submission["id"]) if submission else []
    )
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
        submission_attachments=submission_attachments,
    )


@classrooms_bp.route("/filter/words", methods=["GET", "POST"])
@login_required
@teacher_required
def manage_filter():
    if request.method == "POST":
        action = request.form.get("action")
        word = request.form.get("word", "").strip()

        if not word:
            flash("Word cannot be empty.", "error")
            return redirect(url_for("classrooms.manage_filter"))

        if action == "add":
            success = add_word(word, session["user_id"])
            flash(
                f'"{word}" added to filter.'
                if success
                else f'"{word}" already exists.',
                "success" if success else "warning",
            )
        elif action == "remove":
            remove_word(word)
            flash(f'"{word}" removed from filter.', "success")

        return redirect(url_for("classrooms.manage_filter"))
    words = get_all_words()
    return render_template("classrooms/filter.html", words=words)


@classrooms_bp.route("/onboarding/complete", methods=["POST"])
@login_required
def complete_onboarding():
    mark_onboarded(session["user_id"])
    return "", 204


@classrooms_bp.route("/provision/enroll/<int:student_id>", methods=["POST"])
@login_required
@teacher_required
def enroll_student(student_id):
    student = get_user_by_id(student_id)
    if (
        not student
        or not student["provisional"]
        or student["created_by"] != session["user_id"]
    ):
        return "Forbidden", 403

    join_codes_raw = request.form.get("join_codes", "").strip()
    join_codes = [c.strip() for c in join_codes_raw.split(",") if c.strip()]

    if not join_codes:
        flash("Please enter at least one join code.", "error")
        return redirect(url_for("classrooms.provision"))

    enrolled, invalid_codes = enroll_student_by_codes(student_id, join_codes)

    if invalid_codes:
        flash(f"Invalid join codes: {', '.join(invalid_codes)}", "error")
    if enrolled:
        flash(f"{student['username']} enrolled in: {', '.join(enrolled)}", "success")

    return redirect(url_for("classrooms.provision"))


@classrooms_bp.route("/provision", methods=["GET", "POST"])
@login_required
@teacher_required
def provision():
    provisioned_students = get_provisioned_students_for_teacher(session["user_id"])
    prefill_join_code = request.args.get("join_code", "")
    if request.method == "POST":
        method = request.form.get("method")

        if method == "manual":
            first_name = sanitize_plain(
                request.form.get("first_name", "").strip(), max_length=50
            )
            last_name = sanitize_plain(
                request.form.get("last_name", "").strip(), max_length=50
            )
            dob = request.form.get("dob", "").strip()
            join_codes_raw = request.form.get("join_codes", "").strip()
            join_codes = [
                c.strip().upper() for c in join_codes_raw.split(",") if c.strip()
            ]

            if not first_name or not last_name or not dob:
                return render_template(
                    "classrooms/provision.html",
                    prefill_join_code=prefill_join_code,
                    errors=["First name, last name, and date of birth are required"],
                )

            try:
                result = provision_student(
                    first_name,
                    last_name,
                    dob,
                    join_codes,
                    created_by=session["user_id"],
                )
            except ValueError as e:
                return render_template(
                    "classrooms/provision.html",
                    prefill_join_code=prefill_join_code,
                    errors=[str(e)],
                )

            skipped = []

            if result["invalid_codes"]:
                skipped = [f"Invalid join codes: {', '.join(result['invalid_codes'])}"]

            session["provisioned_students"] = [result]
            session["provisioned_skipped"] = skipped
            return redirect(url_for("classrooms.credentials"))

        elif method == "csv":
            file = request.files.get("csv_file")
            if not file or not file.filename.endswith(".csv"):
                return render_template(
                    "classrooms/provision.html",
                    prefill_join_code=prefill_join_code,
                    errors=["Please upload a valid .csv file."],
                )

            raw = file.stream.read()
            reader = None
            rows = []
            for encoding in ("utf-8-sig", "utf-7", "utf-8", "latin-1"):
                try:
                    stream = io.StringIO(raw.decode(encoding))
                    candidate = csv.DictReader(stream)
                    required = {"first_name", "last_name", "dob"}
                    if candidate.fieldnames and required.issubset(
                        set(candidate.fieldnames)
                    ):
                        rows = [
                            r for r in candidate if any(v.strip() for v in r.values())
                        ]
                        reader = candidate
                        break
                except (UnicodeDecodeError, ValueError):
                    continue

            if reader is None:
                return render_template(
                    "classrooms/provision.html",
                    prefill_join_code=prefill_join_code,
                    errors=[
                        "CSV must have columns: first_name, last_name, dob. Optionally: join_codes"
                    ],
                )

            try:
                students = provision_students_bulk(rows, created_by=session["user_id"])
            except ValueError as e:
                return render_template(
                    "classrooms/provision.html",
                    prefill_join_code=prefill_join_code,
                    errors=e.args[0],
                )

            session["provisioned_students"] = students
            session["provisioned_skipped"] = []
            return redirect(url_for("classrooms.credentials"))
    print("[DEBUG] passing to template:", len(provisioned_students), "students")
    return render_template(
        "classrooms/provision.html",
        prefill_join_code=prefill_join_code,
        provisioned_students=provisioned_students,
        errors=[],
    )


@classrooms_bp.route("/provision/credentials")
@login_required
@teacher_required
def credentials():
    students = session.get("provisioned_students")
    if not students:
        flash("No provisioning data found. Please add students first.", "error")
        return redirect(url_for("classrooms.provision"))

    skipped = session.get("provisioned_skipped", [])
    return render_template(
        "classrooms/credentials.html",
        students=students,
        skipped=skipped,
    )


@classrooms_bp.route("/provision/credentials-csv")
@login_required
@teacher_required
def credentials_csv():
    students = session.get("provisioned_students")
    if not students:
        flash("No provisioning data found.", "error")
        return redirect(url_for("classrooms.provision"))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["first_name", "last_name", "username", "password", "dob", "classrooms"]
    )
    for s in students:
        writer.writerow(
            [
                s["first_name"],
                s["last_name"],
                s["username"],
                s["password"],
                s["dob"],
                ", ".join(s["classrooms"]),
            ]
        )

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=student_credentials.csv"},
    )


@classrooms_bp.route("/provision/template.csv")
@login_required
@teacher_required
def provision_template():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["first_name", "last_name", "dob", "join_codes"])
    writer.writerow(["Jane", "Smith", "2010-05-14", "ABC123"])
    writer.writerow(["John", "Doe", "2011-03-22", ""])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=students_template.csv"},
    )


@classrooms_bp.route(
    "/<int:classroom_id>/students/<int:student_id>/regenerate-qr",
    methods=["POST"],
)
@login_required
@teacher_required
def regenerate_student_qr(classroom_id, student_id):
    classroom, role = _require_member(classroom_id)
    if not classroom:
        return "Classroom not found", 404
    if role != "teacher":
        return "Forbidden", 403

    student = get_user_by_id(student_id)
    member_role = get_member_role(classroom_id, student_id)
    if not student or not member_role:
        return "Student not found in classroom", 404

    if not student["provisional"]:
        return "Forbidden", 403

    regenerate_qr_token(student_id)
    flash(f"QR code regenerated for {student['username']},", "success")
    return redirect(url_for("classrooms.classroom_home", classroom_id=classroom_id))


@classrooms_bp.route("/provision/qr-sheet")
@login_required
@teacher_required
def qr_sheet():
    import qrcode
    from io import BytesIO
    import base64

    students = get_provisioned_students_for_teacher(session["user_id"])
    if not students:
        flash("No provisioned students found.", "error")
        return redirect(url_for("classrooms.provision"))

    base_url = request.host_url.rstrip("/")
    qr_codes = []

    for student in students:
        # fetch full user record to get qr_token

        user = get_user_by_id(student["id"])
        token = user["qr_token"] if user else None
        print(f"[DEBUG] student={student['username']} token={token}")

        if not token:
            qr_codes.append({"student": student, "qr_b64": None})
            continue
        try:
            url = f"{base_url}/auth/qr-login?token={token}"
            img = qrcode.make(url)
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            qr_codes.append({"student": student, "qr_b64": qr_b64})
        except Exception as e:
            print(f"[DEBUG] QR generation error for {student['username']}: {e}")
            qr_codes.append({"student": student, "qr_b64": None})

    return render_template("classrooms/qr_sheet.html", qr_codes=qr_codes)


@classrooms_bp.route("/<int:classroom_id>/students/<int:student_id>/qr")
@login_required
@teacher_required
def show_student_qr(classroom_id, student_id):
    import qrcode
    from io import BytesIO
    import base64

    classroom, role = _require_member(classroom_id)
    if not classroom:
        return "Classroom not found", 404
    if role != "teacher":
        return "Forbidden", 403

    student = get_user_by_id(student_id)
    member_role = get_member_role(classroom_id, student_id)
    if not student or not member_role:
        return "Student not found in classroom", 404
    if not student["provisional"]:
        return "Forbidden", 403

    token = student["qr_token"]
    qr_b64 = None
    if token:
        try:
            base_url = request.host_url.rstrip("/")
            url = f"{base_url}/auth/qr-login?token={token}"
            img = qrcode.make(url)
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception as e:
            flash(f"Could not generate QR code: {e}", "error")
    return render_template(
        "classrooms/student_qr.html",
        classroom=classroom,
        student=student,
        qr_b64=qr_b64,
    )


@classrooms_bp.route("/<int:classroom_id>/students/print-all-qr")
@login_required
@teacher_required
def print_all_qr(classroom_id):
    import qrcode
    from io import BytesIO
    import base64

    classroom, role = _require_member(classroom_id)
    if not classroom:
        return "Classroom not found", 404
    if role != "teacher":
        return "Forbidden", 403

    members = get_classroom_members(classroom_id)
    base_url = request.host_url.rstrip("/")
    badges = []

    for member in members:
        if not member["provisional"]:
            continue
        user = get_user_by_id(member["id"])
        token = user["qr_token"] if user else None
        qr_b64 = None
        if token:
            try:
                url = f"{base_url}/auth/qr-login?token={token}"
                img = qrcode.make(url)
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            except Exception:
                pass
        badges.append({"student": member, "qr_b64": qr_b64})

    if not badges:
        flash("No provisioned students with QR codes in this classroom.", "error")
        return redirect(url_for("classrooms.classroom_home", classroom_id=classroom_id))

    return render_template(
        "classrooms/print_all_qr.html",
        classroom=classroom,
        badges=badges,
    )


# --- assignment attachments


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>/attachments", methods=["POST"]
)
@login_required
@coppa_required
def upload_assignment_attachment(classroom_id, assignment_id):
    classroom, role = _require_member(classroom_id)
    if not classroom:
        return "Classroom not found", 404
    if role != "teacher":
        return "Forbidden", 403

    assignment = get_assignment(assignment_id)
    if not assignment or assignment["classroom_id"] != classroom_id:
        return "Assignment not found", 404

    file = request.files.get("file")

    try:
        add_assignment_attachment(
            assignment_id, file, session["user_id"], current_app._get_current_object()
        )
        flash("File uploaded.", "success")
    except ValueError as e:
        flash(str(e), "error")
    except Exception:
        raise

    return redirect(
        url_for(
            "classrooms.view_assignment",
            classroom_id=classroom_id,
            assignment_id=assignment_id,
        )
    )


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>/attachments/<int:attachment_id>/delete",
    methods=["POST"],
)
@login_required
@coppa_required
def delete_assignment_attachment_route(classroom_id, assignment_id, attachment_id):
    classroom, role = _require_member(classroom_id)
    if not classroom:
        return "Classroom not found", 404
    if role != "teacher":
        return "Forbidden", 403

    delete_assignment_attachment(attachment_id, current_app._get_current_object())
    flash("File deleted.", "success")
    return redirect(
        url_for(
            "classrooms.view_assignment",
            classroom_id=classroom_id,
            assignment_id=assignment_id,
        )
    )


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>/attachments/<int:attachment_id>/download"
)
@login_required
@coppa_required
def download_assignment_attachment(classroom_id, assignment_id, attachment_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or not role:
        return "Forbidden", 403

    from app.models.attachments import get_assignment_attachments

    db_row = next(
        (
            a
            for a in get_assignment_attachments(assignment_id)
            if a["id"] == attachment_id
        ),
        None,
    )
    if not db_row:
        return "File not found", 404

    upload_dir = get_upload_dir(current_app._get_current_object())
    folder = os.path.join(upload_dir, f"assignments/{assignment_id}")
    return send_from_directory(
        folder,
        db_row["filename"],
        as_attachment=True,
        download_name=db_row["original_filename"],
    )


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>/submission/attachments",
    methods=["POST"],
)
@login_required
@coppa_required
def upload_submission_attachment(classroom_id, assignment_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or not role:
        return "Forbidden", 403
    if role != "student":
        return "Forbidden", 403

    assignment = get_assignment(assignment_id)
    if not assignment or assignment["classroom_id"] != classroom_id:
        return "Assignment not found", 404

    submission = get_submission(assignment_id, session["user_id"])
    if not submission:
        create_submission(assignment_id, session["user_id"], "")
        submission = get_submission(assignment_id, session["user_id"])

    file = request.files.get("file")
    import sys

    print(
        f"DEBUG upload: session user_id={session['user_id']}, submission={submission}",
        file=sys.stderr,
    )
    try:
        add_submission_attachment(
            submission["id"],
            file,
            session["user_id"],
            current_app._get_current_object(),
        )
        flash("File uploaded.", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(
        url_for(
            "classrooms.view_assignment",
            classroom_id=classroom_id,
            assignment_id=assignment_id,
        )
    )


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>/submission/attachments/<int:attachment_id>/delete",
    methods=["POST"],
)
@login_required
@coppa_required
def delete_submission_attachment_route(classroom_id, attachment_id, assignment_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or not role:
        return "Forbidden", 403
    submission = get_submission(assignment_id, session["user_id"])

    from app.models import get_db

    if role == "teacher":
        db = get_db()
        row = db.execute(
            "SELECT * FROM submission_attachments WHERE id = ?", (attachment_id,)
        ).fetchone()
    else:
        if not submission:
            return "Forbidden", 403
        attachments = get_submission_attachments(submission["id"])
        row = next((a for a in attachments if a["id"] == attachment_id), None)

    if not row:
        return "File not found", 404

    delete_submission_attachment(attachment_id, current_app._get_current_object())
    flash("File deleted.", "success")
    return redirect(
        url_for(
            "classrooms.view_assignment",
            classroom_id=classroom_id,
            assignment_id=assignment_id,
        )
    )


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>/submission/attachments/<int:attachment_id>/download"
)
@login_required
@coppa_required
def download_submission_attachment(classroom_id, assignment_id, attachment_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or not role:
        return "Forbidden", 403

    from app.models import get_db

    db = get_db()
    row = db.execute(
        "SELECT * FROM submission_attachments WHERE id = ?", (attachment_id,)
    ).fetchone()
    if not row:
        return "File not found", 404

    if role == "student":
        submission = get_submission(assignment_id, session["user_id"])
        if not submission or submission["id"] != row["submission_id"]:
            return "Forbidden", 403

    upload_dir = get_upload_dir(current_app._get_current_object())
    folder = os.path.join(upload_dir, f"submissions/{row['submission_id']}")
    return send_from_directory(
        folder,
        row["filename"],
        as_attachment=True,
        download_name=row["original_filename"],
    )


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>/print-submissions"
)
@login_required
@coppa_required
def print_submissions(classroom_id, assignment_id):
    classroom, role = _require_member(classroom_id)
    if not classroom:
        return "Classroom not found", 404
    if role != "teacher":
        return "Forbidden", 403

    assignment = get_assignment(assignment_id)
    if not assignment or assignment["classroom_id"] != classroom_id:
        return "Assignment not found", 404

    submissions = get_submissions_for_assignment(assignment_id)

    submissions_with_attachments = []
    for sub in submissions:
        attachments = get_assignment_attachments(sub["id"])
        submissions_with_attachments.append(
            {
                "submission": sub,
                "attachments": attachments,
            }
        )
    return render_template(
        "classrooms/print_submissions.html",
        classroom=classroom,
        assignment=assignment,
        submissions=submissions_with_attachments,
    )
