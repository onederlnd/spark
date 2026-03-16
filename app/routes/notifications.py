# app/routes/notifications.py

from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
)
from app.models.notifications import (
    get_notification,
    mark_all_read,
)
from app.models.user import coppa_required
from app.routes.feed import login_required

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@notifications_bp.route("/")
@login_required
@coppa_required
def view_notifications():
    """Retrieve all notifications"""
    notifications = get_notification(session["user_id"])
    return render_template("notifications.html", notifications=notifications)


@notifications_bp.route("/read", methods=["POST"])
@login_required
@coppa_required
def read_all_notifications():
    """mark all notifications as read"""
    mark_all_read(session["user_id"])
    return redirect("/notifications/")
