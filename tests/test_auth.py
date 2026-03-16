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
    response = auth_client.get("/")
    assert "/auth/login" in response.headers["Location"]


def test_feed_requires_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]
