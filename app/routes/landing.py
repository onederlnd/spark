from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    current_app,
)
from app.models.waitlist import add_to_waitlist
from app.utils.email import send_waitlist_confirmation, send_waitlist_admin_notification

marketing_bp = Blueprint("landing", __name__)


@marketing_bp.route("/")
def index():
    from flask import session

    if session.get("user_id"):
        return redirect(url_for("feed.index"))
    return render_template("landing/index.html")


@marketing_bp.route("/waitlist", methods=["POST"])
def waitlist():
    email = request.form.get("email", "").strip()
    if not email or "@" not in email:
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("landing.index") + "#waitlist")

    added = add_to_waitlist(email)
    if added:
        try:
            send_waitlist_confirmation(email)
        except Exception as e:
            current_app.logger.error(f"Waitlist confirm email failed: {e}")
        try:
            send_waitlist_admin_notification(email)
        except Exception as e:
            current_app.logger.error(f"Admin notify email failed: {e}")

    return redirect(url_for("landing.thankyou"))


@marketing_bp.route("/waitlist/thank-you")
def thankyou():
    return render_template("landing/thankyou.html")
