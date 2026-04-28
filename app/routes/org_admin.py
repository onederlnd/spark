# app/routes/org_admin.py

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
)
from app.models import get_db
from app.models.billing import get_org_sub
from app.models.user import create_user
from app.models.organization import (
    get_organization_by_id,
    get_org_teachers,
    get_org_classrooms,
    get_org_coppa_pending,
    deactivate_teacher,
    reactivate_teacher,
)
from app.utils.auth import (
    login_required,
    org_admin_required,
    current_user,
)
from app.utils.stripe_client import (
    create_checkout_session,
    create_billing_portal_session,
)
from app.utils.email import send_welcome_email

org_admin_bp = Blueprint("org_admin", __name__, url_prefix="/org")


def _get_org_or_403():
    from flask import abort

    user = current_user()
    if not user or "org_id" not in user.keys() or not user["org_id"]:
        abort(403)
    org = get_organization_by_id(user["org_id"])
    if not org:
        abort(403)
    return org


@org_admin_bp.route("/dashboard")
@login_required
@org_admin_required
def dashboard():
    org = _get_org_or_403()
    teachers = get_org_teachers(org["id"])
    classrooms = get_org_classrooms(org["id"])
    coppa_pending = get_org_coppa_pending(org["id"])
    return render_template(
        "org_admin/dashboard.html",
        org=org,
        teachers=teachers,
        classrooms=classrooms,
        coppa_pending=coppa_pending,
    )


@org_admin_bp.route("/teachers")
@login_required
@org_admin_required
def teachers():
    org = _get_org_or_403()
    teachers = get_org_teachers(org["id"])
    return render_template("org_admin/teachers.html", org=org, teachers=teachers)


@org_admin_bp.route("/teachers/create", methods=["GET", "POST"])
@login_required
@org_admin_required
def create_teacher():
    from app.utils.sanitize import sanitize_plain

    org = _get_org_or_403()

    if request.method == "POST":
        first_name = sanitize_plain(
            request.form.get("first_name", "").strip(), max_length=50
        )
        last_name = sanitize_plain(
            request.form.get("last_name", "").strip(), max_length=50
        )
        email = sanitize_plain(request.form.get("email", "").strip(), max_length=100)
        password = request.form.get("password", "")
        dob = request.form.get("dob", "")

        if not first_name or not last_name or not email or not password or not dob:
            flash("All fields are required.", "error")
            return render_template("org_admin/create_teacher.html", org=org)

        db = get_db()
        base = f"teacher.{first_name.lower()}.{last_name.lower()}"
        username = base
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
            bio="",
            role="teacher",
            dob=dob,
            email=email,
        )

        if not success:
            flash(error or "Could not create account.", "error")
            return render_template("org_admin/create_teacher.html", org=org)

        user = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        user_id = user["id"]

        db.execute(
            "UPDATE users SET display_name = ?, org_id = ?, created_by = ? WHERE id = ?",
            (display_name, org["id"], session["user_id"], user_id),
        )
        db.commit()

        if email:
            send_welcome_email(email, username)

        flash(f"Teacher account created for {display_name}.", "success")
        return redirect(url_for("org_admin.teachers"))

    return render_template("org_admin/create_teacher.html", org=org)


@org_admin_bp.route("/teachers/<int:user_id>/deactivate", methods=["POST"])
@login_required
@org_admin_required
def deactivate(user_id):
    org = _get_org_or_403()
    deactivate_teacher(user_id, org["id"])
    flash("Teacher account deactivated.", "success")
    return redirect(url_for("org_admin.teachers"))


@org_admin_bp.route("/teachers/<int:user_id>/reactivate", methods=["POST"])
@login_required
@org_admin_required
def reactivate(user_id):
    org = _get_org_or_403()
    reactivate_teacher(user_id, org["id"])
    flash("Teacher account reactivated.", "success")
    return redirect(url_for("org_admin.teachers"))


@org_admin_bp.route("/classrooms")
@login_required
@org_admin_required
def classrooms():
    org = _get_org_or_403()
    classrooms = get_org_classrooms(org["id"])
    return render_template("org_admin/classrooms.html", org=org, classrooms=classrooms)


