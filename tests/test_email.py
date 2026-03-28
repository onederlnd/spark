from unittest.mock import patch
from flask_mail import Message


# --- mail extension is initialized ---


def test_mail_extension_is_configured(app):
    assert app.config.get("MAIL_SERVER") is not None
    assert app.config.get("MAIL_USERNAME") is not None
    assert app.config.get("MAIL_USE_TLS") is True
    assert app.config.get("MAIL_USE_SSL") is False
    assert app.config.get("MAIL_PORT") == 587


# --- confirmation email is attempted on signup ---


def test_waitlist_signup_attempts_confirmation_email(client, app):
    app.config["ADMIN_EMAIL"] = "admin_email@example.com"
    with patch("app.routes.landing.mail.send") as mock_send:
        client.post("/waitlist", data={"email": "emailtest@example.com"})
        assert mock_send.called
        first_call = mock_send.call_args_list[0][0][0]
        assert isinstance(first_call, Message)
        assert "emailtest@example.com" in first_call.recipients


# --- admin notification email is attempted on signup ---


def test_waitlist_signup_attempts_admin_notification(client, app):
    app.config["ADMIN_EMAIL"] = "admin@example.com"
    with patch("app.routes.landing.mail.send") as mock_send:
        client.post("/waitlist", data={"email": "notify@example.com"})
        assert mock_send.call_count == 2
        admin_msg = mock_send.call_args_list[1][0][0]
        assert "admin@example.com" in admin_msg.recipients


# --- no email sent for duplicate signup ---


def test_no_email_sent_for_duplicate(client):
    client.post("/waitlist", data={"email": "dupe@example.com"})
    with patch("app.routes.landing.mail.send") as mock_send:
        client.post("/waitlist", data={"email": "dupe@example.com"})
        mock_send.assert_not_called()


# --- no email sent for invalid input ---


def test_no_email_sent_for_invalid_email(client):
    with patch("app.routes.landing.mail.send") as mock_send:
        client.post("/waitlist", data={"email": "notvalid"})
        mock_send.assert_not_called()


# --- mail send failure does not crash the route ---


def test_mail_failure_does_not_break_signup(client):
    with patch("app.routes.landing.mail.send", side_effect=Exception("SMTP down")):
        response = client.post(
            "/waitlist",
            data={"email": "resilient@example.com"},
            follow_redirects=False,
        )
    assert response.status_code == 302
    assert "/waitlist/thank-you" in response.headers["Location"]
