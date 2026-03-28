# tests/test_rate_limit.py

from app.utils import rate_limit


def test_post_rate_limit(auth_client):
    """Exceeding posting limit returns 429 Too Many Requests"""
    rate_limit._request_counts.clear()

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


def test_react_rate_limit(auth_client, teacher_client, app):
    """Exceeding reaction limit returns 429 Too Many Requests"""
    from app.utils.rate_limit import _request_counts

    response = teacher_client.post(
        "/posts/new",
        data={
            "title": "Rate Limit Post",
            "body": "Testing reaction limits",
            "topic_id": "",
        },
    )

    post_id = response.headers["Location"].split("/")[-1]

    for _ in range(30):
        auth_client.post(f"/posts/{post_id}/react", data={"reaction": "lit"})

    response = auth_client.post(f"/posts/{post_id}/react", data={"reaction": "lit"})

    assert response.status_code == 429


def test_follow_rate_limit(auth_client, app):
    """Exceeding follow/unfollow limit returns 429 Too Many Requests"""
    rate_limit._request_counts.clear()

    for i in range(20):
        app.test_client().post(
            "/auth/register",
            data={
                "username": f"user{i}",
                "password": "pass123",
                "bio": "",
                "dob": "2010-05-21",
            },
        )
        auth_client.post(f"/profile/user{i}/follow")
        response = auth_client.post(f"/profile/user{i}/follow")

    assert response.status_code == 429


# --- test register rate limit
def test_register_rate_limit(client):
    rate_limit._request_counts.clear()

    for i in range(36):
        response = client.post(
            "/auth/register",
            data={
                "username": f"ratelimituser{i}",
                "password": "pass123",
                "bio": "",
                "dob": "2010-05-21",
            },
        )

    assert response.status_code == 429


def test_register_rate_limit_allows_multiple_users_same_ip(client):
    rate_limit._request_counts.clear()

    for i in range(36):
        response = client.post(
            "/auth/register",
            data={
                "username": f"sharedipuser{i}",
                "password": "pass123",
                "bio": "",
                "dob": "2010-05-21",
            },
            environ_base={"REMOTE_ADDR": "192.168.1.100"},
        )

    assert response.status_code == 429


def test_register_rate_limit_blocks_excessive_refresh_attempts(client):
    rate_limit._request_counts.clear()

    with client.session_transaction() as sess:
        sess["user_id"] = "refresh_user"

    for i in range(36):
        response = client.post(
            "auth/register",
            data={"username": f"refreshuser{i}", "password": "pass123", "bio": ""},
        )

    assert response.status_code == 429


def test_register_rate_limit_counts_failed_submissions(client):
    rate_limit._request_counts.clear()

    for _ in range(35):
        response = client.post(
            "/auth/register",
            data={
                "username": "",
                "password": "pass123",
                "bio": "",
                "dob": "2010-05-21",
            },
            environ_base={"REMOTE_ADDR": "192.168.1.200"},
        )

    assert response.status_code == 200

    response = client.post(
        "/auth/register",
        data={
            "username": "",
            "password": "pass123",
            "bio": "",
            "dob": "2010-05-21",
        },
        environ_base={"REMOTE_ADDR": "192.168.1.200"},
    )

    assert response.status_code == 429


def test_register_rate_limit_ip_rotation_bypass_attempts(client):
    rate_limit._request_counts.clear()

    for i in range(35):
        ip_addr = f"192.168.1.{i}"
        response = client.post(
            "auth/register",
            data={
                "username": f"user{i}",
                "password": "pass123",
                "bio": "",
                "dob": "2010-05-21",
            },
            environ_base={"REMOTE_ADDR": ip_addr},
        )

        assert response.status_code == 302

    response = client.post(
        "/auth/register",
        data={
            "username": "user36",
            "password": "pass123",
            "bio": "",
            "dob": "2010-05-21",
        },
        environ_base={"REMOTE_ADDR": "192.168.1.100"},
    )

    assert response.status_code == 302


def test_register_rate_limit_invalid_forms_still_count(client):
    rate_limit._request_counts.clear()

    for _ in range(2):
        client.post(
            "/auth/register",
            data={
                "username": "",
                "password": "pass123",
                "bio": "",
                "dob": "2010-05-21",
            },
        )

    for _ in range(34):
        response = client.post(
            "/auth/register",
            data={
                "username": "",
                "password": "pass123",
                "bio": "",
                "dob": "2010-05-21",
            },
        )

    assert response.status_code == 429
