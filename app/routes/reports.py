# app/routes/reports.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.report import create_report, get_reports_for_classroom
from app.models.post import delete_post, get_post
from app.models.report import resolve_reports
from app.models.classroom import get_member_role
from app.utils.auth import login_required

reports_bp = Blueprint("moderation", __name__, url_prefix="/moderation")


@reports_bp.route("/report", methods=["POST"])
@login_required
def submit_report():
    """Allows students to submit report"""
    post_id = request.form.get("post_id", type=int)

    if not post_id:
        flash("Invalid post.", "error")
        return redirect(request.referrer or url_for("feed.index"))

    reason = request.form.get("reason")

    if not reason:
        flash("Reason required.", "error")
        return redirect(request.referrer or url_for("feed.index"))
    description = request.form.get("description")

    user_id = session.get("user_id")

    report_id = create_report(post_id, user_id, reason, description)
    if report_id is None:
        flash("Already reported", "warning")
    else:
        flash("Report submitted successfully.", "success")

    return redirect(request.referrer or url_for("feed.index"))


@reports_bp.route("/reports", methods=["GET"])
@login_required
def get_posts():
    """Show moderation dashboard for allowing/denying posts"""

    classroom_id = request.args.get("classroom_id", type=int)
    if not classroom_id:
        flash("Missing classroom.", "error")
        return redirect(url_for("feed.index"))

    role = get_member_role(classroom_id, session["user_id"])
    if role != "teacher":
        return "Forbidden", 403
    print("[DEBUG] role check:", role)
    reports = get_reports_for_classroom(classroom_id)

    return render_template("reports.html", reports=reports, classroom_id=classroom_id)


@reports_bp.route("/reports/<int:post_id>/resolve", methods=["POST"])
@login_required
def mark_post_reviewed_allowed(post_id):
    """Mark post resolved -- allowing it to stay"""

    post = get_post(post_id)
    if not post:
        return "Post not found", 404

    role = get_member_role(post["classroom_id"], session["user_id"])

    print("[DEBUG] role: ", role)
    print("[DEBUG] user: ", session["user_id"])
    print("[DEBUG] classroom: ", post["classroom_id"])

    if role != "teacher":
        return "Forbidden", 403

    resolve_reports(post_id, session["user_id"], "allowed")
    flash("Post reviewed and allowed.", "success")
    return redirect(
        request.referrer
        or url_for("moderation.get_posts", classroom_id=post["classroom_id"])
    )


@reports_bp.route("/reports/<int:post_id>/delete", methods=["POST"])
@login_required
def mark_post_reviewed_denied(post_id):
    """Delete reviewed post."""

    post = get_post(post_id)

    if not post:
        return "Post not found", 404

    role = get_member_role(post["classroom_id"], session["user_id"])

    if role != "teacher":
        return "Forbidden", 403

    delete_post(post_id)
    resolve_reports(post_id, session["user_id"], "deleted")
    flash("Post deleted.", "success")

    return redirect(
        request.referrer
        or url_for("moderation.get_posts", classroom_id=post["classroom_id"]),
    )
