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
                subject="You're on the SparK waitlist!",
                recipients=[email],  # ✅ signup email, not sender
                body="Thanks for signing up! We'll be in touch soon.",
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
                    body=f"New signup: {email}",
                )
                mail.send(msg)  # ✅ inside the if admin_email block
        except Exception as e:
            current_app.logger.error(f"Admin notify email failed: {e}")

    return redirect(url_for("landing.thankyou"))


@marketing_bp.route("/waitlist/thank-you")
def thankyou():
    return render_template("landing/thankyou.html")
