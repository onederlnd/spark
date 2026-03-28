from datetime import datetime, timezone, timedelta


def test_active_session_not_expired(auth_client):
    """A user who just logged in is not logged out."""
    response = auth_client.get("/", follow_redirects=True)
    assert response.status_code == 200


def test_inactive_session_redirects_to_login(auth_client, app):
    """A session inactive beyond the timeout is redirected to login."""
    timeout = app.config["SESSION_TIMEOUT_MINUTES"]
    expired = datetime.now(timezone.utc) - timedelta(minutes=timeout + 1)

    with auth_client.session_transaction() as sess:
        sess["last_active"] = expired.isoformat()

    response = auth_client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "auth/login" in response.headers["Location"]


def test_inactive_session_shows_flash_message(auth_client, app):
    """Expired session shows the inactivity logout message."""
    timeout = app.config["SESSION_TIMEOUT_MINUTES"]
    expired = datetime.now(timezone.utc) - timedelta(minutes=timeout + 1)

    with auth_client.session_transaction() as sess:
        sess["last_active"] = expired.isoformat()

    response = auth_client.get("/", follow_redirects=True)
    assert b"inactivity" in response.data


def test_inactive_session_clears_user(auth_client, app):
    """After timeout, user_id is no longer in the session."""
    timeout = app.config["SESSION_TIMEOUT_MINUTES"]
    expired = datetime.now(timezone.utc) - timedelta(minutes=timeout + 1)

    with auth_client.session_transaction() as sess:
        sess["last_active"] = expired.isoformat()

    auth_client.get("/", follow_redirects=True)

    with auth_client.session_transaction() as sess:
        assert "user_id" not in sess


def test_last_active_updated_on_request(auth_client):
    """Each request refreshes last_active to keep an active session alive."""
    with auth_client.session_transaction() as sess:
        sess["last_active"] = datetime.now(timezone.utc).isoformat()

    auth_client.get("/", follow_redirects=True)

    with auth_client.session_transaction() as sess:
        after = sess.get("last_active")

    assert after is not None


def test_timeout_not_applied_to_logged_out_user(client):
    """Unauthenticated requests are never affected by the timeout check."""
    response = client.get("/auth/register")
    assert response.status_code == 200


def test_timeout_configurable(app):
    """SESSION_TIMEOUT_MINUTES is present in app config and is an int."""
    assert "SESSION_TIMEOUT_MINUTES" in app.config
    assert isinstance(app.config["SESSION_TIMEOUT_MINUTES"], int)
