# tests/test_rate_limit.py


def test_post_rate_limit(auth_client):
    """Exceeding posting limit returns 429 Too Many Requests"""
    for _ in range(10):
        response = auth_client.post(
            "/posts/new",
            data={"title": "Test Post", "body": "This is a test body.", "topic_id": ""},
        )
    response = auth_client.post(
        "/posts/new",
        data={"title": "One too many", "body": "Should be blocked", "topic_id": ""},
    )
    assert response.status_code == 429


def test_vote_rate_limit(auth_client):
    """Exceeding voting limit returns 429 Too Many Requests"""
    # create a post to vote on
    response = auth_client.post(
        "/posts/new",
        data={
            "title": "Vote Limit Test",
            "body": "Testing vote limits",
            "topic_id": "",
        },
    )
    post_id = response.headers["Location"].split("/")[-1]
    for _ in range(30):
        auth_client.post(f"/posts/{post_id}/vote", data={"value": "1"})
    response = auth_client.post(f"/posts/{post_id}/vote", data={"value": "1"})
    assert response.status_code == 429


def test_follow_rate_limit(auth_client, app):
    """Exceeding follow/unfollow limit returns 429 Too Many Requests"""
    for i in range(20):
        app.test_client().post(
            "/auth/register",
            data={"username": f"user{i}", "password": "pass123", "bio": ""},
        )
        auth_client.post(f"/profile/user{i}/follow")
        response = auth_client.post(f"/profile/user{i}/follow")
    assert response.status_code == 429
