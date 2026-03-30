# tests/test_follows.py


def test_follow_user(auth_client, app):
    """Follow another user, expect redirect."""
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
    response = auth_client.post("/profile/otheruser/follow")
    assert response.status_code == 302


def test_unfollow_user(auth_client, app):
    """Follow then unfollow, expect redirect both times."""
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
    auth_client.post("/profile/otheruser/follow")
    response = auth_client.post("/profile/otheruser/follow")
    assert response.status_code == 302


def test_cannot_follow_self(auth_client):
    """Following yourself returns 400."""
    response = auth_client.post("/profile/testuser/follow")
    assert response.status_code == 400


def test_follow_nonexistent_user(auth_client):
    """Following a nonexistent user returns 404."""
    response = auth_client.post("/profile/nonexistentuser/follow")
    assert response.status_code == 404


def test_following_feed(auth_client):
    response = auth_client.get("/feed/following")
    assert response.status_code == 200


def test_following_feed_empty_state(auth_client):
    response = auth_client.get("/feed/following")
    assert b"Your following feed is empty" in response.data


def test_following_feed_new_url(auth_client):
    """Following feed loads at canonical /feed/following URL."""
    response = auth_client.get("/feed/following")
    assert response.status_code == 200


def test_following_feed_shows_posts_from_followed_users(auth_client, app):
    """Posts from followed users appear in the following feed."""
    # register a second user and have auth_client follow them
    other = app.test_client(use_cookies=True)
    other.post(
        "/auth/register",
        data={
            "username": "otheruser",
            "password": "pass123",
            "bio": "",
            "dob": "2000-01-01",
        },
    )
    other.post("/auth/login", data={"username": "otheruser", "password": "pass123"})
    other.post(
        "/posts/new",
        data={"title": "Other User Post", "body": "Post body", "topic_id": ""},
    )

    auth_client.post("/profile/otheruser/follow")

    response = auth_client.get("/feed/following")
    assert response.status_code == 200
    assert b"Other User Post" in response.data


def test_following_feed_excludes_unfollowed_users(auth_client, app):
    """Posts from users not followed do not appear in the following feed."""
    other = app.test_client(use_cookies=True)
    other.post(
        "/auth/register",
        data={
            "username": "stranger",
            "password": "pass123",
            "bio": "",
            "dob": "2000-01-01",
        },
    )
    other.post("/auth/login", data={"username": "stranger", "password": "pass123"})
    other.post(
        "/posts/new",
        data={
            "title": "Stranger Post",
            "body": "You should not see this",
            "topic_id": "",
        },
    )

    response = auth_client.get("/feed/following")
    assert b"Stranger Post" not in response.data


def test_following_feed_requires_login(client):
    response = client.get("/feed/following", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]
