from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from app.utils.auth import login_required, teacher_required
from app.utils.sanitize import sanitize_plain
from app.models.bug_reports import (
    create_bug_report,
    get_bug_reports_by_user,
)


bug_reports_bp = Blueprint("bug_reports", __name__, url_prefix="/bug-reports")


@bug_reports_bp.route("/submit", methods=["GET", "POST"])
@login_required
@teacher_required
def submit():
    if request.method == "POST":
        title = sanitize_plain(request.form.get("title", ""), max_length=200)
        description = sanitize_plain(
            request.form.get("description", ""), max_length=2000
        )
        severity = request.form.get("severity", "low")

        if severity not in ("low", "medium", "high"):
            severity = "low"

        if not title or not description:
            flash("Title and description are required.", "error")
            return render_template("bug_reports/submit.html")

        create_bug_report(session["user_id"], title, description, severity)
        flash("Bug report submitted. Thank you!", "success")
        return redirect(url_for("bug_reports.my_reports"))
    return render_template("bug_reports/submit.html")


@bug_reports_bp.route("/my-reports")
@login_required
@teacher_required
def my_reports():
    reports = get_bug_reports_by_user(session["user_id"])
    return render_template("bug_reports/my_reports.html", reports=reports)
