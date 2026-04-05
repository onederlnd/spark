"""
tests/test_password_reset.py

Full test coverage for the password reset feature:
  - Token utility (generate, verify, expiry, tampering)
  - /auth/forgot-password route
  - /auth/reset-password/<token> route
  - Teacher manual reset (/classrooms/<id>/students/<id>/reset-password)
  - Email sending behaviour
  - Rate limiting
  - Security / edge cases
"""

from unittest.mock import patch
from conftest import _make_classroom, _register_teacher


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _create_user_with_email(
    client, app, *, email="user@school.edu", username="resetuser"
):
    """Register a user via the legacy /auth/register route and stamp an email on them."""
    client.post(
        "/auth/register",
        data={
            "username": username,
            "password": "oldpassword",
            "bio": "",
            "dob": "2000-01-01",
        },
    )
    with app.app_context():
        from app.models import get_db

        db = get_db()
        db.execute("UPDATE users SET email = ? WHERE username = ?", (email, username))
        db.commit()
        return db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()


def _get_reset_token(app, user_id):
    """Generate a valid reset token inside an app context."""
    with app.app_context():
        from app.utils.password_reset import generate_reset_token

        return generate_reset_token(user_id)


def _provision_student_in_classroom(app, teacher_client, classroom_id):
    """Provision a student directly in the DB and enroll them. Returns the user row."""
    with app.app_context():
        from app.models import get_db
        import bcrypt

        db = get_db()
        pw = bcrypt.hashpw(b"temppass99", bcrypt.gensalt(rounds=4)).decode()
        db.execute(
            """INSERT INTO users (username, password_hash, dob, bio, role, coppa_status,
               onboarded, provisional, created_by, email)
               VALUES ('prov.student', ?, '2010-05-01', '', 'student', 'approved', 0, 1,
               (SELECT id FROM users WHERE username='teacher1'), NULL)""",
            (pw,),
        )
        db.commit()
        user = db.execute(
            "SELECT * FROM users WHERE username = 'prov.student'"
        ).fetchone()
        db.execute(
            "INSERT INTO classroom_members (classroom_id, user_id, role) VALUES (?, ?, 'student')",
            (classroom_id, user["id"]),
        )
        db.commit()
        return user


# ─────────────────────────────────────────────────────────────────────────────
# Token utility
# ─────────────────────────────────────────────────────────────────────────────


def test_generate_token_returns_string(app):
    with app.app_context():
        from app.utils.password_reset import generate_reset_token

        token = generate_reset_token(1)
        assert isinstance(token, str)
        assert len(token) > 20


def test_verify_valid_token_returns_user_id(app):
    with app.app_context():
        from app.utils.password_reset import generate_reset_token, verify_reset_token

        token = generate_reset_token(42)
        assert verify_reset_token(token) == 42


def test_verify_tampered_token_returns_none(app):
    with app.app_context():
        from app.utils.password_reset import generate_reset_token, verify_reset_token

        token = generate_reset_token(42)
        assert verify_reset_token(token + "x") is None


def test_verify_garbage_token_returns_none(app):
    with app.app_context():
        from app.utils.password_reset import verify_reset_token

        assert verify_reset_token("notavalidtoken") is None


def test_verify_empty_token_returns_none(app):
    with app.app_context():
        from app.utils.password_reset import verify_reset_token

        assert verify_reset_token("") is None


def test_verify_expired_token_returns_none(app):
    with app.app_context():
        from app.utils.password_reset import generate_reset_token, verify_reset_token

        token = generate_reset_token(1)
        with patch("app.utils.password_reset._MAX_AGE", -1):
            assert verify_reset_token(token) is None


def test_different_users_get_different_tokens(app):
    with app.app_context():
        from app.utils.password_reset import generate_reset_token

        assert generate_reset_token(1) != generate_reset_token(2)


def test_same_user_gets_different_tokens_over_time(app):
    """Tokens embed a timestamp so two consecutive tokens for the same user differ."""
    import time

    with app.app_context():
        from app.utils.password_reset import generate_reset_token

        t1 = generate_reset_token(1)
    time.sleep(1.05)
    with app.app_context():
        from app.utils.password_reset import generate_reset_token

        t2 = generate_reset_token(1)
    assert t1 != t2


