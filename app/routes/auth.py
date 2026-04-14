# app/routes/auth.py

import os
from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from datetime import datetime, timezone
from app.models.user import (
    create_user,
    check_password,
    get_user_by_id,
    get_user_by_email,
)
from app.models import get_db
from app.models.notifications import create_notification
from app.routes.settings import update_user_password
from app.utils.brute_force import is_locked_out, record_failure, record_success
from app.utils.rate_limit import rate_limit
from app.utils.auth import current_user, login_required, teacher_required
from app.utils.email import send_welcome_email, send_password_reset_email
from app.utils.password_reset import generate_reset_token, verify_reset_token


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
@rate_limit(max_requests=35, window_seconds=60)
def register():
    if os.environ.get("REGISTERATON_OPEN", "true").lower() == "false":
        return redirect(url_for("landing.index"))

    from app.utils.sanitize import sanitize_username, sanitize_plain

    if request.method == "POST":
        username = sanitize_username(request.form.get("username"))
        password = request.form["password"]
        bio = sanitize_plain(request.form.get("bio", ""), max_length=300)
        dob = request.form.get("dob")
        email = request.form.get("email", "").strip() or None

        if not dob:
            flash("Date of Birth is required.")
            return render_template("auth/register.html")

        role = request.form.get("role", "student")
        role = role if role in ("teacher", "student") else "student"

        if not username or not password:
            flash("Username and password are required", "error")
            return render_template("auth/register.html")

        success, error = create_user(
            username, password, bio, role=role, dob=dob, email=email
        )

        if success:  # ← indented inside POST block
            db = get_db()

            from datetime import date

            try:
                dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
                today = date.today()
                age = (
                    today.year
                    - dob_date.year
                    - ((today.month, today.day) < (dob_date.month, dob_date.day))
                )
            except ValueError:
                age = 99

            if role == "student" and age < 13:
                teachers = db.execute(
                    "SELECT id FROM users WHERE role='teacher'"
                ).fetchall()
                for teacher in teachers:
                    create_notification(
                        user_id=teacher["id"],
                        message=f"{username} has pending COPPA approval",
                        type="coppa",
                        link="/auth/coppa/pending",
                    )

            invite_token = request.args.get("invite") or request.form.get("invite")
            if invite_token and email:
                from app.models.classroom import (
                    get_invite_by_token,
                    accept_classroom_invite,
                )

                invite = get_invite_by_token(invite_token)
                if invite and invite["email"].lower() == email.lower():
                    db = get_db()
                    user = db.execute(
                        "SELECT id FROM users WHERE username = ?", (username,)
                    ).fetchone()
                    if user:
                        accept_classroom_invite(invite_token, user["id"])

            if email:
                send_welcome_email(email, username)

            flash("Account created! Please log in.", "success")
            return redirect(url_for("auth.login"))

        elif error:  # ← was unreachable before
            flash(error, "error")

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    from app.models.classroom import get_invite_by_token, accept_classroom_invite
    from app.models import get_db

    if request.method == "POST":
        username_or_email = request.form["username"].strip()
        password = request.form["password"]
        ip = request.remote_addr
        locked, seconds_remaining = is_locked_out(username_or_email, ip)
        if locked:
            minutes = seconds_remaining // 60 + 1
            flash(
                f"Too many failed attempts. Ask your teacher to unlock your account, or try again in {minutes} minutes",
                "error",
            )
            return render_template("auth/login.html")

        user = check_password(username_or_email, password)
        if user:
            record_success(user["username"])
            session.clear()

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["last_active"] = datetime.now(timezone.utc).isoformat()
            session["coppa_status"] = user["coppa_status"]
            session["role"] = user["role"]

            db = get_db()
            db.execute(
                "INSERT INTO login_events (user_id, method) VALUES (?, ?)",
                (user["id"], "password"),
            )
            db.commit()

            invite_token = request.args.get("invite")
            if invite_token:
                invite = get_invite_by_token(invite_token)
                if (
                    invite
                    and user["email"]
                    and invite["email"].lower() == user["email"].lower()
                ):
                    accept_classroom_invite(invite_token, user["id"])
                    flash(
                        f"You've been added to {invite['classroom_name']}!", "success"
                    )

            if user["role"] in ("teacher", "admin") and not user["tour_seen"]:
                return redirect(url_for("onboarding.welcome"))

            return redirect(url_for("feed.index"))

        else:
            record_failure(username_or_email, ip)
            flash("Invalid username or password", "error")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    user_id = session.get("user_id")
    if user_id:
        db = get_db()
        db.execute(
            "INSERT INTO session_events (user_id, event_type) VALUES (?, ?)",
            (user_id, "logout"),
        )
        db.commit()
    session.clear()

    return redirect(url_for("feed.index"))


