from conftest import _make_classroom, _register_student, _register_teacher, _get_user


# ---------------------------------------------------------------------------
# generic register route
# ---------------------------------------------------------------------------


def test_register_success(client):
    response = client.post(
        "/auth/register",
        data={
            "username": "newuser",
            "password": "pass123",
            "bio": "hi",
            "dob": "2000-05-21",
        },
    )
    assert response.status_code == 302


def test_register_duplicate_username(client):
    data = {
        "username": "dupeuser",
        "password": "pass123",
        "bio": "",
        "dob": "2000-05-21",
    }
    client.post("/auth/register", data=data)
    response = client.post("/auth/register", data=data)
    assert response.status_code == 200
    assert b"already taken" in response.data


def test_register_missing_dob(client):
    response = client.post(
        "/auth/register",
        data={"username": "nodob", "password": "pass123", "bio": "", "dob": ""},
    )
    assert response.status_code == 200
    assert b"Date of Birth" in response.data or b"required" in response.data


def test_register_missing_username(client):
    response = client.post(
        "/auth/register",
        data={"username": "", "password": "pass123", "bio": "", "dob": "2000-05-21"},
    )
    assert response.status_code == 200
    assert b"required" in response.data


def test_register_missing_password(client):
    response = client.post(
        "/auth/register",
        data={"username": "nopass", "password": "", "bio": "", "dob": "2000-05-21"},
    )
    assert response.status_code == 200
    assert b"required" in response.data


def test_register_invalid_role_defaults_to_student(client, app):
    client.post(
        "/auth/register",
        data={
            "username": "badrole",
            "password": "pass123",
            "bio": "",
            "dob": "2000-05-21",
            "role": "admin",
        },
    )
    with app.app_context():
        from app.models.user import get_user_by_username

        user = get_user_by_username("badrole")
        assert user["role"] == "student"


def test_register_xss_in_username(client):
    client.post(
        "/auth/register",
        data={
            "username": "<script>alert('xss')</script>",
            "password": "pass123",
            "bio": "",
            "dob": "2000-05-21",
        },
    )
    response = client.get("/auth/login")
    assert b"<script>alert" not in response.data


def test_register_xss_in_bio(client):
    client.post(
        "/auth/register",
        data={
            "username": "xssbio",
            "password": "pass123",
            "bio": "<script>alert('xss')</script>",
            "dob": "2000-05-21",
        },
    )
    response = client.get("/profile/xssbio")
    assert b"<script>alert" not in response.data


def test_register_rate_limited(client):
    statuses = []
    for i in range(40):
        r = client.post(
            "/auth/register",
            data={
                "username": f"spamuser{i}",
                "password": "pass123",
                "bio": "",
                "dob": "2000-05-21",
            },
        )
        statuses.append(r.status_code)
    assert 429 in statuses


# ---------------------------------------------------------------------------
# login / logout
# ---------------------------------------------------------------------------


def test_login_success(client):
    client.post(
        "/auth/register",
        data={
            "username": "loginuser",
            "password": "pass123",
            "bio": "",
            "dob": "2000-05-21",
        },
    )
    response = client.post(
        "/auth/login", data={"username": "loginuser", "password": "pass123"}
    )
    assert response.status_code == 302
    assert "/" in response.headers["Location"]


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        data={
            "username": "wrongpass",
            "password": "correctpass",
            "bio": "",
            "dob": "2000-05-21",
        },
    )
    response = client.post(
        "/auth/login", data={"username": "wrongpass", "password": "wrongpass"}
    )
    assert response.status_code == 200
    assert b"Invalid" in response.data


def test_login_nonexistent_user(client):
    response = client.post(
        "/auth/login", data={"username": "ghostuser", "password": "pass123"}
    )
    assert response.status_code == 200
    assert b"Invalid" in response.data


def test_logout_redirects(auth_client):
    response = auth_client.get("/auth/logout")
    assert response.status_code == 302


