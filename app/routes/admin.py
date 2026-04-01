import csv
import json
import io
import os
from datetime import datetime, timezone
from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    Response,
)
from app.models.analytics import (
    get_user_counts,
    get_daily_new_users,
    get_daily_logins,
    get_daily_posts,
    get_daily_filter_hits,
    get_daily_rate_limit_hits,
    get_daily_replies,
    get_daily_reports,
    get_daily_session_events,
    get_daily_submissions,
    get_avg_report_resolution_hours,
    get_classroom_completion_rates,
    get_classroom_counts,
    get_coppa_pending,
    get_inactive_students,
    get_report_counts,
    get_login_method_counts,
    get_session_event_counts,
    get_students_with_zero_submissions,
    get_top_active_students_by_posts,
    get_top_active_students_by_submissions,
    get_top_filter_words,
    get_top_rate_limited_routes,
    get_ungraded_submissions_by_teacher,
)
from app.models.feedback import (
    get_all_feedback,
    get_feedback_summary,
    get_feedback_daily,
)
from app.models.waitlist import (
    get_waitlist_summary,
    get_waitlist_all,
    get_waitlist_daily,
)
from app.models.bug_reports import (
    get_all_bug_reports,
    get_bug_report_counts,
    update_bug_report,
)

from app.utils.email import send_acceptance_email


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _get_password():
    return os.environ.get("ALPHA_DASHBOARD_PASSWORD")


def _is_authenticated():
    return session.get("admin_authenticated") is True


def _require_auth():
    if not _get_password():
        from flask import abort

        abort(503)
    if not _is_authenticated():
        return redirect(url_for("admin.login"))
    return None


# --- auth


@admin_bp.route("/alpha/login", methods=["GET", "POST"])
def login():
    if not _get_password():
        return "Dashboard unavailable - ALPHA_DASHBOARD_PASSWORD not set", 503

    if _is_authenticated():
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        password = request.form.get("password", "")
        if password == _get_password():
            session["admin_authenticated"] = True
            return redirect(url_for("admin.dashboard"))
        flash("Incorrect password.", "error")

    return render_template("admin/login.html")


@admin_bp.route("/alpha/logout")
def logout():
    session.pop("admin_authenticated", None)
    return redirect(url_for("admin.login"))