@org_admin_bp.route("/coppa/approve/<int:user_id>", methods=["POST"])
@login_required
@org_admin_required
def coppa_approve(user_id):
    org = _get_org_or_403()
    db = get_db()
    student = db.execute(
        """
        SELECT u.id, u.username FROM users u
        JOIN classroom_members cm ON cm.user_id = u.id
        JOIN classrooms c ON c.id = cm.classroom_id
        JOIN users t ON t.id = c.teacher_id
        WHERE u.id = ? AND t.org_id = ? AND u.role = 'student'
        LIMIT 1
        """,
        (user_id, org["id"]),
    ).fetchone()

    if not student:
        flash("Student not found in your organization.", "error")
        return redirect(url_for("org_admin.coppa_pending"))

    db.execute("UPDATE users SET coppa_status = 'approved' WHERE id = ?", (user_id,))
    db.commit()
    flash(f"{student['username']} approved.", "success")
    return redirect(url_for("org_admin.coppa_pending"))


@org_admin_bp.route("/coppa/deny/<int:user_id>", methods=["POST"])
@login_required
@org_admin_required
def coppa_deny(user_id):
    org = _get_org_or_403()
    db = get_db()
    student = db.execute(
        """
        SELECT u.id, u.username FROM users u
        JOIN classroom_members cm ON cm.user_id = u.id
        JOIN classrooms c ON c.id = cm.classroom_id
        JOIN users t ON t.id = c.teacher_id
        WHERE u.id = ? AND t.org_id = ? AND u.role = 'student'
        LIMIT 1
        """,
        (user_id, org["id"]),
    ).fetchone()

    if not student:
        flash("Student not found in your organization.", "error")
        return redirect(url_for("org_admin.coppa_pending"))

    db.execute(
        "UPDATE users SET coppa_status = 'denied' WHERE id = ?", (user_id,)
    )  # FIX: UDPATE → UPDATE
    db.commit()
    flash(f"{student['username']} denied.", "success")
    return redirect(url_for("org_admin.coppa_pending"))


@org_admin_bp.route("/coppa/pending")
@login_required
@org_admin_required
def coppa_pending():
    org = _get_org_or_403()
    coppa_pending = get_org_coppa_pending(org["id"])
    return render_template(
        "org_admin/coppa_pending.html", org=org, coppa_pending=coppa_pending
    )


@org_admin_bp.route("/billing")
@login_required
@org_admin_required
def billing():
    org = _get_org_or_403()
    org_sub = get_org_sub(org["id"])

    created_at_display = org["created_at"][:10] if org["created_at"] else "—"

    org = dict(org)
    org["created_at_display"] = created_at_display

    return render_template(
        "org_admin/billing.html",
        org=org,
        org_sub=org_sub,
    )


@org_admin_bp.route("/billing/checkout")
@login_required
@org_admin_required
def checkout():
    from flask import current_app

    org = _get_org_or_403()
    org_sub = get_org_sub(org["id"])
    price_id = current_app.config.get("STRIPE_PRICE_ORG")

    if not price_id:
        flash("Org billing is not configured yet.", "error")
        return redirect(url_for("org_admin.billing"))

    existing_customer = org_sub["sub_stripe_customer_id"] if org_sub else None
    try:
        session_obj = create_checkout_session(
            customer_email=org["billing_email"],
            price_id=price_id,
            success_url=url_for("org_admin.billing", _external=True) + "?upgraded=1",
            cancel_url=url_for("org_admin.billing", _external=True),
            metadata={"org_id": str(org["id"])},
            existing_customr_id=existing_customer,
        )
        return redirect(session_obj.url, code=303)
    except Exception as e:
        current_app.logger.error(f"Org Stripe checkout error: {e}")
        flash("Something went wrong. Please try again", "error")
        return redirect(url_for("org_admin.billing"))


@org_admin_bp.route("/billing/portal")
@login_required
@org_admin_required
def billing_portal():
    from flask import current_app

    org = _get_org_or_403()
    org_sub = get_org_sub(org["id"])
    if not org_sub or not org_sub["sub_stripe_customer_id"]:
        flash("No active subscription found.", "error")
        return redirect(url_for("org_admin.billing"))
    try:
        portal = create_billing_portal_session(
            stripe_customer_id=org_sub["sub_stripe_customer_id"],
            return_url=url_for("org_admin.billing", _external=True),
        )
        return redirect(portal.url, code=303)
    except Exception as e:
        current_app.logger.error(f"Org Stripe portal error: {e}")
        flash("Could not open billing portal. Please try again.", "error")
        return redirect(url_for("org_admin.billing"))