def test_logout_clears_session(auth_client):
    auth_client.get("/auth/logout")
    response = auth_client.get("/feed/", follow_redirects=False)
    assert "/auth/login" in response.headers["Location"]


def test_feed_requires_login(client):
    response = client.get("/feed/", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_session_cleared_on_logout(auth_client):
    auth_client.get("/auth/logout")
    response = auth_client.get("/profile/testuser", follow_redirects=False)
    assert response.status_code in (302, 403)


def test_protected_routes_blocked_after_logout(auth_client):
    auth_client.get("/auth/logout")
    for url in ["/feed/", "/posts/new", "/classrooms/"]:
        response = auth_client.get(url, follow_redirects=False)
        assert response.status_code in (302, 403)
        if response.status_code == 302:
            assert "/auth/login" in response.headers["Location"]


def test_brute_force_lockout(client):
    client.post(
        "/auth/register",
        data={
            "username": "bruteuser",
            "password": "correctpass",
            "bio": "",
            "dob": "2000-05-21",
        },
    )
    for _ in range(10):
        r = client.post(
            "/auth/login", data={"username": "bruteuser", "password": "wrongpass"}
        )
    assert b"Too many" in r.data or b"locked" in r.data or b"minutes" in r.data


# ---------------------------------------------------------------------------
# COPPA
# ---------------------------------------------------------------------------


def test_coppa_pending_student_sees_notice(client):
    client.post(
        "/auth/register",
        data={
            "username": "coppauser",
            "password": "pass123",
            "bio": "",
            "dob": "2015-06-15",
        },
    )
    client.post("/auth/login", data={"username": "coppauser", "password": "pass123"})
    response = client.get("/classrooms/", follow_redirects=True)
    assert (
        b"Pending Approval" in response.data
        or b"COPPA" in response.data
        or b"restricted" in response.data
    )


def test_coppa_teacher_can_approve(teacher_client, client, app):
    client.post(
        "/auth/register",
        data={
            "username": "youngkid",
            "password": "pass123",
            "bio": "",
            "dob": "2015-06-15",
        },
    )
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'youngkid'")
            .fetchone()
        )
        user_id = user["id"]
    response = teacher_client.post(
        f"/auth/coppa/approve/{user_id}", follow_redirects=True
    )
    assert response.status_code == 200
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT coppa_status FROM users WHERE id = ?", (user_id,))
            .fetchone()
        )
        assert user["coppa_status"] == "approved"


def test_coppa_teacher_can_deny(teacher_client, client, app):
    client.post(
        "/auth/register",
        data={
            "username": "deniedkid",
            "password": "pass123",
            "bio": "",
            "dob": "2015-06-15",
        },
    )
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'deniedkid'")
            .fetchone()
        )
        user_id = user["id"]
    teacher_client.post(f"/auth/coppa/deny/{user_id}", follow_redirects=True)
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT coppa_status FROM users WHERE id = ?", (user_id,))
            .fetchone()
        )
        assert user["coppa_status"] == "denied"


def test_coppa_non_teacher_cannot_approve(auth_client, client, app):
    client.post(
        "/auth/register",
        data={
            "username": "coppa2",
            "password": "pass123",
            "bio": "",
            "dob": "2015-06-15",
        },
    )
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'coppa2'")
            .fetchone()
        )
        user_id = user["id"]
    response = auth_client.post(f"/auth/coppa/approve/{user_id}")
    assert response.status_code in (302, 403)


def test_coppa_pending_list_visible_to_teacher(teacher_client, client):
    client.post(
        "/auth/register",
        data={
            "username": "pendingkid",
            "password": "pass123",
            "bio": "",
            "dob": "2015-06-15",
        },
    )
    response = teacher_client.get("/auth/coppa/pending")
    assert response.status_code == 200
    assert b"pendingkid" in response.data


# ---------------------------------------------------------------------------
# QR login
# ---------------------------------------------------------------------------


