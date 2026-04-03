# tests/test_blocking.py

from app.models.user import create_user, get_user_by_username
from app.models.block import block_user, unblock_user, is_blocked, get_blocked_ids
from app.models.post import create_post


def test_block_user(client):
    create_user("blocker", "pass123", dob="2000-01-01")
    create_user("target", "pass123", dob="2000-01-01")
    blocker = get_user_by_username("blocker")
    target = get_user_by_username("target")

    result = block_user(blocker["id"], target["id"])
    assert result is True
    assert is_blocked(blocker["id"], target["id"])


def test_cannot_block_twice(client):
    """Blocking the same user twice returns False"""
    create_user("blocker", "pass123", dob="2000-01-01")
    create_user("target", "pass123", dob="2000-01-01")

    blocker = get_user_by_username("blocker")
    target = get_user_by_username("target")

    block_user(blocker["id"], target["id"])
    result = block_user(blocker["id"], target["id"])

    assert result is False


def test_unblock_user(client):
    """A user can unblock a previously blocked user"""
    create_user("blocker", "pass123", dob="2000-01-01")
    create_user("target", "pass123", dob="2000-01-01")
    blocker = get_user_by_username("blocker")
    target = get_user_by_username("target")

    block_user(blocker["id"], target["id"])
    unblock_user(blocker["id"], target["id"])

    assert not is_blocked(blocker["id"], target["id"])


def test_get_blocked_ids(client):
    """get_blocked_ids returns correct list"""
    create_user("blocker", "pass123", dob="2000-01-01")
    create_user("target1", "pass123", dob="2000-01-01")
    create_user("target2", "pass123", dob="2000-01-01")

    blocker = get_user_by_username("blocker")
    t1 = get_user_by_username("target1")
    t2 = get_user_by_username("target2")

    block_user(blocker["id"], t1["id"])
    block_user(blocker["id"], t2["id"])

    blocked = get_blocked_ids(blocker["id"])
    assert t1["id"] in blocked
    assert t2["id"] in blocked


def test_block_is_one_directional(client):
    """Blocking A->B does not block B->A"""
    create_user("user_a", "pass123", dob="2000-01-01")
    create_user("user_b", "pass123", dob="2000-01-01")

    a = get_user_by_username("user_a")
    b = get_user_by_username("user_b")

    block_user(a["id"], b["id"])

    assert is_blocked(a["id"], b["id"])
    assert not is_blocked(b["id"], a["id"])


def test_block_route(client):
    """POST /<username>/block blocks the user"""
    create_user("blocker", "pass123", dob="2000-01-01")
    create_user("target", "pass123", dob="2000-01-01")

    blocker = get_user_by_username("blocker")

    with client.session_transaction() as sess:
        sess["user_id"] = blocker["id"]
        sess["coppa_status"] = "approved"

    response = client.post("/target/block", follow_redirects=True)
    assert response.status_code == 200
    assert b"blocked" in response.data

    target = get_user_by_username("target")
    assert is_blocked(blocker["id"], target["id"])


def test_cannot_block_yourself(client):
    """Blocking yoursel returns 400"""
    create_user("user", "pass123", dob="2000-01-01")
    user = get_user_by_username("user")

    with client.session_transaction() as sess:
        sess["user_id"] = user["id"]
        sess["coppa_status"] = "approved"

    response = client.post("/user/block")
    assert response.status_code == 400


def test_block_nonexistent_user(client):
    """Blocking a nonexistent user returns 404"""
    create_user("user", "pass123", dob="2000-01-01")
    user = get_user_by_username("user")

    with client.session_transaction() as sess:
        sess["user_id"] = user["id"]
        sess["coppa_status"] = "approved"

    response = client.post("/nobody/block")
    assert response.status_code == 404


def test_unblock_route(client):
    """POST /<username>/unblock unblocks the user"""
    create_user("blocker", "pass123", dob="2000-01-01")
    create_user("target", "pass123", dob="2000-01-01")
    blocker = get_user_by_username("blocker")
    target = get_user_by_username("target")

    block_user(blocker["id"], target["id"])

    with client.session_transaction() as sess:
        sess["user_id"] = blocker["id"]
        sess["coppa_status"] = "approved"

    response = client.post("/target/unblock", follow_redirects=True)
    assert response.status_code == 200
    assert not is_blocked(blocker["id"], target["id"])


def test_block_requires_login(client):
    """BLock route requires login"""
    create_user("target", "pass123", dob="2000-01-01")
    response = client.post("/target/block")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_blocked_user_hidden_from_feed(auth_client, app):
    """Posts from blocked users do not appear in the all feed."""
    other = app.test_client(use_cookies=True)
    other.post(
        "/auth/register",
        data={
            "username": "blockeduser",
            "password": "pass123",
            "bio": "",
            "dob": "2000-01-01",
        },
    )
    other.post("/auth/login", data={"username": "blockeduser", "password": "pass123"})
    other.post(
        "/posts/new",
        data={"title": "Blocked Post", "body": "Should be hidden", "topic_id": ""},
    )

    auth_client.post("/blockeduser/block")

    response = auth_client.get("/feed/")
    assert b"Blocked Post" not in response.data


def test_unblocked_user_appears_in_feed(app, client):
    """Post from unblcoked users reappear in the feed"""
    create_user("viewer", "pass123", dob="2000-01-01")
    create_user("author", "pass123", dob="2000-01-01")
    viewer = get_user_by_username("viewer")
    author = get_user_by_username("author")

    create_post(author["id"], "Visible Post", "You should see this", classroom_id=None)
    block_user(viewer["id"], author["id"])
    unblock_user(viewer["id"], author["id"])

    with client.session_transaction() as sess:
        sess["user_id"] = viewer["id"]
        sess["coppa_status"] = "approved"
        sess["role"] = "student"

    response = client.get("/", follow_redirects=True)
    assert b"Visible Post" in response.data


def test_non_blocked_posts_still_visible(auth_client, app):
    """Non-blocked users' posts still appear after blocking someone else."""
    # block someone
    blocked = app.test_client(use_cookies=True)
    blocked.post(
        "/auth/register",
        data={
            "username": "blocked2",
            "password": "pass123",
            "bio": "",
            "dob": "2000-01-01",
        },
    )
    auth_client.post("/blocked2/block")

    # a different user posts
    other = app.test_client(use_cookies=True)
    other.post(
        "/auth/register",
        data={
            "username": "visible",
            "password": "pass123",
            "bio": "",
            "dob": "2000-01-01",
        },
    )
    other.post("/auth/login", data={"username": "visible", "password": "pass123"})
    other.post(
        "/posts/new",
        data={"title": "Visible Post", "body": "Should appear", "topic_id": ""},
    )

    response = auth_client.get("/feed/")
    assert b"Visible Post" in response.data


def test_blocked_user_hidden_from_following_feed(auth_client, app):
    """Posts from blocked users do not appear in the following feed even if followed."""
    other = app.test_client(use_cookies=True)
    other.post(
        "/auth/register",
        data={
            "username": "blockedfollowed",
            "password": "pass123",
            "bio": "",
            "dob": "2000-01-01",
        },
    )
    other.post(
        "/auth/login", data={"username": "blockedfollowed", "password": "pass123"}
    )
    other.post(
        "/posts/new",
        data={"title": "Followed But Blocked", "body": "Hidden post", "topic_id": ""},
    )

    auth_client.post("/profile/blockedfollowed/follow")
    auth_client.post("/blockedfollowed/block")

    response = auth_client.get("/feed/following")
    assert b"Followed But Blocked" not in response.data
