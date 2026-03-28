from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail


def send_waitlist_confirmation(to_email):
    msg = Message(
        subject="You're on the SparK waitlist!",
        recipient=[to_email],
        html=render_template("email/waitlist_confirmation.html", email=to_email),
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
    )
    mail.send(msg)


def send_waitlist_admin_notification(to_email):
    admin_email = current_app.config.get("ADMIN_EMAIL")
    if not admin_email:
        return
    msg = Message(
        subject=f"New waitlist signup: {to_email}",
        recipients=[admin_email],
        body=f"New wailist signup:\n\n{to_email}",
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
    )
    mail.send(msg)