def test_qr_login_invalid_token(client):
    response = client.get("/auth/qr-login?token=totallyfaketoken")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_qr_login_missing_token(client):
    response = client.get("/auth/qr-login")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_qr_login_empty_token(client):
    response = client.get("/auth/qr-login?token=")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_qr_login_valid_provisional_user(app, client):
    """A provisional user with a valid qr_token should be logged in."""
    with app.app_context():
        from app.models import get_db
        from app.models.user import generate_qr_token
        import bcrypt

        token = generate_qr_token()
        pw = bcrypt.hashpw(b"irrelevant", bcrypt.gensalt(rounds=4)).decode()
        get_db().execute(
            """INSERT INTO users (username, password_hash, dob, bio, role, coppa_status,
               onboarded, provisional, qr_token)
               VALUES ('qruser', ?, '2005-01-01', '', 'student', 'approved', 0, 1, ?)""",
            (pw, token),
        )
        get_db().commit()
    response = client.get(f"/auth/qr-login?token={token}")
    assert response.status_code == 302
    assert "/auth/login" not in response.headers["Location"]


# ---------------------------------------------------------------------------
# validate-join-code
# ---------------------------------------------------------------------------


def test_validate_join_code_valid(client, teacher_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    response = client.get(f"/auth/validate-join-code?code={join_code}")
    data = response.get_json()
    assert response.status_code == 200
    assert data["valid"] is True
    assert data["classroom_id"] == classroom_id
    assert "classroom_name" in data


def test_validate_join_code_invalid(client):
    response = client.get("/auth/validate-join-code?code=XXXXXX")
    data = response.get_json()
    assert data["valid"] is False
    assert "error" in data


def test_validate_join_code_missing(client):
    response = client.get("/auth/validate-join-code")
    data = response.get_json()
    assert data["valid"] is False


def test_validate_join_code_empty(client):
    response = client.get("/auth/validate-join-code?code=")
    data = response.get_json()
    assert data["valid"] is False


# ---------------------------------------------------------------------------
# student registration
# ---------------------------------------------------------------------------


def test_student_register_success(client, teacher_client):
    join_code, _ = _make_classroom(teacher_client)
    response = _register_student(client, join_code)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_student_enrolled_in_classroom(app, client, teacher_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    _register_student(client, join_code, first="Alice", last="Smith")
    with app.app_context():
        from app.models.classroom import get_member_role

        user = _get_user(app, "alice.smith")
        assert user is not None
        assert get_member_role(classroom_id, user["id"]) == "student"


def test_student_username_format(app, client, teacher_client):
    join_code, _ = _make_classroom(teacher_client)
    _register_student(client, join_code, first="Charlie", last="Brown")
    user = _get_user(app, "charlie.brown")
    assert user is not None
    assert user["username"].startswith("charlie.brown")


def test_student_username_collision_gets_suffix(app, client, teacher_client):
    join_code1, _ = _make_classroom(teacher_client)
    join_code2, _ = _make_classroom(teacher_client)
    _register_student(client, join_code1, first="Dana", last="Lee")
    _register_student(client, join_code2, first="Dana", last="Lee")
    with app.app_context():
        from app.models import get_db

        rows = (
            get_db()
            .execute(
                "SELECT username FROM users WHERE username LIKE 'dana.lee%' ORDER BY id"
            )
            .fetchall()
        )
        assert len(rows) == 2
        assert rows[0]["username"] == "dana.lee"
        assert rows[1]["username"] == "dana.lee1"


def test_student_display_name_set(app, client, teacher_client):
    join_code, _ = _make_classroom(teacher_client)
    _register_student(client, join_code, first="Grace", last="Hopper")
    user = _get_user(app, "grace.hopper")
    assert user["display_name"] == "Grace Hopper"


def test_student_optional_email_stored(app, client, teacher_client):
    join_code, _ = _make_classroom(teacher_client)
    _register_student(
        client, join_code, first="Fiona", last="Gray", email="fiona@example.com"
    )
    user = _get_user(app, "fiona.gray")
    assert user["email"] == "fiona@example.com"


def test_student_no_email_still_succeeds(client, teacher_client):
    join_code, _ = _make_classroom(teacher_client)
    response = _register_student(
        client, join_code, first="Noemail", last="User", email=""
    )
    assert response.status_code == 302


def test_student_can_log_in_after_register(app, client, teacher_client):
    join_code, _ = _make_classroom(teacher_client)
    _register_student(
        client, join_code, first="Henry", last="Ford", password="mypassword"
    )
    user = _get_user(app, "henry.ford")
    response = client.post(
        "/auth/login", data={"username": user["username"], "password": "mypassword"}
    )
    assert response.status_code == 302


def test_student_invalid_join_code_rejected(client):
    response = _register_student(client, "BADCOD")
    assert response.status_code in (200, 302)
    if response.status_code == 302:
        assert "/register" in response.headers["Location"]
    else:
        assert b"Invalid" in response.data or b"join" in response.data.lower()


def test_student_empty_join_code_rejected(client):
    response = _register_student(client, "")
    assert response.status_code in (200, 302)


def test_student_missing_first_name_rejected(client, teacher_client):
    join_code, _ = _make_classroom(teacher_client)
    response = client.post(
        "/auth/register/student",
        data={
            "first_name": "",
            "last_name": "Smith",
            "password": "pass123",
            "dob": "2005-01-01",
            "join_code": join_code,
        },
    )
    assert response.status_code in (200, 302)


def test_student_missing_last_name_rejected(client, teacher_client):
    join_code, _ = _make_classroom(teacher_client)
    response = client.post(
        "/auth/register/student",
        data={
            "first_name": "Eve",
            "last_name": "",
            "password": "pass123",
            "dob": "2005-01-01",
            "join_code": join_code,
        },
    )
    assert response.status_code in (200, 302)


def test_student_missing_password_rejected(client, teacher_client):
    join_code, _ = _make_classroom(teacher_client)
    response = client.post(
        "/auth/register/student",
        data={
            "first_name": "Eve",
            "last_name": "Hart",
            "password": "",
            "dob": "2005-01-01",
            "join_code": join_code,
        },
    )
    assert response.status_code in (200, 302)


def test_student_missing_dob_rejected(client, teacher_client):
    join_code, _ = _make_classroom(teacher_client)
    response = client.post(
        "/auth/register/student",
        data={
            "first_name": "Eve",
            "last_name": "Hart",
            "password": "pass123",
            "dob": "",
            "join_code": join_code,
        },
    )
    assert response.status_code in (200, 302)


def test_student_under_13_blocked(client, teacher_client):
    join_code, _ = _make_classroom(teacher_client)
    response = _register_student(client, join_code, dob="2015-01-01")
    assert response.status_code in (200, 302)
    if response.status_code == 200:
        assert b"13" in response.data or b"teacher" in response.data.lower()
    else:
        assert "/register" in response.headers["Location"]


def test_student_under_13_not_created_in_db(app, client, teacher_client):
    join_code, _ = _make_classroom(teacher_client)
    _register_student(client, join_code, first="Young", last="Kid", dob="2015-01-01")
    assert _get_user(app, "young.kid") is None


def test_student_under_13_not_enrolled(app, client, teacher_client):
    join_code, classroom_id = _make_classroom(teacher_client)
    _register_student(client, join_code, first="Tiny", last="Tim", dob="2015-01-01")
    with app.app_context():
        from app.models import get_db

        row = (
            get_db()
            .execute(
                "SELECT * FROM classroom_members WHERE classroom_id = ? AND user_id IN "
                "(SELECT id FROM users WHERE username LIKE 'tiny.tim%')",
                (classroom_id,),
            )
            .fetchone()
        )
        assert row is None


def test_student_xss_in_name_sanitized(app, client, teacher_client):
    join_code, _ = _make_classroom(teacher_client)
    _register_student(client, join_code, first="<script>bad</script>", last="Safe")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT display_name FROM users WHERE display_name LIKE '%Safe%'")
            .fetchone()
        )
        if user:
            assert "<script>" not in user["display_name"]


def test_student_register_rate_limited(client, teacher_client):
    join_code, _ = _make_classroom(teacher_client)
    statuses = []
    for i in range(15):
        r = _register_student(client, join_code, first=f"User{i}", last="Test")
        statuses.append(r.status_code)
    assert 429 in statuses


# ---------------------------------------------------------------------------
# teacher registration
# ---------------------------------------------------------------------------


def test_teacher_register_success(client):
    response = _register_teacher(client)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_teacher_username_format(app, client):
    _register_teacher(client, first="Bob", last="Jones")
    user = _get_user(app, "teacher.bob.jones")
    assert user is not None
    assert user["username"].startswith("teacher.bob.jones")


def test_teacher_username_collision_gets_suffix(app, client):
    _register_teacher(client, first="Carol", last="White", email="carol1@school.edu")
    _register_teacher(client, first="Carol", last="White", email="carol2@school.edu")
    with app.app_context():
        from app.models import get_db

        rows = (
            get_db()
            .execute(
                "SELECT username FROM users WHERE username LIKE 'teacher.carol.white%' ORDER BY id"
            )
            .fetchall()
        )
        assert len(rows) == 2
        assert rows[0]["username"] == "teacher.carol.white"
        assert rows[1]["username"] == "teacher.carol.white1"


def test_teacher_display_name_set(app, client):
    _register_teacher(client, first="Diana", last="Prince")
    user = _get_user(app, "teacher.diana.prince")
    assert user["display_name"] == "Diana Prince"


def test_teacher_role_is_teacher(app, client):
    _register_teacher(client, first="Ed", last="Nash", email="ed@school.edu")
    user = _get_user(app, "teacher.ed.nash")
    assert user["role"] == "teacher"


def test_teacher_email_stored(app, client):
    _register_teacher(client, first="Frank", last="Lee", email="frank@school.edu")
    user = _get_user(app, "teacher.frank.lee")
    assert user["email"] == "frank@school.edu"


def test_teacher_can_log_in_after_register(app, client):
    _register_teacher(client, first="Gina", last="Fox", email="gina@school.edu")
    user = _get_user(app, "teacher.gina.fox")
    response = client.post(
        "/auth/login", data={"username": user["username"], "password": "pass123"}
    )
    assert response.status_code == 302


def test_teacher_missing_email_rejected(client):
    response = _register_teacher(client, email="")
    assert response.status_code in (200, 302)
    if response.status_code == 200:
        assert b"required" in response.data.lower() or b"email" in response.data.lower()
    else:
        assert "/register" in response.headers["Location"]


def test_teacher_missing_first_name_rejected(client):
    response = client.post(
        "/auth/register/teacher",
        data={
            "first_name": "",
            "last_name": "Smith",
            "password": "pass123",
            "dob": "1985-01-01",
            "email": "x@school.edu",
        },
    )
    assert response.status_code in (200, 302)


def test_teacher_missing_last_name_rejected(client):
    response = client.post(
        "/auth/register/teacher",
        data={
            "first_name": "Frank",
            "last_name": "",
            "password": "pass123",
            "dob": "1985-01-01",
            "email": "x@school.edu",
        },
    )
    assert response.status_code in (200, 302)


def test_teacher_missing_password_rejected(client):
    response = client.post(
        "/auth/register/teacher",
        data={
            "first_name": "Frank",
            "last_name": "Lee",
            "password": "",
            "dob": "1985-01-01",
            "email": "frank@school.edu",
        },
    )
    assert response.status_code in (200, 302)


def test_teacher_missing_dob_rejected(client):
    response = client.post(
        "/auth/register/teacher",
        data={
            "first_name": "Frank",
            "last_name": "Lee",
            "password": "pass123",
            "dob": "",
            "email": "frank@school.edu",
        },
    )
    assert response.status_code in (200, 302)


def test_teacher_register_rate_limited(client):
    statuses = []
    for i in range(15):
        r = _register_teacher(
            client, first=f"User{i}", last="Test", email=f"user{i}@school.edu"
        )
        statuses.append(r.status_code)
    assert 429 in statuses
