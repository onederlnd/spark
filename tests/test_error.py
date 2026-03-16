# tests/test_error.py


def test_403_page(auth_client, app):
    other = app.test_client(use_cookies=True)
    other.post(
        "/auth/register",
        data={
            "username": "otheruser",
            "password": "pass123",
            "bio": "",
            "dob": "2010-05-21",
        },
    )
    other.post("/auth/login", data={"username": "otheruser", "password": "pass123"})
    response = other.post(
        "/posts/new", data={"title": "Test Post", "body": "Test Body", "topic_id": ""}
    )
    post_id = response.headers["Location"].split("/")[-1]

    response = auth_client.post(
        f"/posts/{post_id}/edit", data={"title": "Hacked!", "body": "Hacked!"}
    )
    assert response.status_code == 403
    assert b"Forbidden" in response.data


def test_404_page(auth_client):
    response = auth_client.get("/nonexistent")
    assert response.status_code == 404
    assert b"Not Found" in response.data


def test_405_page(auth_client):
    response = auth_client.post("/auth/logout")
    assert response.status_code == 405
    assert b"Method Not Allowed" in response.data


def test_429_page(auth_client):
    for _ in range(10):
        auth_client.post(
            "/posts/new",
            data={"title": "Test Post", "body": "Test Body", "topic_id": ""},
        )
    response = auth_client.post(
        "/posts/new", data={"title": "Blocked", "body": "Blocked body", "topic_id": ""}
    )
    assert response.status_code == 429


def test_500_page(app):
    app.config["TESTING"] = False  # Disable testing mode to trigger error handlers

    @app.route("/trigger500")
    def cause_error():
        raise Exception("Test exception for 500 error")

    client = app.test_client()
    response = client.get("/trigger500")
    assert response.status_code == 500
    assert b"Internal Server Error" in response.data
