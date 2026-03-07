# tests/test_follows.py


def test_follow_user(auth_client, app):
    """Follow another user, expect redirect."""
    other = app.test_client(use_cookies=True)
    other.post(
        "/auth/register",
        data={"username": "otheruser", "password": "pass123", "bio": ""},
    )
    response = auth_client.post("/profile/otheruser/follow")
    assert response.status_code == 302


def test_unfollow_user(auth_client, app):
    """Follow then unfollow, expect redirect both times."""
    other = app.test_client(use_cookies=True)
    other.post(
        "/auth/register",
        data={"username": "otheruser", "password": "pass123", "bio": ""},
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
    """Following feed loads successfully."""
    response = auth_client.get("/?feed=following")
    assert response.status_code == 200


def test_following_feed_empty_state(auth_client):
    """Following feed shows empty state when not following anyone."""
    response = auth_client.get("/?feed=following")
    assert b"no posts from followed users yet" in response.data
