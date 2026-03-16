# mark as read
def test_mark_as_read(auth_client):
    """
    Test that notifications can be marked as read
    """
    response = auth_client.post("/notifications/read")
    assert response.status_code == 302


# notification created on reply
def test_notification_on_follow(auth_client, app):
    """
    Test that a notification is created when a user is followed
    """
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

    other.post(
        "/auth/login",
        data={"username": "otheruser", "password": "pass123"},
    )
    response = other.get("/notifications/")
    assert b"followed you" in response.data


# notification created on follow
def test_notification_on_reply(auth_client, app):
    """
    Test that a notification is created when a user receives a reply to their post
    """
    response = auth_client.post(
        "/posts/new",
        data={
            "title": "Original Post",
            "body": "This post will receive a reply",
            "topic_id": "",
        },
    )
    post_id = response.headers["Location"].split("/")[-1]
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
    other.post(
        "/auth/login",
        data={"username": "otheruser", "password": "pass123"},
    )
    other.post(
        f"/posts/{post_id}/reply",
        data={"body": "This is a reply to the original post", "topic_id": ""},
    )
    response = auth_client.get("/notifications/")
    assert b"replied to your post" in response.data