# --- coppa


@auth_bp.route("/coppa/notice")
@login_required
def coppa_notice():
    """show to students whose COPPA status is pending"""
    student = get_user_by_id(session.get("user_id"))

    return render_template("coppa_notice.html", student=student)


@auth_bp.route("/coppa/approve/<int:user_id>", methods=["POST"])
@login_required
@teacher_required
def coppa_approve(user_id):
    """Teacher approves a student under COPPA"""
    user = current_user()

    if not user or user["role"] != "teacher":
        return "Forbidden", 403

    db = get_db()

    student = db.execute(
        "SELECT id, username, role FROM users WHERE id=?", (user_id,)
    ).fetchone()

    if not student:
        flash("Student not found", "error")
        return redirect(url_for("auth.coppa_pending"))

    db.execute("UPDATE users SET coppa_status='approved' WHERE id=?", (user_id,))
    db.commit()

    flash(f"{student['username']} approved successfully", "success")
    return redirect(url_for("auth.coppa_pending"))


@auth_bp.route("/coppa/pending")
@login_required
@teacher_required
def coppa_pending():
    """Teacher dashboard for approving students under 13."""

    db = get_db()

    pending_students = db.execute(
        "SELECT id, username, dob, role FROM users WHERE coppa_status='pending'"
    ).fetchall()

    return render_template("coppa_pending.html", pending_students=pending_students)


@auth_bp.route("/coppa/deny/<int:user_id>", methods=["POST"])
@login_required
@teacher_required
def coppa_deny(user_id):

    db = get_db()

    student = db.execute(
        "SELECT id, username, role FROM users WHERE id=?", (user_id,)
    ).fetchone()

    if not student or student["role"] != "student":
        flash("Invalid target", "error")
        return redirect(url_for("auth.coppa_pending"))

    db.execute("UPDATE users SET coppa_status='denied' WHERE id=?", (user_id,))
    db.commit()

    flash(f"{student['username']} denied successfully", "success")
    return redirect(url_for("auth.coppa_pending"))


# Terms & Privacy
@auth_bp.route("/terms")
def terms():
    return render_template("auth/terms.html")


@auth_bp.route("/privacy")
def privacy():
    return render_template("auth/terms.html")


@auth_bp.route("/qr-login")
@rate_limit(max_requests=20, window_seconds=60)
def qr_login():
    token = request.args.get("token", "").strip()
    if not token:
        flash("Invalid QR code.", "error")
        return redirect(url_for("auth.login"))

    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE qr_token = ? AND provisional = 1", (token,)
    ).fetchone()

    if not user:
        flash("Invalid or expired QR code.", "error")
        return redirect(url_for("auth.login"))

    ip = request.remote_addr
    locked, seconds_remaining = is_locked_out(user["username"], ip)
    if locked:
        minutes = seconds_remaining // 60 + 1
        flash(
            f"This account is locked. Ask your teacher to unlock it, or try again in {minutes} minutes.",
            "error",
        )
        return redirect(url_for("auth.login"))

    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["last_active"] = datetime.now(timezone.utc).isoformat()
    session["coppa_status"] = user["coppa_status"]
    session["role"] = user["role"]

    db.execute(
        "INSERT INTO login_events (user_id, method) VALUES (?, ?)", (user["id"], "qr")
    )
    db.commit()

    if user["role"] in ("teacher", "admin") and not user["tour_seen"]:
        return redirect(url_for("onboarding.welcome"))
    return redirect(url_for("feed.index"))


@auth_bp.route("/validate-join-code")
def validate_join_code():
    """Auth helper to pull join codes directly from the json in api."""
    from flask import jsonify
    from app.models.classroom import get_classroom_by_join_code

    code = request.args.get("code", "").strip()
    if not code:
        return jsonify({"valid": False, "error": "No code provided."})
    classroom = get_classroom_by_join_code(code)
    if not classroom:
        return jsonify({"valid": False, "error": "Invalid join code."})
    return jsonify(
        {
            "valid": True,
            "classroom_id": classroom["id"],
            "classroom_name": classroom["name"],
        }
    )


