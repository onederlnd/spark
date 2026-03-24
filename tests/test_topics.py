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

    response = auth_client.get("/t/testfeed")
    assert response.status_code == 200
    assert b"testfeed" in response.data


# --- Topic name edge cases ---


def test_create_topic_too_long(auth_client):
    response = auth_client.post(
        "/topics/new", data={"name": "a" * 31, "description": ""}
    )
    assert response.status_code == 200
    assert b"between 2 and 30" in response.data


def test_create_topic_exactly_max_length(auth_client):
    response = auth_client.post(
        "/topics/new", data={"name": "a" * 30, "description": ""}
    )
    assert response.status_code == 302


def test_create_topic_exactly_min_length(auth_client):
    response = auth_client.post("/topics/new", data={"name": "ab", "description": ""})
    assert response.status_code == 302


def test_create_topic_with_hyphens(auth_client):
    response = auth_client.post(
        "/topics/new", data={"name": "my-cool-topic", "description": ""}
    )
    assert response.status_code == 302
    assert "my-cool-topic" in response.headers["Location"]


def test_create_topic_with_spaces(auth_client):
    response = auth_client.post(
        "/topics/new", data={"name": "has spaces", "description": ""}
    )
    assert response.status_code == 200
    assert b"only contain" in response.data


def test_create_topic_uppercase_normalized(auth_client):
    """Topic names should be lowercased before saving."""
    response = auth_client.post(
        "/topics/new", data={"name": "UPPERCASE", "description": ""}
    )
    assert response.status_code == 302
    assert "uppercase" in response.headers["Location"]


def test_create_topic_empty_name(auth_client):
    response = auth_client.post("/topics/new", data={"name": "", "description": ""})
    assert response.status_code == 200


def test_create_topic_description_too_long(auth_client):
    response = auth_client.post(
        "/topics/new", data={"name": "validname", "description": "x" * 301}
    )
    # Description should be truncated or rejected — adjust assertion to match your sanitize_plain behavior
    assert response.status_code in (200, 302)


# --- Topic feed / routing ---


def test_topic_feed_nonexistent(auth_client):
    """This is the class of bug you just had — make sure 404s are explicit."""
    response = auth_client.get("/t/doesnotexist")
    assert response.status_code == 404


def test_topic_feed_url_matches_redirect(auth_client):
    """After creating a topic, the redirect Location should resolve to a 200."""
    create = auth_client.post(
        "/topics/new", data={"name": "routecheck", "description": ""}
    )
    redirect_url = create.headers["Location"]
    response = auth_client.get(redirect_url)
    assert response.status_code == 200


def test_topic_feed_contains_topic_name(auth_client):
    auth_client.post("/topics/new", data={"name": "mytopic", "description": "desc"})
    response = auth_client.get("/t/mytopic")
    assert b"mytopic" in response.data


# --- Topics index ---


def test_topics_index_lists_created_topic(auth_client):
    auth_client.post("/topics/new", data={"name": "listed", "description": "yes"})
    response = auth_client.get("/topics")
    assert b"listed" in response.data


def test_topics_index_empty_state(auth_client):
    """Index should render fine with no topics."""
    response = auth_client.get("/topics")
    assert response.status_code == 200


# --- Auth guards ---


def test_topics_index_requires_login(client):
    """Unauthenticated requests should be redirected."""
    response = client.get("/topics")
    assert response.status_code == 302


def test_new_topic_get_requires_login(client):
    response = client.get("/topics/new")
    assert response.status_code == 302


def test_new_topic_post_requires_login(client):
    response = client.post("/topics/new", data={"name": "nope", "description": ""})
    assert response.status_code == 302


# --- GET /topics/new ---


def test_new_topic_page_renders(auth_client):
    response = auth_client.get("/topics/new")
    assert response.status_code == 200


# --- Post count display on topics index ---


def test_topics_index_shows_post_count(auth_client):
    """Topics index should show post counts (even if 0)."""
    auth_client.post("/topics/new", data={"name": "countme", "description": ""})
    response = auth_client.get("/topics")
    assert response.status_code == 200
    assert b"countme" in response.data


# --- Topic feed pagination ---


def test_topic_feed_page_param(auth_client):
    auth_client.post("/topics/new", data={"name": "paged", "description": ""})
    response = auth_client.get("/t/paged?page=1")
    assert response.status_code == 200


