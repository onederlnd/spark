import csv
import os
import io
import secrets
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
from app.utils.brute_force import unlock_user, is_locked_out
from app.utils.content_filter import add_word, remove_word, get_all_words
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
    invite_coteacher,
    remove_coteacher,
    is_classroom_owner,
)
from app.models.user import (
    get_user_by_id,
    coppa_required,
    mark_onboarded,
    regenerate_qr_token,
)
from app.models.announcement import create_announcement
from app.models.report import get_reports_for_classroom
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
from app.models.notifications import create_notification
from app.routes.settings import update_user_password
from app.models.lesson import (
    create_block,
    get_blocks_for_assignment,
    get_block,
    update_block,
    delete_block,
    reorder_blocks,
    create_choice,
    get_choices_for_blocks,
    delete_choices_for_block,
    save_block_response,
    auto_grade_submission,
    get_block_stats,
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


@classrooms_bp.before_request
def block_parents():
    if session.get("role") == "parent":
        return redirect(url_for("parent.dashboard"))


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
    show_onboarding = not user["onboarded"] and user["role"] in ("teacher", "student")

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

    if _is_teacher(session["user_id"]):
        flash("Teachers must be invited by a classroom owner.", "error")
        return redirect(url_for("classrooms.dashboard"))
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

    join_classroom(classroom["id"], session["user_id"], "student")

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

    members = get_classroom_members(classroom_id)
    members = [dict(m) for m in members]
    for member in members:
        locked, seconds = is_locked_out(member["username"], ip="")
        member["locked_out"] = locked
        member["lockout_remaining"] = seconds

    assignments = get_assignments_for_classroom(classroom_id)
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
        is_owner=is_classroom_owner(classroom_id, session["user_id"]),
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
        auto_grade = 1 if request.form.get("auto_grade") else 0
        attempts_allowed = int(request.form.get("attempts_allowed", 1))
        show_answers = 1 if request.form.get("show_answers") else 0

        if not title:
            return render_template(
                "classrooms/assignments_new.html",
                classroom=classroom,
                resources=resources,
                error="Title is required.",
            )

        assignment_id = create_assignment(
            classroom_id,
            title,
            instructions,
            due_date,
            auto_grade=auto_grade,
            attempts_allowed=attempts_allowed,
            show_answers=show_answers,
        )

        resource_ids = request.form.getlist("resource_ids", type=int)
        if resource_ids:
            attach_resources_to_assignment(assignment_id, resource_ids)

        flash("Lesson created! Add blocks below.", "success")
        return redirect(
            url_for(
                "classrooms.lesson_builder",
                classroom_id=classroom_id,
                assignment_id=assignment_id,
            )
        )

    return render_template(
        "classrooms/assignments_new.html",
        classroom=classroom,
        resources=resources,
    )


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>/builder", methods=["GET"]
)
@login_required
@teacher_required
def lesson_builder(classroom_id, assignment_id):
    classroom, role = _require_member(classroom_id)
    if not classroom:
        return "Classroom not found", 404
    if role != "teacher":
        return "Forbidden", 403

    assignment = get_assignment(assignment_id)
    if not assignment or assignment["classroom_id"] != classroom_id:
        return "Assignment not found", 404

    blocks = get_blocks_for_assignment(assignment_id)
    block_ids = [b["id"] for b in blocks]
    choices_map = get_choices_for_blocks(block_ids)

    return render_template(
        "classrooms/lesson_builder.html",
        classroom=classroom,
        assignment=assignment,
        blocks=blocks,
        choices_map=choices_map,
    )


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

    blocks = get_blocks_for_assignment(assignment_id)
    block_ids = [b["id"] for b in blocks]
    choices_map = get_choices_for_blocks(block_ids)

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
                blocks=blocks,
                choices_map=choices_map,
                error="Submission cannot be empty.",
            )

        create_submission(assignment_id, session["user_id"], body)

        create_notification(
            user_id=classroom["teacher_id"],
            type="submission",
            message=f"{session['username']} submitted {assignment['title']}",
            link=url_for(
                "classrooms.grade_grid",
                classroom_id=classroom_id,
                assignment_id=assignment_id,
            ),
        )
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
        else:
            flash(
                f'Your submission for "{assignment["title"]}" has been saved', "success"
            )

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
        blocks=blocks,
        choices_map=choices_map,
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
    "/<int:classroom_id>/resources/<int:resource_id>/download", methods=["GET"]
)
@login_required
def download_resources(classroom_id, resource_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or not role:
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

        if not submission or not submission["grade"]:
            create_notification(
                user_id=student_id,
                type="grade",
                message=f'Your submission for "{assignment["title"]}" has been graded.',
                link=url_for(
                    "classrooms.view_assignment",
                    classroom_id=classroom_id,
                    assignment_id=assignment_id,
                ),
            )

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
    user = get_user_by_id(session["user_id"])
    if user["role"] != "teacher":
        return "Forbidden", 403
    mark_onboarded(session["user_id"])
    return "", 204


@classrooms_bp.route("/student-onboarding/complete", methods=["POST"])
@login_required
def complete_student_onboarding():
    user = get_user_by_id(session["user_id"])
    if user["role"] != "student":
        return "Forbidden", 403
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
        user = get_user_by_id(student["id"])
        token = user["qr_token"] if user else None

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
        except Exception:
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
        attachments = get_submission_attachments(sub["id"])
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


@classrooms_bp.route(
    "/<int:classroom_id>/students/<int:student_id>/unlock", methods=["POST"]
)
@login_required
@teacher_required
def unlock_student(classroom_id, student_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or role != "teacher":
        return "Forbidden", 403
    student = get_user_by_id(student_id)
    if not student:
        return "Not found", 404
    unlock_user(student["username"])

    flash(f"{student['username']} has been unlocked", "success")
    return redirect(url_for("classrooms.classroom_home", classroom_id=classroom_id))


@classrooms_bp.route("/<int:classroom_id>/coteachers/invite", methods=["POST"])
@login_required
@teacher_required
def invite_coteacher_route(classroom_id):
    from app.utils.email import (
        send_coteacher_invite_email,
        send_coteacher_invite_email_by_email,
    )
    from app.models.classroom import create_classroom_invite

    classroom, role = _require_member(classroom_id)
    if not classroom:
        return "Classroom not found", 404
    if not is_classroom_owner(classroom_id, session["user_id"]):
        return "Forbidden", 403

    username = sanitize_plain(request.form.get("username", "").strip(), max_length=50)
    email = sanitize_plain(request.form.get("email", "").strip(), max_length=200)
    inviter = get_user_by_id(session["user_id"])

    if not username and not email:
        flash("Please enter a username or email address.", "error")
        return redirect(url_for("classrooms.classroom_home", classroom_id=classroom_id))

    if username:
        success, error, invitee_email = invite_coteacher(
            classroom_id, session["user_id"], username
        )
        if success:
            flash(f'"{username}" has been added as a co-teacher.', "success")
            if invitee_email:
                send_coteacher_invite_email(
                    to_email=invitee_email,
                    inviter_username=inviter["username"],
                    classroom_name=classroom["name"],
                )
            if classroom["teacher_id"] != session["user_id"]:
                create_notification(
                    user_id=classroom["teacher_id"],
                    type="coteacher",
                    message=f"{username} joined {classroom['name']} as a co-teacher.",
                    link=url_for(
                        "classrooms.classroom_home", classroom_id=classroom_id
                    ),
                )
        else:
            flash(error, "error")

    elif email:
        if "@" not in email:
            flash("Please enter a valid email address.", "error")
            return redirect(
                url_for("classrooms.classroom_home", classroom_id=classroom_id)
            )

        token = create_classroom_invite(classroom_id, session["user_id"], email)
        invite_url = request.host_url.rstrip("/") + f"/auth/register?invite={token}"
        login_url = request.host_url.rstrip("/") + f"/auth/login?invite={token}"
        send_coteacher_invite_email_by_email(
            to_email=email,
            inviter_username=inviter["username"],
            classroom_name=classroom["name"],
            invite_url=invite_url,
            login_url=login_url,
        )
        flash(f"Invite sent to {email}.", "success")

    return redirect(url_for("classrooms.classroom_home", classroom_id=classroom_id))


@classrooms_bp.route(
    "/<int:classroom_id>/coteachers/<int:target_user_id>/remove", methods=["POST"]
)
@login_required
@teacher_required
def remove_coteacher_route(classroom_id, target_user_id):
    if not is_classroom_owner(classroom_id, session["user_id"]):
        return "Forbidden", 403

    classroom, role = _require_member(classroom_id)
    if not classroom:
        return "Classroom not found.", 404

    if not is_classroom_owner(classroom_id, session["user_id"]):
        return "Forbidden", 403

    success, error = remove_coteacher(classroom_id, session["user_id"], target_user_id)
    if success:
        flash("Co-teacher removed.", "success")
    else:
        flash(error, "error")

    return redirect(url_for("classrooms.classroom_home", classroom_id=classroom_id))


@classrooms_bp.route("/<int:classroom_id>/announcements/new", methods=["GET", "POST"])
@login_required
@coppa_required
def new_announcement(classroom_id):
    classroom, role = _require_member(classroom_id)
    if not classroom:
        return "Classroom not found", 404
    if role != "teacher":
        return "Forbidden", 403

    if request.method == "POST":
        title = sanitize_plain(request.form.get("title", ""), max_length=TITLE_MAX)
        body = sanitize_plain(request.form.get("body", ""), max_length=BODY_MAX)

        if not title or not body:
            return render_template(
                "classrooms/announcement_new.html",
                classroom=classroom,
                error="Title and body are required.",
            )

        create_announcement(classroom_id, session["user_id"], title, body)
        flash("Announcement posted!", "success")
        return redirect(url_for("classrooms.classroom_home", classroom_id=classroom_id))

    return render_template("classrooms/announcement_new.html", classroom=classroom)


@classrooms_bp.route("/<int:classroom_id>/grades.csv")
@login_required
@teacher_required
def export_grades(classroom_id):

    classroom, role = _require_member(classroom_id)
    if not classroom:
        return "Classroom not found", 404
    if role != "teacher":
        return "Forbidden", 403

    assignments = get_assignments_for_classroom(classroom_id)
    members = get_classroom_members(classroom_id)
    students = [m for m in members if m["role"] == "student"]

    grade_map = {}
    for assignment in assignments:
        grid = get_submission_grid(assignment["id"], classroom_id)
        for row in grid:
            grade_map.setdefault(row["user_id"], {})[assignment["id"]] = row

    output = io.StringIO()
    writer = csv.writer(output)

    header = ["username"]
    for a in assignments:
        label = a["title"][:40]
        header += [f"{label} - grade", f"{label} - feedback"]
    writer.writerow(header)

    for student in students:
        row = [student["username"]]
        for a in assignments:
            entry = grade_map.get(student["id"], {}).get(a["id"])
            if entry is None:
                row += ["", ""]
            elif entry["submission_id"] is None:
                row += ["", ""]
            else:
                row += [entry["grade"] or "", entry["feedback"] or ""]
        writer.writerow(row)

    filename = f"{classroom['name'].replace(' ', '_')}_grades.csv"
    filename = filename.encode("ascii", "ignore").decode("ascii")
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@classrooms_bp.route(
    "/<int:classroom_id>/students/<int:student_id>/reset-password",
    methods=["POST"],
)
@login_required
@teacher_required
def reset_student_password(classroom_id, student_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or role != "teacher":
        return "Forbidden", 403

    student = get_user_by_id(student_id)
    member_role = get_member_role(classroom_id, student_id)
    if not student or not member_role:
        return "Student not found in classroom", 404

    new_password = _generate_temp_password()
    update_user_password(student_id, new_password)

    flash(
        f"Password for {student['username']} reset to: {new_password} - share this with the student.",
        "success",
    )
    return redirect(url_for("classrooms.classroom_home", classroom_id=classroom_id))


def _generate_temp_password():
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
    return (
        f"{secrets.choice(_WORDS)}{secrets.choice(_WORDS)}{secrets.randbelow(90) + 10}"
    )


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>/blocks/add",
    methods=["POST"],
)
@login_required
@teacher_required
def add_block(classroom_id, assignment_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or role != "teacher":
        return "Forbidden", 403

    assignment = get_assignment(assignment_id)
    if not assignment or assignment["classroom_id"] != classroom_id:
        return "Assignment not found", 404

    block_type = request.form.get("type", "").strip()
    valid_types = (
        "text",
        "multiple_choice",
        "true_false",
        "short_answer",
        "file_upload",
    )
    if block_type not in valid_types:
        return "Invalid block type", 400

    existing_blocks = get_blocks_for_assignment(assignment_id)
    position = len(existing_blocks)

    body = ""
    if block_type == "true_false":
        body = "True or False?"

    block_id = create_block(
        assignment_id=assignment_id,
        block_type=block_type,
        body=body,
        position=position,
        points=1 if block_type not in ("text", "file_upload") else 0,
    )

    if block_type == "true_false":
        create_choice(block_id, "True", is_correct=0)
        create_choice(block_id, "False", is_correct=0)

    return redirect(
        url_for(
            "classrooms.lesson_builder",
            classroom_id=classroom_id,
            assignment_id=assignment_id,
        )
    )


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>/blocks/<int:block_id>/update",
    methods=["POST"],
)
@login_required
@teacher_required
def update_block_route(classroom_id, assignment_id, block_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or role != "teacher":
        return "Forbidden", 403

    block = get_block(block_id)
    if not block:
        return "Block not found.", 404

    body = sanitize_plain(request.form.get("body", ""), max_length=2000)
    points = int(request.form.get("points", 0))
    required = 1 if request.form.get("required") else 0

    update_block(block_id, body, points, required)

    if block["type"] in ("multiple_choice", "true_false"):
        delete_choices_for_block(block_id)
        choices = request.form.getlist("choices")
        correct_index = request.form.get("correct", type=int)
        for i, choice_body in enumerate(choices):
            choice_body = sanitize_plain(choice_body, max_length=500)
            if choice_body:
                create_choice(
                    block_id, choice_body, is_correct=1 if i == correct_index else 0
                )

    return redirect(
        url_for(
            "classrooms.lesson_builder",
            classroom_id=classroom_id,
            assignment_id=assignment_id,
        )
    )


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>/blocks/<int:block_id>/delete",
    methods=["POST"],
)
@login_required
@teacher_required
def delete_block_route(classroom_id, assignment_id, block_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or role != "teacher":
        return "Forbidden", 403

    block = get_block(block_id)
    if not block:
        return "Block not found", 404

    delete_choices_for_block(block_id)
    delete_block(block_id)

    return redirect(
        url_for(
            "classrooms.lesson_builder",
            classroom_id=classroom_id,
            assignment_id=assignment_id,
        )
    )


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>/blocks/reorder",
    methods=["POST"],
)
@login_required
@teacher_required
def reorder_blocks_route(classroom_id, assignment_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or role != "teacher":
        return "Forbidden", 403

    order = request.get_json()
    if not order or not isinstance(order, list):
        return "Invalid data", 400

    block_positions = [(item["id"], item["position"]) for item in order]
    reorder_blocks(block_positions)
    return "", 204


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>/blocks/publish",
    methods=["POST"],
)
@login_required
@teacher_required
def publish_lesson(classroom_id, assignment_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or role != "teacher":
        return "Forbidden", 403

    assignment = get_assignment(assignment_id)
    if not assignment or assignment["classroom_id"] != classroom_id:
        return "Assignment not found", 404

    members = get_classroom_members(classroom_id)
    for member in members:
        if member["role"] == "student":
            create_notification(
                user_id=member["id"],
                type="assignment",
                message=f"New lesson in {classroom['name']}: {assignment['title']}",
                link=url_for(
                    "classrooms.view_assignment",
                    classroom_id=classroom_id,
                    assignment_id=assignment_id,
                ),
            )

    flash("Lesson published!", "success")
    return redirect(url_for("classrooms.classroom_home", classroom_id=classroom_id))


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>/lesson/submit",
    methods=["POST"],
)
@login_required
@coppa_required
def submit_lesson(classroom_id, assignment_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or role != "student":
        return "Forbidden", 403

    assignment = get_assignment(assignment_id)
    if not assignment or assignment["classroom_id"] != classroom_id:
        return "Assignment not found", 404

    submission_id = create_submission(assignment_id, session["user_id"], "")
    blocks = get_blocks_for_assignment(assignment_id)

    for block in blocks:
        if block["type"] == "text":
            continue
        elif block["type"] in ("multiple_choice", "true_false"):
            choice_id = request.form.get(f"block_{block['id']}", type=int)
            save_block_response(submission_id, block["id"], choice_id=choice_id)
        elif block["type"] == "short_answer":
            body = sanitize_plain(
                request.form.get(f"block_{block['id']}", ""), max_length=5000
            )
            save_block_response(submission_id, block["id"], body=body)

    if assignment["auto_grade"]:
        total = auto_grade_submission(submission_id)
        create_notification(
            user_id=session["user_id"],
            type="grade",
            message=f'Your submission for "{assignment["title"]}" was auto-graded: {total} pts',
            link=url_for(
                "classrooms.view_assignment",
                classroom_id=classroom_id,
                assignment_id=assignment_id,
            ),
        )
    else:
        create_notification(
            user_id=classroom["teacher_id"],
            type="submission",
            message=f'{session["username"]} submitted "{assignment["title"]}"',
            link=url_for(
                "classrooms.grade_grid",
                classroom_id=classroom_id,
                assignment_id=assignment_id,
            ),
        )

    flash("Lesson submitted!", "success")
    return redirect(
        url_for(
            "classrooms.view_assignment",
            classroom_id=classroom_id,
            assignment_id=assignment_id,
        )
    )


@classrooms_bp.route(
    "/<int:classroom_id>/assignments/<int:assignment_id>/results",
    methods=["GET"],
)
@login_required
@teacher_required
def lesson_results(classroom_id, assignment_id):
    classroom, role = _require_member(classroom_id)
    if not classroom or role != "teacher":
        return "Forbidden", 403

    assignment = get_assignment(assignment_id)
    if not assignment or assignment["classroom_id"] != classroom_id:
        return "Assignment not found", 404

    stats = get_block_stats(assignment_id)
    grid = get_submission_grid(assignment_id, classroom_id)

    return render_template(
        "classrooms/lesson_results.html",
        classroom=classroom,
        assignment=assignment,
        stats=stats,
        grid=grid,
    )
