# tests/test_auth.py


def test_register_success(client):
    response = client.post(
        "/auth/register",
        data={
            "username": "newuser",
            "password": "pass123",
            "bio": "This is a newuser test bio",
            "dob": "2010-05-21",
        },
    )

    # successful register redirects to login
    print(response.data.decode())
    assert response.status_code == 302


def test_register_duplicate_username(client):
    data = {
        "username": "dupeuser",
        "password": "pass123",
        "bio": "",
        "dob": "2010-05-21",
    }
    client.post("/auth/register", data=data)
    response = client.post("/auth/register", data=data)
    # should stay on register page with error
    assert response.status_code == 200
    assert b"already taken" in response.data


def test_login_success(client):
    client.post(
        "/auth/register",
        data={
            "username": "loginuser",
            "password": "pass123",
            "bio": "",
            "dob": "2010-05-21",
        },
    )
    response = client.post(
        "/auth/login",
        data={
            "username": "loginuser",
            "password": "pass123",
        },
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
            "dob": "2010-05-21",
        },
    )
    response = client.post(
        "/auth/login", data={"username": "wrongpass", "password": "wrongpass"}
    )
    assert response.status_code == 200
    assert b"Invalid" in response.data


def test_logout(auth_client):
    response = auth_client.get("/auth/logout")
    assert response.status_code == 302
    # after logout, feed should redirect to login
    response = auth_client.get("/feed/", follow_redirects=False)
    assert "/auth/login" in response.headers["Location"]


def test_feed_requires_login(client):
    response = client.get("/feed/", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


# --- registration edge cases ---


def test_register_missing_dob(client):
    """DOB is required — especially important for COPPA compliance."""
    response = client.post(
        "/auth/register",
        data={"username": "nodob", "password": "pass123", "bio": "", "dob": ""},
    )
    assert response.status_code == 200
    assert b"Date of Birth" in response.data or b"required" in response.data


def test_register_missing_username(client):
    response = client.post(
        "/auth/register",
        data={"username": "", "password": "pass123", "bio": "", "dob": "2010-05-21"},
    )
    assert response.status_code == 200
    assert b"required" in response.data


def test_register_missing_password(client):
    response = client.post(
        "/auth/register",
        data={"username": "nopass", "password": "", "bio": "", "dob": "2010-05-21"},
    )
    assert response.status_code == 200
    assert b"required" in response.data


def test_register_invalid_role_defaults_to_student(client):
    """Supplying an arbitrary role should silently fall back to student."""
    response = client.post(
        "/auth/register",
        data={
            "username": "badrole",
            "password": "pass123",
            "bio": "",
            "dob": "2010-05-21",
            "role": "admin",
        },
    )
    assert response.status_code == 302
    # confirm they were not granted an elevated role
    from app.models.user import get_user_by_username

    # adjust to match your actual lookup function
    with client.application.app_context():
        user = get_user_by_username("badrole")
        assert user["role"] == "student"


def test_register_xss_in_username(client):
    client.post(
        "/auth/register",
        data={
            "username": "<script>alert('xss')</script>",
            "password": "pass123",
            "bio": "",
            "dob": "2010-05-21",
        },
    )
    # sanitize_username strips non-word chars, leaving "scriptalertxssscript"
    response = client.get("/auth/login")
    assert b"<script>alert" not in response.data


def test_register_xss_in_bio(client):
    client.post(
        "/auth/register",
        data={
            "username": "xssbio",
            "password": "pass123",
            "bio": "<script>alert('xss')</script>",
            "dob": "2010-05-21",
        },
    )
    response = client.get("/profile/xssbio")
    assert b"<script>alert" not in response.data


# --- brute force / rate limiting ---


def test_brute_force_lockout(client):
    """Repeated failed logins should trigger a lockout."""
    client.post(
        "/auth/register",
        data={
            "username": "bruteuser",
            "password": "correctpass",
            "bio": "",
            "dob": "2010-05-21",
        },
    )
    responses = []
    for _ in range(10):
        r = client.post(
            "/auth/login",
            data={"username": "bruteuser", "password": "wrongpass"},
        )
        responses.append(r)

    # at some point the response should mention lockout
    last = responses[-1]
    assert b"Too many" in last.data or b"locked" in last.data or b"minutes" in last.data


def test_rate_limit_on_registration(client):
    """Rapid registrations should eventually be rate limited."""
    responses = []
    for i in range(40):
        r = client.post(
            "/auth/register",
            data={
                "username": f"spamuser{i}",
                "password": "pass123",
                "bio": "",
                "dob": "2010-05-21",
            },
        )
        responses.append(r.status_code)
    assert 429 in responses, "Rate limiting should have triggered before 40 requests"


# --- session / login state ---


def test_login_nonexistent_user(client):
    response = client.post(
        "/auth/login",
        data={"username": "ghostuser", "password": "pass123"},
    )
    assert response.status_code == 200
    assert b"Invalid" in response.data


def test_session_cleared_on_logout(auth_client):
    """Session data should not persist after logout."""
    auth_client.get("/auth/logout")
    response = auth_client.get("/profile/testuser", follow_redirects=False)
    assert response.status_code in (302, 403)


def test_cannot_access_protected_routes_after_logout(auth_client):
    auth_client.get("/auth/logout")
    protected = ["/feed/", "/posts/new", "/classrooms/"]
    for url in protected:
        response = auth_client.get(url, follow_redirects=False)
        assert response.status_code in (302, 403), (
            f"{url} should be protected after logout"
        )
        if response.status_code == 302:
            assert "/auth/login" in response.headers["Location"]


# --- COPPA ---


def test_coppa_notice_shown_to_pending_student(client):
    """Students under 13 should be blocked until COPPA approved."""
    client.post(
        "/auth/register",
        data={
            "username": "coppauser",
            "password": "pass123",
            "bio": "",
            "dob": "2015-06-15",  # unambiguously under 13
        },
    )
    client.post("/auth/login", data={"username": "coppauser", "password": "pass123"})
    response = client.get("/classrooms/", follow_redirects=True)
    assert (
        b"Pending Approval" in response.data
        or b"COPPA" in response.data
        or b"restricted" in response.data
    )


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