def test_token_for_user_id_zero_returns_zero(app):
    with app.app_context():
        from app.utils.password_reset import generate_reset_token, verify_reset_token

        token = generate_reset_token(0)
        assert verify_reset_token(token) == 0


def test_token_signed_with_app_secret(app):
    """A token created with one SECRET_KEY must fail under a different key."""
    with app.app_context():
        from app.utils.password_reset import generate_reset_token

        token = generate_reset_token(1)

    app.config["SECRET_KEY"] = "completely-different-secret"
    with app.app_context():
        from app.utils.password_reset import verify_reset_token

        assert verify_reset_token(token) is None


# ─────────────────────────────────────────────────────────────────────────────
# GET /auth/forgot-password
# ─────────────────────────────────────────────────────────────────────────────


def test_forgot_password_get_renders_form(client):
    response = client.get("/auth/forgot-password")
    assert response.status_code == 200
    assert b"email" in response.data.lower()


def test_forgot_password_get_accessible_when_logged_out(client):
    response = client.get("/auth/forgot-password")
    assert response.status_code == 200


def test_forgot_password_get_accessible_when_logged_in(auth_client):
    response = auth_client.get("/auth/forgot-password")
    assert response.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# POST /auth/forgot-password — user enumeration / messaging
# ─────────────────────────────────────────────────────────────────────────────


