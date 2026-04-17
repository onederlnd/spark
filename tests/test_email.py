from unittest.mock import patch


# --- mail extension is initialized ---


def test_mail_extension_is_configured(app):
    assert app.config.get("MAIL_SERVER") is not None
    assert app.config.get("MAIL_USERNAME") is not None
    assert app.config.get("MAIL_USE_TLS") is True
    assert app.config.get("MAIL_USE_SSL") is False
    assert app.config.get("MAIL_PORT") == 587


# --- confirmation email is attempted on signup ---


def test_waitlist_signup_attempts_confirmation_email(client, app):
    with patch("app.routes.landing.send_waitlist_confirmation") as mock_confirm:
        with patch(
            "app.routes.landing.add_to_waitlist", return_value=(True, "fake-token")
        ):
            client.post("/waitlist", data={"email": "emailtest@example.com"})
            assert mock_confirm.called


def test_waitlist_signup_attempts_admin_notification(client, app):
    app.config["ADMIN_EMAIL"] = "admin@example.com"
    with patch("app.routes.landing.send_waitlist_admin_notification") as mock_admin:
        with patch(
            "app.routes.landing.verify_waitlist_email",
            return_value="notify@example.com",
        ):
            client.get("/waitlist/verify/fake-token")
            assert mock_admin.called


# --- no email sent for duplicate signup ---


def test_no_email_sent_for_duplicate(client):
    with patch("app.routes.landing.add_to_waitlist", return_value=(False, None)):
        with patch("app.routes.landing.send_waitlist_confirmation") as mock_confirm:
            client.post("/waitlist", data={"email": "dupe@example.com"})
            assert not mock_confirm.called


# --- no email sent for invalid input ---


def test_no_email_sent_for_invalid_email(client):
    with patch("app.routes.landing.send_waitlist_confirmation") as mock_confirm:
        client.post("/waitlist", data={"email": "notanemail"})
        assert not mock_confirm.called


# --- mail send failure does not crash the route ---


def test_mail_failure_does_not_break_signup(client):
    with patch(
        "app.routes.landing.send_waitlist_confirmation",
        side_effect=Exception("SMTP down"),
    ):
        resp = client.post(
            "/waitlist", data={"email": "fail@example.com"}, follow_redirects=True
        )

        assert resp.status_code == 200
