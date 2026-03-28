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


def test_blocked_user_hidden_from_feed(app, client):
    """Posts from blocked users do not appear in the feed"""
    create_user("viewer", "pass123", dob="2000-01-01")
    create_user("blocked_author", "pass123", dob="2000-01-01")

    viewer = get_user_by_username("viewer")
    blocked_author = get_user_by_username("blocked_author")

    create_post(blocked_author["id"], "Hidden Post", "You should not see this", None)
    block_user(viewer["id"], blocked_author["id"])

    with client.session_transaction() as sess:
        sess["user_id"] = viewer["id"]
        sess["coppa_status"] = "approved"
        sess["role"] = "student"

    response = client.get("/", follow_redirects=True)
    assert b"Hidden Post" not in response.data


def test_unblocked_user_appears_in_feed(app, client):
    """Post from unblcoked users reappear in the feed"""
    create_user("viewer", "pass123", dob="2000-01-01")
    create_user("author", "pass123", dob="2000-01-01")
    viewer = get_user_by_username("viewer")
    author = get_user_by_username("author")

    create_post(author["id"], "Visible Post", "You should see this", None)
    block_user(viewer["id"], author["id"])
    unblock_user(viewer["id"], author["id"])

    with client.session_transaction() as sess:
        sess["user_id"] = viewer["id"]
        sess["coppa_status"] = "approved"
        sess["role"] = "student"

    response = client.get("/", follow_redirects=True)
    assert b"Visible Post" in response.data


def test_non_blocked_posts_still_visible(app, client):
    """Posts from non-blocked users are unaffected by blocking someone else"""
    create_user("viewer", "pass123", dob="2000-01-01")
    create_user("blocked_author", "pass123", dob="2000-01-01")
    create_user("normal_author", "pass123", dob="2000-01-01")

    viewer = get_user_by_username("viewer")
    blocked_author = get_user_by_username("blocked_author")
    normal_author = get_user_by_username("normal_author")

    create_post(blocked_author["id"], "Hidden Post", "Should not appear", None)
    create_post(normal_author["id"], "Normal Post", "Should appear", None)
    block_user(viewer["id"], blocked_author["id"])

    with client.session_transaction() as sess:
        sess["user_id"] = viewer["id"]
        sess["coppa_status"] = "approved"
        sess["role"] = "student"

    response = client.get("/", follow_redirects=True)
    assert b"Hidden Post" not in response.data
    assert b"Normal Post" in response.data
