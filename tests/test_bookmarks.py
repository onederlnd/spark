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