@auth_bp.route("/register/student", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def register_student():
    from app.utils.sanitize import sanitize_plain
    from app.models.classroom import get_classroom_by_join_code, join_classroom

    first_name = sanitize_plain(request.form.get("first_name").strip(), max_length=50)
    last_name = sanitize_plain(request.form.get("last_name").strip(), max_length=50)
    password = request.form.get("password", "")
    dob = request.form.get("dob", "")
    email = request.form.get("email", "").strip() or None
    join_code = request.form.get("join_code", "").strip()

    if not first_name or not last_name or not password or not dob or not join_code:
        flash("All required fields must be filled in.", "error")
        return redirect(url_for("auth.register"))

    # age check
    from datetime import date

    try:
        dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
        today = date.today()
        age = (
            today.year
            - dob_date.year
            - ((today.month, today.day) < (dob_date.month, dob_date.day))
        )
    except ValueError:
        flash("Invalid date of birth.", "error")
        return redirect(url_for("auth.register"))

    if age < 13:
        flash("Students under 13 must be provisioned by a teacher.", "error")
        return redirect(url_for("auth.register"))

    # validate join code
    classroom = get_classroom_by_join_code(join_code)
    if not classroom:
        flash("Invalid join code.", "error")
        return redirect(url_for("auth.register"))

    # auto-generate username
    db = get_db()
    base = f"{first_name.lower()}.{last_name.lower()}"
    username = base
    counter = 1
    while db.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
        username = f"{base}{counter}"
        counter += 1

    display_name = f"{first_name} {last_name}"

    success, error = create_user(
        username=username,
        password=password,
        bio="",
        role="student",
        dob=dob,
        email=email,
    )

    if not success:
        flash(error or "Could not create account.", "error")
        return redirect(url_for("auth.register"))

    user = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    user_id = user["id"]

    db.execute(
        "UPDATE users SET display_name = ? WHERE id = ?", (display_name, user_id)
    )
    db.commit()

    join_classroom(classroom["id"], user_id, role="student")

    if email:
        send_welcome_email(email, username)

    flash("Account created! Please log in.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register/teacher", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def register_teacher():
    from app.utils.sanitize import sanitize_plain

    first_name = sanitize_plain(
        request.form.get("first_name", "").strip(), max_length=50
    )
    last_name = sanitize_plain(request.form.get("last_name", "").strip(), max_length=50)
    password = request.form.get("password", "")
    dob = request.form.get("dob", "")
    email = request.form.get("email", "")

    if not first_name or not last_name or not password or not dob or not email:
        flash("All fields are required.", "error")
        return redirect(url_for("auth.register"))

    # auto-generate username
    db = get_db()
    base = f"teacher.{first_name.lower()}.{last_name.lower()}"
    username = base
    counter = 1
    while db.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
        username = f"{base}{counter}"
        counter += 1

    display_name = f"{first_name} {last_name}"

    success, error = create_user(
        username=username,
        password=password,
        bio="",
        role="teacher",
        dob=dob,
        email=email,
    )

    if not success:
        flash(error or "Could not create account.", "error")
        return redirect(url_for("auth.register"))

    user = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    user_id = user["id"]

    db.execute(
        "UPDATE users SET display_name = ? WHERE id = ?", (display_name, user_id)
    )
    db.commit()

    if email:
        send_welcome_email(email, username)

    flash("Account created! Please log in.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@rate_limit(max_requests=5, window_seconds=300)
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email").strip().lower()
        user = get_user_by_email(email)
        if user:
            token = generate_reset_token(user["id"])
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            try:
                send_password_reset_email(email, user["username"], reset_url)
            except Exception:
                pass
        flash(
            "If that email is registered, you'll receive a reset link shortly.", "info"
        )
        return redirect(url_for("auth.forgot_password"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user_id = verify_reset_token(token)
    if not user_id:
        flash("That reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        user_id = verify_reset_token(token)
        if not user_id:
            flash("Your reset link expired. Please request a new one.", "error")

            return redirect(url_for("auth.forgot_password"))

        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("auth/reset_password.html", token=token)

        if password != confirm:
            flash("Passwords do not match", "error")
            return render_template("auth/reset_password.html", token=token)

        update_user_password(user_id, password)

        flash("Password updated. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)
