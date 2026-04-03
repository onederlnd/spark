# app/routes/reports.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.report import (
    create_report,
    get_reports_for_classroom,
    resolve_reports,
    get_reports_for_post,
)
from app.models.post import delete_post, get_post, unhide_post
from app.models.notifications import create_notification
from app.models.classroom import get_classroom
from app.utils.auth import login_required, is_teacher_in_classroom
from app.utils.rate_limit import rate_limit
from app.utils.sanitize import sanitize_plain

reports_bp = Blueprint("moderation", __name__, url_prefix="/moderation")

REASON_MAX = 100
DESCRIPTION_MAX = 1000


@reports_bp.route("/report", methods=["POST"])
@login_required
@rate_limit(max_requests=10, window_seconds=60)
def submit_report():
    """Allows students to submit report"""
    post_id = request.form.get("post_id", type=int)

    if not post_id:
        flash("Invalid post.", "error")
        return redirect(request.referrer or url_for("feed.index"))

    reason = sanitize_plain(request.form.get("reason", ""), max_length=REASON_MAX)

    if not reason:
        flash("Reason required.", "error")
        return redirect(request.referrer or url_for("feed.index"))

    description = sanitize_plain(
        request.form.get("description", ""), max_length=DESCRIPTION_MAX
    )

    user_id = session.get("user_id")
    report_id = create_report(post_id, user_id, reason, description)

    if report_id is None:
        flash("Already reported", "warning")
    else:
        flash("Report submitted successfully.", "success")

    post = get_post(post_id)
    if post and post["classroom_id"]:
        classroom = get_classroom(post["classroom_id"])
        if classroom:
            create_notification(
                user_id=classroom["teacher_id"],
                type="report",
                message=f"A post in {classroom['name']} was reported.",
                link=url_for(
                    "moderation.moderation_dashboard", classroom_id=classroom["id"]
                ),
            )

    return redirect(request.referrer or url_for("feed.index"))


@reports_bp.route("/queue/<int:classroom_id>", methods=["GET"])
@login_required
def moderation_dashboard(classroom_id):
    """Show moderation dashboard for allowing/denying posts"""
    if not is_teacher_in_classroom(classroom_id):
        return "Forbidden", 403

    flagged_posts = get_reports_for_classroom(classroom_id)

    detailed = []
    for post in flagged_posts:
        individual_reports = get_reports_for_post(post["post_id"])
        detailed.append(
            {
                "post": post,
                "reports": individual_reports,
            }
        )

    return render_template("reports.html", detailed=detailed, classroom_id=classroom_id)


@reports_bp.route("/reports/<int:post_id>/resolve", methods=["POST"])
@login_required
def mark_post_reviewed_allowed(post_id):
    """Mark post resolved -- allowing it to stay"""

    post = get_post(post_id)
    if not post:
        return "Post not found", 404

    if not is_teacher_in_classroom(post["classroom_id"]):
        return "Forbidden", 403

    unhide_post(post_id)
    resolve_reports(post_id, session["user_id"], "allowed")
    flash("Post reviewed and allowed.", "success")
    return redirect(
        request.referrer
        or url_for("moderation.moderation_dashboard", classroom_id=post["classroom_id"])
    )


@reports_bp.route("/reports/<int:post_id>/delete", methods=["POST"])
@login_required
def mark_post_reviewed_denied(post_id):
    """Delete reviewed post."""

    post = get_post(post_id)

    if not post:
        return "Post not found", 404

    if not is_teacher_in_classroom(post["classroom_id"]):
        return "Forbidden", 403

    delete_post(post_id)
    resolve_reports(post_id, session["user_id"], "deleted")
    flash("Post deleted.", "success")

    return redirect(
        request.referrer
        or url_for(
            "moderation.moderation_dashboard", classroom_id=post["classroom_id"]
        ),
    )
