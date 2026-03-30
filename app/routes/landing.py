from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    current_app,
)
from flask_mail import Message
from app.extensions import mail
from app.models.waitlist import add_to_waitlist
from datetime import datetime, timezone

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
        # Confirmation to user
        try:
            msg = Message(
                subject="You're on the SparK waitlist! ⚡",
                recipients=[email],  # ✅ signup email, not sender
                html=render_template("email/waitlist_confirmation.html"),
            )
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Waitlist confirm email failed: {e}")

        # Notify admin
        try:
            admin_email = current_app.config.get("ADMIN_EMAIL")
            if admin_email:
                msg = Message(
                    subject="New SparK waitlist signup",
                    recipients=[admin_email],
                    html=render_template(
                        "email/admin_notification.html",
                        email=email,
                        timestamp=datetime.now(timezone.utc).strftime(
                            "%B %d, %Y at %I:%M %p UTC"
                        ),
                    ),
                )
                mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Admin notify email failed: {e}")

    return redirect(url_for("landing.thankyou"))


@marketing_bp.route("/waitlist/thank-you")
def thankyou():
    return render_template("landing/thankyou.html")
