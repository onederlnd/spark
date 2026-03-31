from flask import current_app, render_template, url_for
from flask_mail import Message
from app.extensions import mail
from datetime import datetime, timezone


def send_welcome_email(email, username):
    try:
        msg = Message(
            subject="Welcome to SparK! ⚡",
            recipients=[email],
            html=render_template(
                "email/welcome.html",
                username=username,
                dashboard_url=url_for("feed.index", _external=True),
            ),
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Welcome email failed: {e}")


def send_acceptance_email(email):
    try:
        msg = Message(
            subject="You're invited to SparK! ⚡",
            recipients=[email],
            html=render_template(
                "email/waitlist_acceptance.html",
                register_url=url_for("auth.register", _external=True),
            ),
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Acceptance email failed: {e}")


def send_waitlist_confirmation(to_email):
    msg = Message(
        subject="You're on the SparK waitlist!",
        recipient=[to_email],
        html=render_template("email/waitlist_confirmation.html", email=to_email),
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
    )
    mail.send(msg)


def send_waitlist_admin_notification(email):
    try:
        admin_email = current_app.config.get("ADMIN_EMAIL")
        if not admin_email:
            return
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


def send_coteacher_invite_email(to_email, inviter_username, classroom_name, login_url):
    try:
        msg = Message(
            subject=f"{inviter_username} invited you to co-teach on SparK",
            recipients=[to_email],
            html=render_template(
                "email/coteacher_invite.html",
                inviter_username=inviter_username,
                classroom_name=classroom_name,
                login_url=login_url,
            ),
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Co-teacher invite email failed: {e}")


def send_coteacher_invite_email_by_email(
    to_email, inviter_username, classroom_name, invite_url, login_url=None
):
    try:
        msg = Message(
            subject=f"{inviter_username} invited you to co-teach on SparK",
            recipients=[to_email],
            html=render_template(
                "email/coteacher_invite.html",
                inviter_username=inviter_username,
                classroom_name=classroom_name,
                invite_url=invite_url,
                login_url=login_url,
            ),
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Co-teacher invite email failed: {e}")