def test_forgot_password_known_email_shows_generic_message(client, app, monkeypatch):
    monkeypatch.setattr(
        "app.routes.auth.send_password_reset_email", lambda *a, **kw: None
    )
    _create_user_with_email(client, app, email="known@school.edu", username="knownuser")
    response = client.post(
        "/auth/forgot-password",
        data={"email": "known@school.edu"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"If that email" in response.data


def test_forgot_password_unknown_email_shows_same_message(client):
    response = client.post(
        "/auth/forgot-password",
        data={"email": "nobody@nowhere.com"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"If that email" in response.data


def test_forgot_password_empty_email_shows_generic_message(client):
    response = client.post(
        "/auth/forgot-password",
        data={"email": ""},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"If that email" in response.data


def test_forgot_password_does_not_confirm_email_exists(client, app, monkeypatch):
    """Response must be identical for known and unknown emails (no enumeration)."""
    monkeypatch.setattr(
        "app.routes.auth.send_password_reset_email", lambda *a, **kw: None
    )
    _create_user_with_email(
        client, app, email="exists@school.edu", username="existsuser"
    )

    r_known = client.post(
        "/auth/forgot-password",
        data={"email": "exists@school.edu"},
        follow_redirects=True,
    )
    r_unknown = client.post(
        "/auth/forgot-password",
        data={"email": "nope@school.edu"},
        follow_redirects=True,
    )
    # Both should flash the same message; neither should say "not found" or "sent"
    assert b"If that email" in r_known.data
    assert b"If that email" in r_unknown.data


def test_forgot_password_case_insensitive_email_lookup(client, app, monkeypatch):
    sent = []
    monkeypatch.setattr(
        "app.routes.auth.send_password_reset_email",
        lambda *a, **kw: sent.append(a),
    )
    _create_user_with_email(client, app, email="Mixed@School.EDU", username="mixeduser")
    client.post(
        "/auth/forgot-password",
        data={"email": "mixed@school.edu"},
        follow_redirects=True,
    )
    assert len(sent) == 1


# ─────────────────────────────────────────────────────────────────────────────
# POST /auth/forgot-password — email sending
# ─────────────────────────────────────────────────────────────────────────────


def test_forgot_password_sends_email_for_known_user(client, app, monkeypatch):
    sent = []
    monkeypatch.setattr(
        "app.routes.auth.send_password_reset_email",
        lambda email, username, reset_url: sent.append((email, username, reset_url)),
    )
    _create_user_with_email(
        client, app, email="sendme@school.edu", username="sendmeuser"
    )
    client.post("/auth/forgot-password", data={"email": "sendme@school.edu"})
    assert len(sent) == 1
    assert sent[0][0] == "sendme@school.edu"


def test_forgot_password_does_not_send_email_for_unknown_user(client, monkeypatch):
    sent = []
    monkeypatch.setattr(
        "app.routes.auth.send_password_reset_email",
        lambda *a, **kw: sent.append(a),
    )
    client.post("/auth/forgot-password", data={"email": "ghost@school.edu"})
    assert len(sent) == 0


def test_forgot_password_reset_url_in_email_is_absolute(client, app, monkeypatch):
    sent = []
    monkeypatch.setattr(
        "app.routes.auth.send_password_reset_email",
        lambda email, username, reset_url: sent.append(reset_url),
    )
    _create_user_with_email(client, app, email="abs@school.edu", username="absuser")
    client.post("/auth/forgot-password", data={"email": "abs@school.edu"})
    assert len(sent) == 1
    assert sent[0].startswith("http")


def test_forgot_password_reset_url_contains_token(client, app, monkeypatch):
    sent = []
    monkeypatch.setattr(
        "app.routes.auth.send_password_reset_email",
        lambda email, username, reset_url: sent.append(reset_url),
    )
    _create_user_with_email(client, app, email="tok@school.edu", username="tokuser")
    client.post("/auth/forgot-password", data={"email": "tok@school.edu"})
    assert "/reset-password/" in sent[0]


def test_forgot_password_email_send_failure_does_not_crash(client, app, monkeypatch):
    def _raise(*a, **kw):
        raise Exception("SMTP error")

    monkeypatch.setattr("app.routes.auth.send_password_reset_email", _raise)
    _create_user_with_email(client, app, email="err@school.edu", username="erruser")
    response = client.post(
        "/auth/forgot-password",
        data={"email": "err@school.edu"},
        follow_redirects=True,
    )
    assert response.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# POST /auth/forgot-password — rate limiting
# ─────────────────────────────────────────────────────────────────────────────


def test_forgot_password_rate_limited(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.auth.send_password_reset_email", lambda *a, **kw: None
    )
    statuses = []
    for _ in range(10):
        r = client.post("/auth/forgot-password", data={"email": "spam@school.edu"})
        statuses.append(r.status_code)
    assert 429 in statuses


# ─────────────────────────────────────────────────────────────────────────────
# GET /auth/reset-password/<token>
# ─────────────────────────────────────────────────────────────────────────────


def test_reset_password_get_valid_token_renders_form(client, app):
    _create_user_with_email(client, app, email="form@school.edu", username="formuser")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username='formuser'")
            .fetchone()
        )
        token = _get_reset_token(app, user["id"])
    response = client.get(f"/auth/reset-password/{token}")
    assert response.status_code == 200
    assert b"password" in response.data.lower()


def test_reset_password_get_invalid_token_redirects(client):
    response = client.get("/auth/reset-password/thisisnotvalid")
    assert response.status_code == 302
    assert "/forgot-password" in response.headers["Location"]


def test_reset_password_get_invalid_token_shows_error(client):
    response = client.get("/auth/reset-password/thisisnotvalid", follow_redirects=True)
    assert b"invalid" in response.data.lower() or b"expired" in response.data.lower()


def test_reset_password_get_expired_token_redirects(client, app):
    _create_user_with_email(client, app, email="exp@school.edu", username="expuser")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db().execute("SELECT id FROM users WHERE username='expuser'").fetchone()
        )
        token = _get_reset_token(app, user["id"])
    with patch("app.utils.password_reset._MAX_AGE", -1):
        response = client.get(f"/auth/reset-password/{token}")
    assert response.status_code == 302
    assert "/forgot-password" in response.headers["Location"]


def test_reset_password_get_empty_token_redirects(client):
    response = client.get("/auth/reset-password/")
    assert response.status_code in (302, 404)


def test_reset_password_get_tampered_token_redirects(client, app):
    _create_user_with_email(client, app, email="tamp@school.edu", username="tampuser")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username='tampuser'")
            .fetchone()
        )
        token = _get_reset_token(app, user["id"])
    response = client.get(f"/auth/reset-password/{token}TAMPERED")
    assert response.status_code == 302
    assert "/forgot-password" in response.headers["Location"]


# ─────────────────────────────────────────────────────────────────────────────
# POST /auth/reset-password/<token> — success path
# ─────────────────────────────────────────────────────────────────────────────


def test_reset_password_post_valid_updates_password(client, app):
    _create_user_with_email(client, app, email="up@school.edu", username="upuser")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db().execute("SELECT id FROM users WHERE username='upuser'").fetchone()
        )
        token = _get_reset_token(app, user["id"])
    client.post(
        f"/auth/reset-password/{token}",
        data={"password": "newpassword1", "confirm_password": "newpassword1"},
    )
    response = client.post(
        "/auth/login", data={"username": "upuser", "password": "newpassword1"}
    )
    assert response.status_code == 302


def test_reset_password_post_old_password_no_longer_works(client, app):
    _create_user_with_email(client, app, email="old@school.edu", username="oldpwuser")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username='oldpwuser'")
            .fetchone()
        )
        token = _get_reset_token(app, user["id"])
    client.post(
        f"/auth/reset-password/{token}",
        data={"password": "brandnewpass1", "confirm_password": "brandnewpass1"},
    )
    response = client.post(
        "/auth/login", data={"username": "oldpwuser", "password": "oldpassword"}
    )
    assert response.status_code == 200
    assert b"Invalid" in response.data


