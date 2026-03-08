# tests/test_api.py


def test_get_single_post(auth_client):
    """GET /api/posts/<id> should return post details."""
    response = auth_client.post(
        "/posts/new",
        data={"title": "API Test Post", "body": "Testing API endpoint", "topic_id": ""},
    )
    assert response.status_code == 302
    post_url = response.headers["Location"]
    post_id = post_url.split("/")[-1]
    response = auth_client.get(f"/api/posts/{post_id}")
    assert response.status_code == 200
    post = response.get_json()
    assert post["post"]["title"] == "API Test Post"
    assert post["post"]["body"] == "Testing API endpoint"


def test_get_single_post_not_found(auth_client):
    """GET /api/posts/<id> with nonexistent id should return 404."""
    response = auth_client.get("/api/posts/99999")
    assert response.status_code == 404


def test_create_post_unauthenticated(client):
    """POST /api/posts without auth should return 401."""
    response = client.post(
        "/api/posts",
        json={
            "title": "Unauthorized Post",
            "body": "Should not be created",
            "topic_id": "",
        },
    )
    assert response.status_code == 401


def test_create_post_authenticated(auth_client):
    """POST /api/posts with valid data should create post and return 201."""
    response = auth_client.post(
        "/api/posts",
        json={
            "title": "New API Post",
            "body": "This post was created via the API",
            "topic_id": "",
        },
    )
    assert response.status_code == 201
    posts = response.get_json()
    assert "post_id" in posts


def test_create_post_missing_fields(auth_client):
    """POST /api/posts with missing title/body should return 400."""
    response = auth_client.post(
        "/api/posts",
        json={"title": "", "body": "", "topic_id": ""},
    )
    assert response.status_code == 400


def test_get_topics(client):
    """GET /api/topics should return list of topics."""
    response = client.get("/api/topics")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_get_profile(auth_client, client):
    """GET /api/profile/<username> should return user profile and posts."""
    auth_client.post(
        "/posts/new",
        data={
            "title": "Profile API Post",
            "body": "This post should appear in profile API",
            "topic_id": "",
        },
    )

    response = client.get("/api/profile/testuser")
    assert response.status_code == 200
    data = response.get_json()
    assert data["username"] == "testuser"
    assert "posts" in data


def test_get_profile_not_found(client):
    """GET /api/profile/<username> with nonexistent user should return 404."""
    response = client.get("/api/profile/nonexistentuser")
    assert response.status_code == 404
