def test_view_topics(auth_client):
    response = auth_client.get("/topics")
    assert response.status_code == 200
    assert b"All Topics" in response.data


def test_create_topic(auth_client):
    response = auth_client.post(
        "/topics/new", data={"name": "newtopic", "description": "A brand new topic"}
    )
    assert response.status_code == 302
    assert "newtopic" in response.headers["Location"]


def test_create_topic_invalid_name(auth_client):
    response = auth_client.post(
        "/topics/new", data={"name": "Invalid Topic Name!", "description": ""}
    )
    assert response.status_code == 200
    assert b"only contain" in response.data


def test_create_duplicate_topic(auth_client):
    auth_client.post("/topics/new", data={"name": "duplicate", "description": ""})
    response = auth_client.post(
        "/topics/new", data={"name": "duplicate", "description": ""}
    )
    response = auth_client.post(
        "/topics/new", data={"name": "duplicate", "description": ""}
    )
    assert response.status_code == 200
    assert b"already exists" in response.data


def test_create_topic_too_short(auth_client):
    response = auth_client.post("/topics/new", data={"name": "a", "description": ""})
    assert response.status_code == 200
    assert b"between 2 and 30" in response.data


def test_topic_feed(auth_client):
    auth_client.post("/topics/new", data={"name": "testfeed", "description": "test"})

    response = auth_client.get("/feed/t/testfeed")
    assert response.status_code == 200
    assert b"testfeed" in response.data
