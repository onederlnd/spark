# tests/test_posts.py


def test_create_post(auth_client):
    response = auth_client.post(
        "/posts/new",
        data={
            "title": "Test Post Title",
            "body": "This is the body of the test post.",
            "topic_id": "",
        },
    )
    # should redirect to the new post page
    assert response.status_code == 302
    assert "/posts/" in response.headers["Location"]


def test_view_post(auth_client):
    # create a post first
    response = auth_client.post(
        "/posts/new",
        data={"title": "Viewable Post", "body": "Body content here", "topic_id": ""},
    )
    # post id will be 1 in a fresh test DB
    post_url = response.headers["Location"]
    response = auth_client.get(post_url)
    assert response.status_code == 200
    assert b"Viewable Post" in response.data


def test_create_post_missing_fields(auth_client):
    response = auth_client.post(
        "/posts/new", data={"title": "", "body": "", "topic_id": ""}
    )
    assert response.status_code == 200
    assert b"required" in response.data


def test_upvote_post(auth_client):
    auth_client.post(
        "/posts/new",
        data={"title": "Vote Test", "body": "Voting on this post", "topic_id": ""},
    )
    response = auth_client.post("/posts/1/vote", data={"value": "1"})
    assert response.status_code == 302


def test_reply_to_post(auth_client):
    response = auth_client.post(
        "/posts/new",
        data={"title": "Reply Test", "body": "Post to reply to.", "topic_id": ""},
    )
    post_url = response.headers["Location"]
    auth_client.post(f"{post_url}/reply", data={"body": "This is my reply."})
    response = auth_client.get("/posts/1")
    assert response.status_code == 200
    # check reply appears on post page
    assert b"This is my reply" in response.data


def test_post_not_found(auth_client):
    response = auth_client.get("/posts/99999")
    assert response.status_code == 404


def test_edit_post(auth_client):
    response = auth_client.post(
        "posts/new",
        data={"title": "Original Title", "body": "Original body", "topic_id": ""},
    )
    post_url = response.headers["Location"]
    post_id = post_url.split("/")[-1]

    response = auth_client.post(
        f"/posts/{post_id}/edit",
        data={"title": "Updated Title", "body": "Updated body"},
    )

    assert response.status_code == 302

    response = auth_client.get(post_url)
    assert b"Updated Title" in response.data
    assert b"Updated body" in response.data


def test_delete_post(auth_client):
    response = auth_client.post(
        "/posts/new",
        data={
            "title": "To Be Deleted",
            "body": "This post will be deleted",
            "topic_id": "",
        },
    )
    post_url = response.headers["Location"]
    post_id = post_url.split("/")[-1]

    response = auth_client.post(f"/posts/{post_id}/delete")
    assert response.status_code == 302

    response = auth_client.get(post_url)
    assert response.status_code == 404


def test_edit_post_forbidden(auth_client, app):
    response = auth_client.post(
        "/posts/new",
        data={
            "title": "Testuser Post",
            "body": "Only Testuser can edit this",
            "topic_id": "",
        },
    )
    post_id = response.headers["Location"].split("/")[-1]

    other = app.test_client(use_cookies=True)

    reg_response = other.post(
        "/auth/register",
        data={
            "username": "otheruser",
            "password": "pass123",
            "bio": "",
            "dob": "2010-05-21",
        },
    )
    print(f"DEBUG register status: {reg_response.status_code}")
    print(f"DEBUG register location: {reg_response.headers.get('Location')}")

    login_response = other.post(
        "/auth/login", data={"username": "otheruser", "password": "pass123"}
    )
    print(f"DEBUG login status: {login_response.status_code}")
    print(f"DEBUG login location: {login_response.headers.get('Location')}")

    response = other.post(
        f"/posts/{post_id}/edit", data={"title": "Hacked!", "body": "Hacked!"}
    )
    print(f"DEBUG edit status: {response.status_code}")
    assert response.status_code == 403


def test_feed_pagination(auth_client):
    response = auth_client.get("/feed/?page=1", follow_redirects=True)
    assert response.status_code == 200

    response = auth_client.get("/feed/?page=99", follow_redirects=True)
    assert response.status_code == 200


# --- authentication required ---


