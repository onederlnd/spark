# tests/test_feed.py

# --- feed routes ---


def test_feed_requires_login(client):
    response = client.get("/feed/", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_feed_loads(auth_client):
    response = auth_client.get("/feed/")
    assert response.status_code == 200


def test_feed_default_shows_all(auth_client):
    response = auth_client.get("/feed/")
    assert response.status_code == 200
    assert b"For You" in response.data
