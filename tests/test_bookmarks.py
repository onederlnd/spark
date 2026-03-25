def test_bookmark_post(auth_client):
    response = auth_client.post(
        "/posts/new",
        data={"title": "Bookmark Test", "body": "Post to bookmark", "topic_id": ""},
    )
    post_url = response.headers["Location"]
    post_id = post_url.split("/")[-1]

    response = auth_client.post(f"/posts/{post_id}/bookmark")
    assert response.status_code == 302

    response = auth_client.get(post_url)
    assert response.status_code == 200
    assert b"bookmarked" in response.data


def test_unbookmark_post(auth_client):
    # create and bookmark
    response = auth_client.post(
        "/posts/new",
        data={"title": "Unbookmark Test", "body": "Post to unbookmark", "topic_id": ""},
    )
    post_url = response.headers["Location"]
    post_id = post_url.split("/")[-1]

    auth_client.post(f"/posts/{post_id}/bookmark")  # add
    auth_client.post(f"/posts/{post_id}/bookmark")  # remove

    # shoudl no longer show bookmarked
    response = auth_client.get(post_url)
    assert b"bookmarked" not in response.data or b"\u2295 bookmark" in response.data


def test_bookmarks_appear_on_profile(auth_client):
    response = auth_client.post(
        "/posts/new",
        data={
            "title": "Profile Bookmark Test",
            "body": "Should appear in bookmarks",
            "topic_id": "",
        },
    )
    post_url = response.headers["Location"]
    post_id = post_url.split("/")[-1]
    auth_client.post(f"/posts/{post_id}/bookmark")

    # check profile shows it
    response = auth_client.get("/profile/testuser")
    assert response.status_code == 200
    assert b"Profile Bookmark Test" in response.data


# --- bookmarks ---


def test_unauthenticated_cannot_bookmark(client):
    response = client.post("/posts/1/bookmark")
    assert response.status_code in (302, 403)
    if response.status_code == 302:
        assert "/auth/login" in response.headers["Location"]


def test_bookmark_nonexistent_post(auth_client):
    response = auth_client.post("/posts/99999/bookmark")
    assert response.status_code == 404


def test_bookmark_persists_after_reload(auth_client):
    response = auth_client.post(
        "/posts/new",
        data={
            "title": "Persist Bookmark",
            "body": "Should stay bookmarked",
            "topic_id": "",
        },
    )
    post_url = response.headers["Location"]
    post_id = post_url.split("/")[-1]

    auth_client.post(f"/posts/{post_id}/bookmark")

    # reload the page twice to confirm persistence
    response = auth_client.get(post_url)
    assert b"bookmarked" in response.data
    response = auth_client.get(post_url)
    assert b"bookmarked" in response.data


def test_bookmark_another_users_post(auth_client, app):
    """Students should be able to bookmark posts made by other users."""
    other = app.test_client(use_cookies=True)
    other.post(
        "/auth/register",
        data={
            "username": "otheruser2",
            "password": "pass123",
            "bio": "",
            "dob": "2008-04-10",
        },
    )
    other.post("/auth/login", data={"username": "otheruser2", "password": "pass123"})
    response = other.post(
        "/posts/new",
        data={
            "title": "Other User Post",
            "body": "Written by someone else",
            "topic_id": "",
        },
    )
    post_url = response.headers["Location"]
    post_id = post_url.split("/")[-1]

    # auth_client (testuser) bookmarks it
    response = auth_client.post(f"/posts/{post_id}/bookmark")
    assert response.status_code == 302

    response = auth_client.get(post_url)
    assert b"bookmarked" in response.data


def test_bookmark_toggle_is_idempotent(auth_client):
    """Toggling bookmark twice should return to unbookmarked state cleanly."""
    response = auth_client.post(
        "/posts/new",
        data={"title": "Toggle Test", "body": "Toggle me", "topic_id": ""},
    )
    post_id = response.headers["Location"].split("/")[-1]

    auth_client.post(f"/posts/{post_id}/bookmark")  # bookmark
    auth_client.post(f"/posts/{post_id}/bookmark")  # unbookmark
    auth_client.post(f"/posts/{post_id}/bookmark")  # bookmark again

    response = auth_client.get(f"/posts/{post_id}")
    assert b"bookmarked" in response.data


def test_bookmarks_not_visible_to_other_users(auth_client, app):
    """One user's bookmarks should not appear on another user's profile."""
    response = auth_client.post(
        "/posts/new",
        data={
            "title": "Private Bookmark",
            "body": "Only testuser bookmarks this",
            "topic_id": "",
        },
    )
    post_id = response.headers["Location"].split("/")[-1]
    auth_client.post(f"/posts/{post_id}/bookmark")

    other = app.test_client(use_cookies=True)
    other.post(
        "/auth/register",
        data={
            "username": "otheruser3",
            "password": "pass123",
            "bio": "",
            "dob": "2009-01-15",
        },
    )
    other.post("/auth/login", data={"username": "otheruser3", "password": "pass123"})

    response = other.get("/profile/otheruser3")
    assert b"Private Bookmark" not in response.data


def test_deleted_post_removed_from_bookmarks(auth_client):
    """Bookmarked posts that are deleted should not appear in bookmarks."""
    response = auth_client.post(
        "/posts/new",
        data={"title": "Soon Deleted", "body": "Will be deleted", "topic_id": ""},
    )
    post_url = response.headers["Location"]
    post_id = post_url.split("/")[-1]

    auth_client.post(f"/posts/{post_id}/bookmark")
    auth_client.post(f"/posts/{post_id}/delete")

    response = auth_client.get("/profile/testuser")
    assert b"Soon Deleted" not in response.data
