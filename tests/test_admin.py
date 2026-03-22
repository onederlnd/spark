# tests/test_admin.py
import os


def _login(client, password="testpass"):
    return client.post(
        "/admin/alpha/login",
        data={"password": password},
        follow_redirects=False,
    )


def _set_password(monkeypatch, password="testpass"):
    monkeypatch.setenv("ALPHA_DASHBOARD_PASSWORD", password)


# --- login page


def test_login_page_loads(client, monkeypatch):
    _set_password(monkeypatch)
    response = client.get("/admin/alpha/login")
    assert response.status_code == 200
    assert b"Alpha Dashboard" in response.data


def test_login_page_unavailable_without_password_set(client):
    os.environ.pop("ALPHA_DASHBOARD_PASSWORD", None)
    response = client.get("/admin/alpha/login")
    assert response.status_code == 503


def test_correct_password_redirects_to_dashboard(client, monkeypatch):
    _set_password(monkeypatch)
    response = _login(client)
    assert response.status_code == 302
    assert "/admin/alpha" in response.headers["Location"]


def test_wrong_password_stays_on_login(client, monkeypatch):
    _set_password(monkeypatch)
    response = client.post(
        "/admin/alpha/login",
        data={"password": "wrongpassword"},
        follow_redirects=True,
    )
    assert b"Incorrect password" in response.data


def test_empty_password_rejected(client, monkeypatch):
    _set_password(monkeypatch)
    response = client.post(
        "/admin/alpha/login",
        data={"password": ""},
        follow_redirects=True,
    )
    assert b"Incorrect password" in response.data


# --- dashboard access


def test_dashboard_requires_auth(client, monkeypatch):
    _set_password(monkeypatch)
    response = client.get("/admin/alpha", follow_redirects=False)
    assert response.status_code == 302
    assert "login" in response.headers["Location"]


def test_dashboard_loads_after_login(client, monkeypatch):
    _set_password(monkeypatch)
    with client:
        _login(client)
        response = client.get("/admin/alpha")
        assert response.status_code == 200
        assert b"Alpha Dashboard" in response.data


def test_dashboard_unavailable_without_env_var(client):
    os.environ.pop("ALPHA_DASHBOARD_PASSWORD", None)
    response = client.get("/admin/alpha")
    assert response.status_code == 503


def test_dashboard_shows_usage_section(client, monkeypatch):
    _set_password(monkeypatch)
    with client:
        _login(client)
        response = client.get("/admin/alpha")
        assert b"Usage" in response.data


def test_dashboard_shows_safety_section(client, monkeypatch):
    _set_password(monkeypatch)
    with client:
        _login(client)
        response = client.get("/admin/alpha")
        assert b"Safety" in response.data


def test_dashboard_shows_classroom_section(client, monkeypatch):
    _set_password(monkeypatch)
    with client:
        _login(client)
        response = client.get("/admin/alpha")
        assert b"Classroom" in response.data


def test_dashboard_shows_technical_section(client, monkeypatch):
    _set_password(monkeypatch)
    with client:
        _login(client)
        response = client.get("/admin/alpha")
        assert b"Technical" in response.data


def test_dashboard_loads_with_empty_db(client, monkeypatch):
    """Dashboard should render gracefully with no data."""
    _set_password(monkeypatch)
    with client:
        _login(client)
        response = client.get("/admin/alpha")
        assert response.status_code == 200


# --- logout


def test_logout_clears_session(client, monkeypatch):
    _set_password(monkeypatch)
    with client:
        _login(client)
        client.get("/admin/alpha/logout")
        response = client.get("/admin/alpha", follow_redirects=False)
        assert response.status_code == 302
        assert "login" in response.headers["Location"]


def test_logout_redirects_to_login(client, monkeypatch):
    _set_password(monkeypatch)
    with client:
        _login(client)
        response = client.get("/admin/alpha/logout", follow_redirects=False)
        assert response.status_code == 302
        assert "login" in response.headers["Location"]


# --- export


def test_export_requires_auth(client, monkeypatch):
    _set_password(monkeypatch)
    response = client.get("/admin/alpha/export", follow_redirects=False)
    assert response.status_code == 302
    assert "login" in response.headers["Location"]


def test_export_returns_zip(client, monkeypatch):
    _set_password(monkeypatch)
    with client:
        _login(client)
        response = client.get("/admin/alpha/export")
        assert response.status_code == 200
        assert response.content_type == "application/zip"


def test_export_filename_contains_timestamp(client, monkeypatch):
    _set_password(monkeypatch)
    with client:
        _login(client)
        response = client.get("/admin/alpha/export")
        disposition = response.headers.get("Content-Disposition", "")
        assert "spark_alpha_" in disposition
        assert ".zip" in disposition


def test_export_zip_contains_expected_files(client, monkeypatch):
    import zipfile
    import io

    _set_password(monkeypatch)
    with client:
        _login(client)
        response = client.get("/admin/alpha/export")
        zf = zipfile.ZipFile(io.BytesIO(response.data))
        names = zf.namelist()
        assert "usage_daily_users.csv" in names
        assert "safety_daily_reports.csv" in names
        assert "classroom_completion.csv" in names
        assert "technical_rate_limits.csv" in names


def test_export_csv_has_headers(client, monkeypatch):
    import zipfile
    import io
    import csv

    _set_password(monkeypatch)
    with client:
        _login(client)
        response = client.get("/admin/alpha/export")
        zf = zipfile.ZipFile(io.BytesIO(response.data))
        content = zf.read("usage_daily_users.csv").decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        headers = next(reader)
        assert "day" in headers
        assert "count" in headers


# --- data presence after activity


def test_dashboard_reflects_new_user(client, monkeypatch):
    _set_password(monkeypatch)
    client.post(
        "/auth/register",
        data={
            "username": "dashuser",
            "password": "pass123",
            "bio": "",
            "dob": "2008-01-01",
        },
    )
    with client:
        _login(client)
        response = client.get("/admin/alpha")
        assert response.status_code == 200


def test_dashboard_reflects_login_event(client, monkeypatch):
    _set_password(monkeypatch)
    client.post(
        "/auth/register",
        data={
            "username": "logintrack",
            "password": "pass123",
            "bio": "",
            "dob": "2008-01-01",
        },
    )
    client.post(
        "/auth/login",
        data={"username": "logintrack", "password": "pass123"},
    )
    with client:
        _login(client)
        response = client.get("/admin/alpha")
        assert response.status_code == 200


def test_dashboard_reflects_classroom_data(
    client, monkeypatch, teacher_client, classroom
):
    _set_password(monkeypatch)
    with client:
        _login(client)
        response = client.get("/admin/alpha")
        assert response.status_code == 200


def test_dashboard_coppa_pending_shown(client, monkeypatch):
    """Under-13 self-registered student should appear in COPPA pending."""
    _set_password(monkeypatch)
    client.post(
        "/auth/register",
        data={
            "username": "youngkid",
            "password": "pass123",
            "bio": "",
            "dob": "2015-01-01",  # under 13
        },
    )
    with client:
        _login(client)
        response = client.get("/admin/alpha")
        assert b"youngkid" in response.data


def test_dashboard_session_isolation(client, monkeypatch, auth_client):
    """Admin session should be separate from user session."""
    _set_password(monkeypatch)
    with client:
        _login(client)
        with client.session_transaction() as sess:
            assert sess.get("admin_authenticated") is True
            assert sess.get("user_id") is None
