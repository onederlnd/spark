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
        data={"title": "Vote Test", "body": "VOting on this post", "topic_id": ""},
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