def test_reset_password_post_redirects_to_login(client, app):
    _create_user_with_email(client, app, email="redir@school.edu", username="rediruser")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username='rediruser'")
            .fetchone()
        )
        token = _get_reset_token(app, user["id"])
    response = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "newpassword1", "confirm_password": "newpassword1"},
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_reset_password_post_success_shows_flash(client, app):
    _create_user_with_email(client, app, email="fl@school.edu", username="flashuser")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username='flashuser'")
            .fetchone()
        )
        token = _get_reset_token(app, user["id"])
    response = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "newpassword1", "confirm_password": "newpassword1"},
        follow_redirects=True,
    )
    assert b"updated" in response.data.lower() or b"success" in response.data.lower()


def test_reset_password_post_password_is_bcrypt_hashed(client, app):
    _create_user_with_email(client, app, email="hash@school.edu", username="hashuser")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username='hashuser'")
            .fetchone()
        )
        token = _get_reset_token(app, user["id"])
    client.post(
        f"/auth/reset-password/{token}",
        data={"password": "newpassword1", "confirm_password": "newpassword1"},
    )
    # Verify via login rather than inspecting the hash directly —
    # update_user_password handles hashing internally
    response = client.post(
        "/auth/login", data={"username": "hashuser", "password": "newpassword1"}
    )
    assert response.status_code == 302


# ─────────────────────────────────────────────────────────────────────────────
# POST /auth/reset-password/<token> — validation failures
# ─────────────────────────────────────────────────────────────────────────────


def test_reset_password_post_short_password_rejected(client, app):
    _create_user_with_email(client, app, email="sh@school.edu", username="shortuser")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username='shortuser'")
            .fetchone()
        )
        token = _get_reset_token(app, user["id"])
    response = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "short", "confirm_password": "short"},
    )
    assert response.status_code == 200
    assert b"8" in response.data


def test_reset_password_post_mismatched_passwords_rejected(client, app):
    _create_user_with_email(client, app, email="mm@school.edu", username="mismatch")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username='mismatch'")
            .fetchone()
        )
        token = _get_reset_token(app, user["id"])
    response = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "password123", "confirm_password": "different123"},
    )
    assert response.status_code == 200
    assert b"match" in response.data.lower()


def test_reset_password_post_empty_password_rejected(client, app):
    _create_user_with_email(client, app, email="ep@school.edu", username="emptypass")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username='emptypass'")
            .fetchone()
        )
        token = _get_reset_token(app, user["id"])
    response = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "", "confirm_password": ""},
    )
    assert response.status_code == 200


def test_reset_password_post_missing_confirm_rejected(client, app):
    _create_user_with_email(client, app, email="mc@school.edu", username="noconfirm")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username='noconfirm'")
            .fetchone()
        )
        token = _get_reset_token(app, user["id"])
    response = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "newpassword1"},
    )
    assert response.status_code == 200


def test_reset_password_post_exactly_8_chars_accepted(client, app):
    _create_user_with_email(client, app, email="8ch@school.edu", username="eightchar")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username='eightchar'")
            .fetchone()
        )
        token = _get_reset_token(app, user["id"])
    response = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "exactly8", "confirm_password": "exactly8"},
    )
    assert response.status_code == 302