@admin_bp.route("/alpha")
def dashboard():
    guard = _require_auth()
    if guard is not None:
        return guard

    def safe(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            return None

    def safe_list(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs) or []
        except Exception:
            return []

    def rows_to_dicts(rows):
        if not rows:
            return []
        return [dict(row) for row in rows]

    completion = []
    for row in safe_list(get_classroom_completion_rates):
        row = dict(row)
        total = row["assignment_count"] * row["student_count"]
        row["completion_pct"] = (
            round(100.0 * row["submission_count"] / total, 1) if total > 0 else 0
        )
        completion.append(row)

    return render_template(
        "admin/alpha.html",
        # usage
        user_counts=safe(get_user_counts),
        daily_new_users=rows_to_dicts(safe_list(get_daily_new_users)),
        daily_logins=rows_to_dicts(safe_list(get_daily_logins)),
        daily_posts=rows_to_dicts(safe_list(get_daily_posts)),
        daily_replies=rows_to_dicts(safe_list(get_daily_replies)),
        daily_submissions=rows_to_dicts(safe_list(get_daily_submissions)),
        top_students_posts=safe_list(get_top_active_students_by_posts),
        top_students_submissions=safe_list(get_top_active_students_by_submissions),
        login_method_counts=safe_list(get_login_method_counts),
        # safety
        report_counts=safe(get_report_counts),
        daily_reports=rows_to_dicts(safe_list(get_daily_reports)),
        avg_resolution_hours=safe(get_avg_report_resolution_hours),
        top_filter_words=safe_list(get_top_filter_words),
        daily_filter_hits=rows_to_dicts(safe_list(get_daily_filter_hits)),
        coppa_pending=safe_list(get_coppa_pending),
        # classroom
        classroom_counts=safe(get_classroom_counts),
        classroom_completion=completion,
        ungraded_by_teacher=safe_list(get_ungraded_submissions_by_teacher),
        inactive_students=safe_list(get_inactive_students),
        students_zero_submissions=safe_list(get_students_with_zero_submissions),
        # technical
        daily_rate_limit_hits=rows_to_dicts(safe_list(get_daily_rate_limit_hits)),
        top_rate_limited_routes=safe_list(get_top_rate_limited_routes),
        daily_session_events=rows_to_dicts(safe_list(get_daily_session_events)),
        session_event_counts=safe_list(get_session_event_counts),
        # feedback
        feedback_summary=safe(get_feedback_summary),
        feedback_all=safe_list(get_all_feedback),
        feedback_daily=rows_to_dicts(safe_list(get_feedback_daily)),
        # waitlist
        waitlist_summary=safe(get_waitlist_summary),
        waitlist_all=safe_list(get_waitlist_all),
        waitlist_daily=rows_to_dicts(safe_list(get_waitlist_daily)),
        # bug reports
        bug_reports=[dict(r) for r in (get_all_bug_reports() or [])],
        bug_report_counts=get_bug_report_counts(),
        chart_data=json.dumps(
            {
                "dailyUsers": rows_to_dicts(safe_list(get_daily_new_users)),
                "dailyLogins": rows_to_dicts(safe_list(get_daily_logins)),
                "dailyPosts": rows_to_dicts(safe_list(get_daily_posts)),
                "dailySubmissions": rows_to_dicts(safe_list(get_daily_submissions)),
                "dailyReports": rows_to_dicts(safe_list(get_daily_reports)),
                "dailyFilterHits": rows_to_dicts(safe_list(get_daily_filter_hits)),
                "dailyRateLimit": rows_to_dicts(safe_list(get_daily_rate_limit_hits)),
                "dailySession": rows_to_dicts(safe_list(get_daily_session_events)),
                "dailyFeedback": rows_to_dicts(safe_list(get_feedback_daily)),
                "dailyWaitlist": rows_to_dicts(safe_list(get_waitlist_daily)),
            }
        ),
    )


@admin_bp.route("/alpha/export")
def export():
    guard = _require_auth()
    if guard is not None:
        return guard

    import zipfile

    def write_csv(writer, headers, rows):
        writer.writerow(headers)
        for row in rows:
            writer.writerow(
                [
                    row[h] if isinstance(row, dict) else getattr(row, h, "")
                    for h in headers
                ]
            )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        sections = [
            ("usage_daily_users.csv", ["day", "count"], get_daily_new_users()),
            ("usage_daily_logins.csv", ["day", "count"], get_daily_logins()),
            ("usage_daily_posts.csv", ["day", "count"], get_daily_posts()),
            ("usage_daily_submissions.csv", ["day", "count"], get_daily_submissions()),
            ("safety_daily_reports.csv", ["day", "count"], get_daily_reports()),
            ("safety_daily_filter_hits.csv", ["day", "count"], get_daily_filter_hits()),
            (
                "safety_top_filter_words.csv",
                ["word", "hit_count"],
                get_top_filter_words(),
            ),
            (
                "classroom_completion.csv",
                [
                    "classroom_name",
                    "student_count",
                    "assignment_count",
                    "submission_count",
                    "completion_pct",
                ],
                get_classroom_completion_rates(),
            ),
            (
                "classroom_ungraded.csv",
                ["teacher", "ungraded_count"],
                get_ungraded_submissions_by_teacher(),
            ),
            (
                "classroom_inactive.csv",
                ["username", "last_login", "hours_since_login"],
                get_inactive_students(),
            ),
            (
                "technical_rate_limits.csv",
                ["route", "hit_count"],
                get_top_rate_limited_routes(),
            ),
            (
                "technical_session_events.csv",
                ["event_type", "count"],
                get_session_event_counts(),
            ),
        ]
        for filename, headers, rows in sections:
            buf = io.StringIO()
            writer = csv.writer(buf)
            write_csv(writer, headers, rows or [])
            zf.writestr(filename, buf.getvalue())

    zip_buffer.seek(0)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    return Response(
        zip_buffer.getvalue(),
        mimetype="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=spark_alpha_{timestamp}.zip"
        },
    )


@admin_bp.route("/alpha/waitlist/invite/<int:waitlist_id>", methods=["POST"])
def invite_from_waitlist(waitlist_id):
    guard = _require_auth()
    if guard is not None:
        return guard

    db_waitlist = get_waitlist_all()
    entry = next((r for r in db_waitlist if r["id"] == waitlist_id), None)

    if not entry:
        flash("Waitlist entry not found.", "error")
        return redirect(url_for("admin.dashboard"))

    send_acceptance_email(entry["email"])
    flash(f"Invite sent to {entry['email']}", "success")
    return redirect(url_for("admin.dashboard") + "#waitlist")


@admin_bp.route("/alpha/bugs/<int:report_id>/update", methods=["POST"])
def update_bug(report_id):
    guard = _require_auth()
    if guard is not None:
        return guard

    status = request.form.get("status")
    severity = request.form.get("severity")
    admin_notes = request.form.get("admin_notes", "")

    if status in ("open", "in_progress", "resolved"):
        update_bug_report(report_id, status, admin_notes, severity)
        flash("Report updated.", "success")

    return redirect(url_for("admin.dashboard") + "#bugs")