def test_unauthenticated_cannot_create_post(client):
    response = client.post(
        "/posts/new",
        data={"title": "Sneaky Post", "body": "Should not work", "topic_id": ""},
    )
    assert response.status_code in (302, 403)
    if response.status_code == 302:
        assert "/auth/login" in response.headers["Location"]


def test_unauthenticated_cannot_reply(client):
    response = client.post("/posts/1/reply", data={"body": "Sneaky reply"})
    assert response.status_code in (302, 403)
    if response.status_code == 302:
        assert "/auth/login" in response.headers["Location"]


def test_unauthenticated_cannot_vote(client):
    response = client.post("/posts/1/vote", data={"value": "1"})
    assert response.status_code in (302, 403)
    if response.status_code == 302:
        assert "/auth/login" in response.headers["Location"]


def test_unauthenticated_cannot_edit_post(client):
    response = client.post("/posts/1/edit", data={"title": "Hacked", "body": "Hacked"})
    assert response.status_code in (302, 403)
    if response.status_code == 302:
        assert "/auth/login" in response.headers["Location"]


def test_unauthenticated_cannot_delete_post(client):
    response = client.post("/posts/1/delete")
    assert response.status_code in (302, 403)
    if response.status_code == 302:
        assert "/auth/login" in response.headers["Location"]


# --- content filtering ---


def test_post_with_blocked_word_rejected(auth_client, app):
    from app.utils.content_filter import add_word

    with app.app_context():
        add_word("badword", user_id=1)

    response = auth_client.post(
        "/posts/new",
        data={
            "title": "Clean Title",
            "body": "This contains badword here",
            "topic_id": "",
        },
    )
    assert response.status_code == 200
    assert b"not allowed" in response.data


def test_post_title_with_blocked_word_rejected(auth_client, app):
    from app.utils.content_filter import add_word

    with app.app_context():
        add_word("badword", user_id=1)

    response = auth_client.post(
        "/posts/new",
        data={"title": "This has badword", "body": "Clean body", "topic_id": ""},
    )
    assert response.status_code == 200
    assert b"not allowed" in response.data


def test_reply_with_blocked_word_rejected(auth_client, app):
    from app.utils.content_filter import add_word

    with app.app_context():
        add_word("badword", user_id=1)

    auth_client.post(
        "/posts/new",
        data={"title": "Clean Post", "body": "Clean body", "topic_id": ""},
    )
    response = auth_client.post(
        "/posts/1/reply",
        data={"body": "badword in reply"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"not allowed" in response.data


# --- XSS / injection ---


def test_xss_in_post_title_escaped(auth_client):
    response = auth_client.post(
        "/posts/new",
        data={
            "title": "<script>alert('xss')</script>",
            "body": "Clean body",
            "topic_id": "",
        },
    )
    post_url = response.headers.get("Location")
    if post_url:
        response = auth_client.get(post_url)
        assert b"<script>alert" not in response.data


def test_xss_in_post_body_escaped(auth_client):
    response = auth_client.post(
        "/posts/new",
        data={
            "title": "XSS Body Test",
            "body": "<script>alert('xss')</script>",
            "topic_id": "",
        },
    )
    post_url = response.headers.get("Location")
    if post_url:
        response = auth_client.get(post_url)
        assert b"<script>alert" not in response.data


def test_xss_in_reply_escaped(auth_client):
    auth_client.post(
        "/posts/new",
        data={"title": "XSS Reply Test", "body": "Clean body", "topic_id": ""},
    )
    auth_client.post(
        "/posts/1/reply",
        data={"body": "<script>alert('xss')</script>"},
    )
    response = auth_client.get("/posts/1")
    assert b"<script>alert" not in response.data


def test_sql_injection_in_post_title(auth_client):
    response = auth_client.post(
        "/posts/new",
        data={
            "title": "'; DROP TABLE posts; --",
            "body": "Clean body",
            "topic_id": "",
        },
    )
    # should either sanitize and create, or reject — but never crash
    assert response.status_code in (200, 302)


# --- rate limiting ---


def test_rate_limit_on_post_creation(auth_client):
    """Rapid post creation should eventually be rate limited."""
    responses = []
    for i in range(40):
        r = auth_client.post(
            "/posts/new",
            data={"title": f"Spam Post {i}", "body": "Spam body", "topic_id": ""},
        )
        responses.append(r.status_code)

    assert 429 in responses, "Rate limiting should have triggered before 40 requests"