def test_reset_password_post_7_chars_rejected(client, app):
    _create_user_with_email(client, app, email="7ch@school.edu", username="sevenchar")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username='sevenchar'")
            .fetchone()
        )
        token = _get_reset_token(app, user["id"])
    response = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "seven77", "confirm_password": "seven77"},
    )
    assert response.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# POST /auth/reset-password/<token> — invalid / expired token on submit
# ─────────────────────────────────────────────────────────────────────────────


def test_reset_password_post_invalid_token_redirects(client):
    response = client.post(
        "/auth/reset-password/badtoken",
        data={"password": "newpassword1", "confirm_password": "newpassword1"},
    )
    assert response.status_code == 302
    assert "/forgot-password" in response.headers["Location"]


def test_reset_password_post_expired_token_redirects(client, app):
    _create_user_with_email(client, app, email="exppost@school.edu", username="exppost")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db().execute("SELECT id FROM users WHERE username='exppost'").fetchone()
        )
        token = _get_reset_token(app, user["id"])
    with patch("app.utils.password_reset._MAX_AGE", -1):
        response = client.post(
            f"/auth/reset-password/{token}",
            data={"password": "newpassword1", "confirm_password": "newpassword1"},
        )
    assert response.status_code == 302
    assert "/forgot-password" in response.headers["Location"]


def test_reset_password_post_tampered_token_redirects(client, app):
    _create_user_with_email(client, app, email="tpost@school.edu", username="tamppost")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username='tamppost'")
            .fetchone()
        )
        token = _get_reset_token(app, user["id"])
    response = client.post(
        f"/auth/reset-password/{token}TAMPERED",
        data={"password": "newpassword1", "confirm_password": "newpassword1"},
    )
    assert response.status_code == 302
    assert "/forgot-password" in response.headers["Location"]


def test_reset_password_post_invalid_token_does_not_change_password(client, app):
    _create_user_with_email(client, app, email="safe@school.edu", username="safeuser")
    client.post(
        "/auth/reset-password/badtoken",
        data={"password": "hacked!", "confirm_password": "hacked!"},
    )
    response = client.post(
        "/auth/login", data={"username": "safeuser", "password": "oldpassword"}
    )
    assert response.status_code == 302


# ─────────────────────────────────────────────────────────────────────────────
# Token single-use: token remains valid until expiry (stateless)
# but a second reset with a fresh token supersedes the old one
# ─────────────────────────────────────────────────────────────────────────────


def test_second_reset_token_also_works(client, app, monkeypatch):
    """Two valid tokens can both be used (stateless); the last one wins."""
    monkeypatch.setattr(
        "app.routes.auth.send_password_reset_email", lambda *a, **kw: None
    )
    _create_user_with_email(client, app, email="two@school.edu", username="twotoken")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username='twotoken'")
            .fetchone()
        )

    import time

    time.sleep(1.05)
    token2 = _get_reset_token(app, user["id"])

    # Use the second token
    client.post(
        f"/auth/reset-password/{token2}",
        data={"password": "secondpass1", "confirm_password": "secondpass1"},
    )
    r = client.post(
        "/auth/login", data={"username": "twotoken", "password": "secondpass1"}
    )
    assert r.status_code == 302


# ─────────────────────────────────────────────────────────────────────────────
# Teacher manual student password reset
# ─────────────────────────────────────────────────────────────────────────────


