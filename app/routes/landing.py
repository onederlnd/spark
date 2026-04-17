# app/routes/landing.py
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    current_app,
)
from app import csrf
from app.models.waitlist import add_to_waitlist, verify_waitlist_email
from app.utils.email import send_waitlist_confirmation, send_waitlist_admin_notification

marketing_bp = Blueprint("landing", __name__)


@marketing_bp.route("/")
def index():
    from flask import session

    if session.get("user_id"):
        return redirect(url_for("feed.index"))
    return render_template("landing/index.html")


@marketing_bp.route("/waitlist", methods=["POST"])
@csrf.exempt
def waitlist():
    email = request.form.get("email", "").strip()
    if not email or "@" not in email:
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("landing.index") + "#waitlist")

    added, token = add_to_waitlist(email)  # unpack the token now
    current_app.logger.warning(f"WAITLIST ADD RESULT: added={added}, token={token}")
    if added:
        try:
            send_waitlist_confirmation(email, token)  # sends verify link
        except Exception as e:
            current_app.logger.error(f"Waitlist confirm email failed: {e}")
    return redirect(url_for("landing.thankyou"))


@marketing_bp.route("/waitlist/verify/<token>")
def verify_waitlist(token):
    email = verify_waitlist_email(token)  # from waitlist.py
    if not email:
        flash("This verification link is invalid or has already been used.", "error")
        return redirect(url_for("landing.index"))

    try:
        send_waitlist_admin_notification(email)  # now fires post-verification
    except Exception as e:
        current_app.logger.error(f"Admin notify email failed: {e}")

    flash("You're confirmed — we'll be in touch!", "success")
    return redirect(url_for("landing.thankyou"))


@marketing_bp.route("/waitlist/thank-you")
def thankyou():
    return render_template("landing/thankyou.html")
