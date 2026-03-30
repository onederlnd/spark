def test_feed_pagination_page_1(auth_client):
    response = auth_client.get("/feed/?page=1")
    assert response.status_code == 200


def test_feed_pagination_high_page(auth_client):
    response = auth_client.get("/feed/?page=99")
    assert response.status_code == 200


def test_following_feed_pagination(auth_client):
    response = auth_client.get("/feed/following?page=1")
    assert response.status_code == 200


def test_feed_invalid_page_param(auth_client):
    """Non-integer page param should not crash."""
    response = auth_client.get("/feed/?page=abc", follow_redirects=True)
    assert response.status_code == 200