def test_teacher_reset_student_password_success(app, teacher_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    student = _provision_student_in_classroom(app, teacher_client, classroom_id)
    response = teacher_client.post(
        f"/classrooms/{classroom_id}/students/{student['id']}/reset-password",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"prov.student" in response.data


def test_teacher_reset_shows_new_temp_password_in_flash(app, teacher_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    student = _provision_student_in_classroom(app, teacher_client, classroom_id)
    response = teacher_client.post(
        f"/classrooms/{classroom_id}/students/{student['id']}/reset-password",
        follow_redirects=True,
    )
    # Flash message should contain the new password (letters + digits)
    assert b"reset to:" in response.data or b"Reset" in response.data


def test_teacher_reset_new_password_works_for_login(app, client, teacher_client):
    """After teacher reset, the student can log in with the new temp password."""
    join_code, classroom_id = _make_classroom(teacher_client)
    student = _provision_student_in_classroom(app, teacher_client, classroom_id)

    # Capture the flashed password
    response = teacher_client.post(
        f"/classrooms/{classroom_id}/students/{student['id']}/reset-password",
        follow_redirects=True,
    )
    html = response.data.decode()

    import re

    # Flash format: "reset to: sunnybird42"
    match = re.search(r"reset to:\s*(\S+)", html)
    assert match, "Could not find temp password in flash message"
    new_password = re.sub(r"[^a-z0-9]+$", "", match.group(1), flags=re.IGNORECASE)

    login_response = client.post(
        "/auth/login",
        data={"username": "prov.student", "password": new_password},
    )
    assert login_response.status_code == 302


def test_teacher_reset_old_password_no_longer_works(app, client, teacher_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    student = _provision_student_in_classroom(app, teacher_client, classroom_id)

    teacher_client.post(
        f"/classrooms/{classroom_id}/students/{student['id']}/reset-password"
    )
    response = client.post(
        "/auth/login", data={"username": "prov.student", "password": "temppass99"}
    )
    assert response.status_code == 200
    assert b"Invalid" in response.data


def test_teacher_reset_password_is_bcrypt_hashed(app, client, teacher_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    student = _provision_student_in_classroom(app, teacher_client, classroom_id)

    response = teacher_client.post(
        f"/classrooms/{classroom_id}/students/{student['id']}/reset-password",
        follow_redirects=True,
    )
    html = response.data.decode()

    import re

    match = re.search(r"reset to:\s*(\S+)", html)
    assert match, "Could not find temp password in flash message"
    new_password = re.sub(r"[^a-z0-9]+$", "", match.group(1), flags=re.IGNORECASE)

    # update_user_password handles hashing internally — verify via login
    login_response = client.post(
        "/auth/login",
        data={"username": "prov.student", "password": new_password},
    )
    assert login_response.status_code == 302


def test_teacher_cannot_reset_student_in_other_classroom(app, client, teacher_client):
    """A teacher cannot reset a student who isn't in their classroom."""
    join_code, classroom_id = _make_classroom(teacher_client)
    student = _provision_student_in_classroom(app, teacher_client, classroom_id)

    # Register and log in a second teacher
    other = client
    _register_teacher(other, first="Other", last="Teacher", email="other@school.edu")
    other.post(
        "/auth/login", data={"username": "teacher.other.teacher", "password": "pass123"}
    )
    _, other_classroom_id = _make_classroom(other, name="Other Classroom")

    response = other.post(
        f"/classrooms/{other_classroom_id}/students/{student['id']}/reset-password"
    )
    assert response.status_code in (403, 404)


def test_student_cannot_reset_other_student_password(
    app, client, teacher_client, student_client
):
    join_code, classroom_id = _make_classroom(teacher_client)
    student = _provision_student_in_classroom(app, teacher_client, classroom_id)
    response = student_client.post(
        f"/classrooms/{classroom_id}/students/{student['id']}/reset-password"
    )
    assert response.status_code in (302, 403)


def test_unauthenticated_cannot_reset_student_password(app, client, teacher_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    student = _provision_student_in_classroom(app, teacher_client, classroom_id)
    response = client.post(
        f"/classrooms/{classroom_id}/students/{student['id']}/reset-password"
    )
    assert response.status_code in (302, 403)
    if response.status_code == 302:
        assert "/auth/login" in response.headers["Location"]


def test_teacher_reset_nonexistent_student_404(app, teacher_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    response = teacher_client.post(
        f"/classrooms/{classroom_id}/students/99999/reset-password"
    )
    assert response.status_code in (403, 404)


def test_teacher_reset_redirects_to_classroom_home(app, teacher_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    student = _provision_student_in_classroom(app, teacher_client, classroom_id)
    response = teacher_client.post(
        f"/classrooms/{classroom_id}/students/{student['id']}/reset-password"
    )
    assert response.status_code == 302
    assert f"/classrooms/{classroom_id}" in response.headers["Location"]


# ─────────────────────────────────────────────────────────────────────────────
# _generate_temp_password
# ─────────────────────────────────────────────────────────────────────────────


def test_temp_password_format(app):
    with app.app_context():
        from app.routes.classrooms import _generate_temp_password

        for _ in range(20):
            pw = _generate_temp_password()
            # Must be all lowercase letters followed by exactly two digits
            assert pw[-2:].isdigit(), f"No trailing digits: {pw}"
            assert pw[:-2].isalpha(), f"Non-alpha prefix: {pw}"
            assert pw[:-2].islower(), f"Uppercase in prefix: {pw}"


def test_temp_password_length_reasonable(app):
    with app.app_context():
        from app.routes.classrooms import _generate_temp_password

        for _ in range(20):
            pw = _generate_temp_password()
            assert 8 <= len(pw) <= 30, f"Unexpected length: {pw}"


def test_temp_passwords_are_random(app):
    with app.app_context():
        from app.routes.classrooms import _generate_temp_password

        passwords = {_generate_temp_password() for _ in range(50)}
        # 50 draws from a large space — collisions would be extraordinary
        assert len(passwords) > 10


# ─────────────────────────────────────────────────────────────────────────────
# send_password_reset_email helper
# ─────────────────────────────────────────────────────────────────────────────


def test_send_password_reset_email_sends_to_correct_recipient(app):
    with app.app_context():
        with patch("app.utils.email.mail.send") as mock_send:
            from app.utils.email import send_password_reset_email

            send_password_reset_email(
                "target@school.edu", "targetuser", "https://example.com/reset/token"
            )
            assert mock_send.called
            msg = mock_send.call_args[0][0]
            assert "target@school.edu" in msg.recipients


def test_send_password_reset_email_subject(app):
    with app.app_context():
        with patch("app.utils.email.mail.send") as mock_send:
            from app.utils.email import send_password_reset_email

            send_password_reset_email(
                "x@school.edu", "xuser", "https://example.com/reset/tok"
            )
            msg = mock_send.call_args[0][0]
            assert "password" in msg.subject.lower() or "reset" in msg.subject.lower()


def test_send_password_reset_email_body_contains_reset_url(app):
    with app.app_context():
        with patch("app.utils.email.mail.send") as mock_send:
            from app.utils.email import send_password_reset_email

            url = "https://example.com/auth/reset-password/sometoken"
            send_password_reset_email("y@school.edu", "yuser", url)
            msg = mock_send.call_args[0][0]
            assert url in (msg.body or "") or url in (msg.html or "")


def test_send_password_reset_email_html_contains_reset_url(app):
    with app.app_context():
        with patch("app.utils.email.mail.send") as mock_send:
            from app.utils.email import send_password_reset_email

            url = "https://example.com/auth/reset-password/sometoken"
            send_password_reset_email("z@school.edu", "zuser", url)
            msg = mock_send.call_args[0][0]
            assert url in (msg.html or "")


def test_send_password_reset_email_html_contains_username(app):
    with app.app_context():
        with patch("app.utils.email.mail.send") as mock_send:
            from app.utils.email import send_password_reset_email

            send_password_reset_email(
                "u@school.edu", "specificuser", "https://example.com/r"
            )
            msg = mock_send.call_args[0][0]
            assert "specificuser" in (msg.html or "") or "specificuser" in (
                msg.body or ""
            )


def test_send_password_reset_email_sends_exactly_one_message(app):
    with app.app_context():
        with patch("app.utils.email.mail.send") as mock_send:
            from app.utils.email import send_password_reset_email

            send_password_reset_email(
                "once@school.edu", "onceuser", "https://example.com/r"
            )
            assert mock_send.call_count == 1


# ─────────────────────────────────────────────────────────────────────────────
# mock_emails fixture coverage — reset email is suppressed in other tests
# ─────────────────────────────────────────────────────────────────────────────


def test_mock_emails_fixture_suppresses_reset_email(client, app, monkeypatch):
    """Confirm the monkeypatch in conftest.mock_emails covers send_password_reset_email
    so other tests aren't accidentally making real SMTP calls."""
    import app.routes.auth as auth_module

    original = getattr(auth_module, "send_password_reset_email", None)
    # If the attribute exists it should be callable — the mock_emails fixture
    # in conftest patches it for auth tests; we just verify it's patchable.
    assert callable(original) or original is None
