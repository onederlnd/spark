def test_view_own_profile(auth_client):
    response = auth_client.get("/profile/testuser")
    assert response.status_code == 200
    assert b"testuser" in response.data


def test_profile_shows_posts(auth_client):
    auth_client.post(
        "/posts/new",
        data={
            "title": "My Profile Post",
            "body": "This should appear on my profile.",
            "topic_id": "",
        },
    )
    response = auth_client.get("/profile/testuser")
    assert response.status_code == 200
    assert b"My Profile Post" in response.data


def test_profile_not_found(auth_client):
    response = auth_client.get("/profile/nonexistentuser")
    assert response.status_code == 404


def test_other_profile_no_bookmarks(auth_client):
    # create another user
    auth_client.post(
        "/auth/register",
        data={"username": "otheruser", "password": "pass123", "bio": ""},
    )
    # viewing profile shouldn't show bookmarks
    response = auth_client.get("/profile/otheruser")
    assert response.status_code == 200
    # bookmarks show on owner
    assert b"bookmarks" not in response.data