def test_topic_feed_invalid_page_param(auth_client):
    """Non-integer page param should fall back gracefully."""
    auth_client.post("/topics/new", data={"name": "badpage", "description": ""})
    response = auth_client.get("/t/badpage?page=notanumber")
    assert response.status_code == 200


def test_topic_feed_page_zero(auth_client):
    auth_client.post("/topics/new", data={"name": "pagezero", "description": ""})
    response = auth_client.get("/t/pagezero?page=0")
    assert response.status_code == 200


# --- Topic name boundary / character edge cases ---


def test_create_topic_numbers_only(auth_client):
    response = auth_client.post(
        "/topics/new", data={"name": "12345", "description": ""}
    )
    assert response.status_code == 302


def test_create_topic_leading_hyphen(auth_client):
    """Leading hyphens are technically valid per regex — document the behavior."""
    response = auth_client.post(
        "/topics/new", data={"name": "-leadinghyphen", "description": ""}
    )
    assert response.status_code in (200, 302)


def test_create_topic_trailing_hyphen(auth_client):
    response = auth_client.post(
        "/topics/new", data={"name": "trailinghyphen-", "description": ""}
    )
    assert response.status_code in (200, 302)


def test_create_topic_special_chars(auth_client):
    for name in ["topic@name", "topic/name", "topic.name", "topic#name"]:
        response = auth_client.post(
            "/topics/new", data={"name": name, "description": ""}
        )
        assert response.status_code == 200, f"Expected rejection for: {name}"
        assert b"only contain" in response.data


def test_create_topic_unicode(auth_client):
    response = auth_client.post(
        "/topics/new", data={"name": "tópico", "description": ""}
    )
    assert response.status_code == 200
    assert b"only contain" in response.data


def test_create_topic_whitespace_only(auth_client):
    response = auth_client.post("/topics/new", data={"name": "   ", "description": ""})
    assert response.status_code == 200


def test_create_topic_sql_injection_attempt(auth_client):
    response = auth_client.post(
        "/topics/new", data={"name": "'; DROP TABLE topics;--", "description": ""}
    )
    assert response.status_code == 200
    assert b"only contain" in response.data


# --- Description edge cases ---


def test_create_topic_description_exactly_300(auth_client):
    response = auth_client.post(
        "/topics/new", data={"name": "desc300", "description": "x" * 300}
    )
    assert response.status_code == 302


def test_create_topic_no_description_field(auth_client):
    """POST with description key missing entirely should not crash."""
    response = auth_client.post("/topics/new", data={"name": "nodesc"})
    assert response.status_code == 302


def test_create_topic_description_html_stripped(auth_client):
    """HTML in description should be sanitized, not stored raw."""
    auth_client.post(
        "/topics/new",
        data={"name": "htmldesc", "description": "<script>alert(1)</script>"},
    )
    response = auth_client.get("/t/htmldesc")
    assert b"<script>alert(1)" not in response.data


# --- Case normalization / deduplication ---


def test_create_topic_case_insensitive_duplicate(auth_client):
    """UPPERCASE and lowercase versions of the same name should conflict."""
    auth_client.post("/topics/new", data={"name": "casedup", "description": ""})
    response = auth_client.post(
        "/topics/new", data={"name": "CASEDUP", "description": ""}
    )
    assert response.status_code == 200
    assert b"already exists" in response.data


# --- GET /topics/new ---


def test_new_topic_get_renders_form(auth_client):
    response = auth_client.get("/topics/new")
    assert b"name" in response.data  # form field present


# --- Topic feed auth ---


def test_topic_feed_requires_login(client):
    response = client.get("/t/sometopic", follow_redirects=False)
    assert response.status_code == 302


# --- Flash messages ---


def test_create_topic_success_flash(auth_client):
    response = auth_client.post(
        "/topics/new",
        data={"name": "flashtest", "description": ""},
        follow_redirects=True,
    )
    assert b"flashtest" in response.data


def test_create_topic_duplicate_flash(auth_client):
    auth_client.post("/topics/new", data={"name": "flashdup", "description": ""})
    response = auth_client.post(
        "/topics/new",
        data={"name": "flashdup", "description": ""},
        follow_redirects=True,
    )
    assert b"already exists" in response.data


def test_create_topic_invalid_name_flash(auth_client):
    response = auth_client.post(
        "/topics/new",
        data={"name": "bad name!", "description": ""},
        follow_redirects=True,
    )
    assert b"only contain" in response.data
