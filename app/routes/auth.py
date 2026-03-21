# app/routes/auth.py

from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from datetime import datetime, timezone
from app.models.user import create_user, check_password, get_user_by_id
from app.models import get_db
from app.models.notifications import create_notification
from app.utils.brute_force import is_locked_out, record_failure, record_success
from app.utils.rate_limit import rate_limit
from app.utils.auth import current_user, login_required, teacher_required


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
@rate_limit(max_requests=35, window_seconds=60)
def register():
    from app.utils.sanitize import sanitize_username, sanitize_plain

    if request.method == "POST":
        username = sanitize_username(request.form.get("username"))
        password = request.form["password"]
        bio = sanitize_plain(request.form.get("bio", ""), max_length=300)
        dob = request.form.get("dob")

        if not dob:
            flash("Date of Birth is required.")
            return render_template("auth/register.html")

        role = request.form.get("role", "student")
        role = role if role in ("teacher", "student") else "student"

        if not username or not password:
            flash("Username and password are required", "error")
            return render_template("auth/register.html")

        success, error = create_user(username, password, bio, role=role, dob=dob)
        if success:
            db = get_db()

            teachers = db.execute(
                "SELECT id FROM users WHERE role='teacher'"
            ).fetchall()

            for teacher in teachers:
                create_notification(
                    user_id=teacher["id"],
                    message=f"{username} has pending COPPA approval",
                    type="coppa",
                    link="/auth/coppa/approve",
                )

            flash("Account created! Please log in.", "success")
            return redirect(url_for("auth.login"))
        if error:
            flash(error, "error")

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        ip = request.remote_addr
        locked, seconds_remaining = is_locked_out(username, ip)
        if locked:
            minutes = seconds_remaining // 60 + 1
            flash(f"Too many failed attempts. Try again in {minutes} minutes.")
            return render_template("auth/login.html")

        user = check_password(username, password)
        if user:
            record_success(username)
            session.clear()

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["last_active"] = datetime.now(timezone.utc).isoformat()
            session["coppa_status"] = user["coppa_status"]
            session["role"] = user["role"]

            return redirect(url_for("feed.index"))
        else:
            record_failure(username, ip)
            flash("Invalid username or password", "error")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
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

    if student["role"] != "student":
        flash("Invalid approval target", "error")
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
        "SELECT id, username, dob FROM users WHERE coppa_status='pending'"
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
        "SELECT * FROM users WHERE qr_token = ? AND provsional = 1", (token,)
    ).fetchone()

    if not user:
        flash("Invalid or expired QR code.", "error")
        return redirect(url_for("auth.login"))

    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["last_active"] = datetime.now(timezone.utc).isoformat()
    session["coppa_status"] = user["coppa_status"]
    session["role"] = user["role"]

    return redirect(url_for("classroom.dashboard"))
