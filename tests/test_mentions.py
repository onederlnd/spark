# tests/test_mentions.py

from app.utils.sanitize import extract_mentions


# --- extract_mentions unit tests ---


def test_extract_single_mention():
    assert "alice" in extract_mentions("Hello @alice how are you?")


def test_extract_multiple_mentions():
    mentions = extract_mentions("Hey @alice and @bob check this out")
    assert "alice" in mentions
    assert "bob" in mentions


def test_extract_no_mentions():
    assert extract_mentions("No mentions here") == []


def test_extract_duplicate_mentions_deduplicated():
    mentions = extract_mentions("@alice @alice @alice")
    assert mentions.count("alice") == 1


def test_extract_mention_at_start():
    assert "alice" in extract_mentions("@alice said something")


def test_extract_mention_at_end():
    assert "alice" in extract_mentions("great work @alice")


def test_extract_mention_with_underscores():
    assert "alice_smith" in extract_mentions("thanks @alice_smith")


def test_extract_mention_ignores_email():
    """Email addresses should not produce mentions."""
    mentions = extract_mentions("email me at alice@example.com")
    assert "example" not in mentions


def test_extract_mention_empty_string():
    assert extract_mentions("") == []


def test_extract_mention_only_at_symbol():
    assert extract_mentions("@ hello") == []


def test_extract_mention_numbers_in_username():
    assert "user123" in extract_mentions("hey @user123")


def test_extract_mention_mixed_content():
    mentions = extract_mentions(
        "[b]bold[/b] @alice and @bob [url=http://x.com]link[/url]"
    )
    assert "alice" in mentions
    assert "bob" in mentions


# --- notify_mentions unit tests ---


def test_mention_creates_notification(app, auth_client):
    """Posting with @mention fires a notification for the mentioned user."""
    # register a second user to be mentioned
    other = app.test_client()
    other.post(
        "/auth/register",
        data={
            "username": "mentioned_user",
            "password": "pass123",
            "dob": "2000-01-01",
        },
    )

    auth_client.post(
        "/posts/new",
        data={
            "title": "Mention Test",
            "body": "Hey @mentioned_user check this out",
            "topic_id": "",
        },
    )

    with app.app_context():
        from app.models import get_db

        db = get_db()
        user = db.execute(
            "SELECT id FROM users WHERE username = 'mentioned_user'"
        ).fetchone()
        notif = db.execute(
            "SELECT * FROM notifications WHERE user_id = ? AND type = 'mention'",
            (user["id"],),
        ).fetchone()
        assert notif is not None
        assert "testuser" in notif["message"]


def test_mention_links_to_post(app, auth_client):
    """Mention notification link points to the correct post."""
    other = app.test_client()
    other.post(
        "/auth/register",
        data={
            "username": "linkuser",
            "password": "pass123",
            "dob": "2000-01-01",
        },
    )

    response = auth_client.post(
        "/posts/new",
        data={
            "title": "Link Test",
            "body": "Hey @linkuser",
            "topic_id": "",
        },
    )
    post_id = response.headers["Location"].split("/")[-1]

    with app.app_context():
        from app.models import get_db

        db = get_db()
        user = db.execute("SELECT id FROM users WHERE username = 'linkuser'").fetchone()
        notif = db.execute(
            "SELECT * FROM notifications WHERE user_id = ? AND type = 'mention'",
            (user["id"],),
        ).fetchone()
        assert f"/posts/{post_id}" in notif["link"]


def test_self_mention_does_not_create_notification(app, auth_client):
    """Author mentioning themselves does not create a notification."""
    auth_client.post(
        "/posts/new",
        data={
            "title": "Self Mention",
            "body": "Look at me @testuser",
            "topic_id": "",
        },
    )

    with app.app_context():
        from app.models import get_db

        db = get_db()
        user = db.execute("SELECT id FROM users WHERE username = 'testuser'").fetchone()
        notif = db.execute(
            "SELECT * FROM notifications WHERE user_id = ? AND type = 'mention'",
            (user["id"],),
        ).fetchone()
        assert notif is None


def test_mention_nonexistent_user_no_error(auth_client):
    """Mentioning a username that doesn't exist does not crash."""
    response = auth_client.post(
        "/posts/new",
        data={
            "title": "Ghost Mention",
            "body": "Hey @doesnotexist_xyz",
            "topic_id": "",
        },
    )
    assert response.status_code == 302


def test_multiple_mentions_all_notified(app, auth_client):
    """All mentioned users receive notifications."""
    for username in ["userA", "userB", "userC"]:
        c = app.test_client()
        c.post(
            "/auth/register",
            data={
                "username": username,
                "password": "pass123",
                "dob": "2000-01-01",
            },
        )

    auth_client.post(
        "/posts/new",
        data={
            "title": "Multi Mention",
            "body": "Hello @userA, @userB, and @userC",
            "topic_id": "",
        },
    )

    with app.app_context():
        from app.models import get_db

        db = get_db()
        for username in ["userA", "userB", "userC"]:
            user = db.execute(
                "SELECT id FROM users WHERE username = ?", (username,)
            ).fetchone()
            notif = db.execute(
                "SELECT * FROM notifications WHERE user_id = ? AND type = 'mention'",
                (user["id"],),
            ).fetchone()
            assert notif is not None, (
                f"{username} should have received a mention notification"
            )


def test_duplicate_mention_only_one_notification(app, auth_client):
    """Mentioning the same user twice only fires one notification."""
    other = app.test_client()
    other.post(
        "/auth/register",
        data={
            "username": "dupuser",
            "password": "pass123",
            "dob": "2000-01-01",
        },
    )

    auth_client.post(
        "/posts/new",
        data={
            "title": "Dupe Mention",
            "body": "@dupuser @dupuser @dupuser",
            "topic_id": "",
        },
    )

    with app.app_context():
        from app.models import get_db

        db = get_db()
        user = db.execute("SELECT id FROM users WHERE username = 'dupuser'").fetchone()
        count = db.execute(
            "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND type = 'mention'",
            (user["id"],),
        ).fetchone()[0]
        assert count == 1


def test_mention_in_reply_creates_notification(app, auth_client):
    """Mentioning a user in a reply also fires a notification."""
    other = app.test_client()
    other.post(
        "/auth/register",
        data={
            "username": "replymentioned",
            "password": "pass123",
            "dob": "2000-01-01",
        },
    )

    post_resp = auth_client.post(
        "/posts/new",
        data={
            "title": "Reply Mention Test",
            "body": "Original post",
            "topic_id": "",
        },
    )
    post_id = post_resp.headers["Location"].split("/")[-1]

    auth_client.post(
        f"/posts/{post_id}/reply",
        data={
            "body": "Hey @replymentioned look at this",
        },
    )

    with app.app_context():
        from app.models import get_db

        db = get_db()
        user = db.execute(
            "SELECT id FROM users WHERE username = 'replymentioned'"
        ).fetchone()
        notif = db.execute(
            "SELECT * FROM notifications WHERE user_id = ? AND type = 'mention'",
            (user["id"],),
        ).fetchone()
        assert notif is not None


def test_mention_no_notification_without_post(app):
    """notify_mentions called with no matching users does nothing."""
    with app.app_context():
        from app.models.notifications import notify_mentions

        # should not raise
        notify_mentions("Hey @nobody_xyz", post_id=999, author_id=1)


# --- render tests ---


def test_mention_renders_as_link(app, auth_client):
    """@username in post body renders as a profile link."""
    other = app.test_client()
    other.post(
        "/auth/register",
        data={
            "username": "renderuser",
            "password": "pass123",
            "dob": "2000-01-01",
        },
    )

    response = auth_client.post(
        "/posts/new",
        data={
            "title": "Render Test",
            "body": "Hello @renderuser",
            "topic_id": "",
        },
    )
    post_url = response.headers["Location"]
    response = auth_client.get(post_url)

    assert b"/profile/renderuser" in response.data
    assert b"mention" in response.data


def test_mention_renders_as_link_in_reply(app, auth_client):
    """@username in reply body renders as a profile link."""
    other = app.test_client()
    other.post(
        "/auth/register",
        data={
            "username": "replyrender",
            "password": "pass123",
            "dob": "2000-01-01",
        },
    )

    post_resp = auth_client.post(
        "/posts/new",
        data={
            "title": "Reply Render Test",
            "body": "Original",
            "topic_id": "",
        },
    )
    post_id = post_resp.headers["Location"].split("/")[-1]

    auth_client.post(
        f"/posts/{post_id}/reply",
        data={
            "body": "Hey @replyrender",
        },
    )

    response = auth_client.get(f"/posts/{post_id}")
    assert b"/profile/replyrender" in response.data


def test_nonexistent_mention_does_not_render_link(app, auth_client):
    """@username for a user that doesn't exist still renders safely without crashing."""
    response = auth_client.post(
        "/posts/new",
        data={
            "title": "Ghost Render",
            "body": "Hey @totallymadeupuser999",
            "topic_id": "",
        },
    )
    post_url = response.headers["Location"]
    response = auth_client.get(post_url)
    assert response.status_code == 200


def test_mention_css_class_present(app, auth_client):
    """Rendered mention has the 'mention' CSS class."""
    other = app.test_client()
    other.post(
        "/auth/register",
        data={
            "username": "cssuser",
            "password": "pass123",
            "dob": "2000-01-01",
        },
    )

    response = auth_client.post(
        "/posts/new",
        data={
            "title": "CSS Class Test",
            "body": "Hey @cssuser",
            "topic_id": "",
        },
    )
    post_url = response.headers["Location"]
    response = auth_client.get(post_url)
    assert b'class="mention"' in response.data


# --- XSS safety ---


def test_mention_xss_safe(auth_client):
    """Malicious username in mention cannot inject executable HTML."""
    response = auth_client.post(
        "/posts/new",
        data={
            "title": "XSS Mention",
            "body": "@<script>alert('xss')</script>",
            "topic_id": "",
        },
    )
    post_url = response.headers["Location"]
    response = auth_client.get(post_url)
    assert b"<script>alert" not in response.data


def test_mention_in_bbcode_context(app, auth_client):
    """Mentions work correctly inside BBCode tags."""
    other = app.test_client()
    other.post(
        "/auth/register",
        data={
            "username": "bbcodeuser",
            "password": "pass123",
            "dob": "2000-01-01",
        },
    )

    response = auth_client.post(
        "/posts/new",
        data={
            "title": "BBCode Mention",
            "body": "[b]Hello[/b] @bbcodeuser [i]how are you?[/i]",
            "topic_id": "",
        },
    )
    post_url = response.headers["Location"]
    response = auth_client.get(post_url)
    assert b"/profile/bbcodeuser" in response.data
    assert b"<b>Hello</b>" in response.data or b"<strong>" in response.data


# tests/test_mention_notifications.py

# --- mention notification tests for student and teacher roles ---


def _approve_coppa(app, username):
    """Helper: set coppa_status = approved for a user."""
    with app.app_context():
        from app.models import get_db

        db = get_db()
        db.execute(
            "UPDATE users SET coppa_status = 'approved' WHERE username = ?",
            (username,),
        )
        db.commit()


def _get_mention_notif(app, username):
    """Helper: fetch the first mention notification for a user."""
    with app.app_context():
        from app.models import get_db

        db = get_db()
        user = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        return db.execute(
            "SELECT * FROM notifications WHERE user_id = ? AND type = 'mention'",
            (user["id"],),
        ).fetchone()


def _get_unread_count(app, username):
    """Helper: fetch unread notification count for a user."""
    with app.app_context():
        from app.models import get_db

        db = get_db()
        user = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        return db.execute(
            "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
            (user["id"],),
        ).fetchone()[0]


# ---------------------------------------------------------------------------
# student mention tests
# ---------------------------------------------------------------------------


def test_student_receives_mention_notification(app, teacher_client):
    """Teacher mentioning a student creates a mention notification for that student."""
    _approve_coppa(app, "teacher1")

    student = app.test_client()
    student.post(
        "/auth/register",
        data={
            "username": "student_mention",
            "password": "pass123",
            "dob": "2008-01-01",
        },
    )
    _approve_coppa(app, "student_mention")

    teacher_client.post(
        "/posts/new",
        data={
            "title": "Hey Student",
            "body": "Check this out @student_mention",
            "topic_id": "",
        },
    )

    notif = _get_mention_notif(app, "student_mention")
    assert notif is not None
    assert notif["type"] == "mention"
    assert "teacher1" in notif["message"]


def test_student_mention_notification_link_valid(app, teacher_client):
    """Mention notification for student links to the correct post."""
    _approve_coppa(app, "teacher1")

    student = app.test_client()
    student.post(
        "/auth/register",
        data={"username": "student_link", "password": "pass123", "dob": "2008-01-01"},
    )
    _approve_coppa(app, "student_link")

    resp = teacher_client.post(
        "/posts/new",
        data={
            "title": "Link Test",
            "body": "Hey @student_link",
            "topic_id": "",
        },
    )
    post_id = resp.headers["Location"].split("/")[-1]

    notif = _get_mention_notif(app, "student_link")
    assert notif is not None
    assert f"/posts/{post_id}" in notif["link"]


def test_student_mention_shows_on_notifications_page(app, teacher_client):
    """Mention notification appears on the student's /notifications/ page."""
    _approve_coppa(app, "teacher1")

    student = app.test_client()
    student.post(
        "/auth/register",
        data={
            "username": "student_notifpage",
            "password": "pass123",
            "dob": "2008-01-01",
        },
    )
    _approve_coppa(app, "student_notifpage")
    student.post(
        "/auth/login", data={"username": "student_notifpage", "password": "pass123"}
    )

    teacher_client.post(
        "/posts/new",
        data={
            "title": "Notif Page Test",
            "body": "Hey @student_notifpage",
            "topic_id": "",
        },
    )

    resp = student.get("/notifications/")
    assert resp.status_code == 200
    assert b"mention" in resp.data.lower()
    assert b"teacher1" in resp.data


def test_student_mention_increments_bell_count(app, teacher_client):
    """Unread notification count increments for student after mention."""
    _approve_coppa(app, "teacher1")

    student = app.test_client()
    student.post(
        "/auth/register",
        data={"username": "student_bell", "password": "pass123", "dob": "2008-01-01"},
    )
    _approve_coppa(app, "student_bell")
    student.post(
        "/auth/login", data={"username": "student_bell", "password": "pass123"}
    )

    before = _get_unread_count(app, "student_bell")

    teacher_client.post(
        "/posts/new",
        data={
            "title": "Bell Test",
            "body": "Hey @student_bell",
            "topic_id": "",
        },
    )

    after = _get_unread_count(app, "student_bell")
    assert after == before + 1


def test_student_bell_count_visible_in_nav(app, teacher_client):
    """Nav badge appears for student after receiving a mention notification."""
    _approve_coppa(app, "teacher1")

    with app.test_client() as student:
        student.post(
            "/auth/register",
            data={
                "username": "student_nav",
                "password": "pass123",
                "dob": "2008-01-01",
            },
        )
        _approve_coppa(app, "student_nav")
        student.post(
            "/auth/login",
            data={"username": "student_nav", "password": "pass123"},
            follow_redirects=True,
        )

        teacher_client.post(
            "/posts/new",
            data={
                "title": "Nav Badge Test",
                "body": "Hey @student_nav",
                "topic_id": "",
            },
        )

        resp = student.get("/", follow_redirects=True)
        print(resp.data)
        assert resp.status_code == 200
        assert b"nav-badge" in resp.data


def test_student_mention_in_reply_creates_notification(app, teacher_client):
    """Mentioning a student in a reply fires a notification."""
    _approve_coppa(app, "teacher1")

    student = app.test_client()
    student.post(
        "/auth/register",
        data={
            "username": "student_reply_mention",
            "password": "pass123",
            "dob": "2008-01-01",
        },
    )
    _approve_coppa(app, "student_reply_mention")

    post_resp = teacher_client.post(
        "/posts/new",
        data={"title": "Reply Mention", "body": "Original post", "topic_id": ""},
    )
    post_id = post_resp.headers["Location"].split("/")[-1]

    teacher_client.post(
        f"/posts/{post_id}/reply",
        data={"body": "Hey @student_reply_mention check this"},
    )

    notif = _get_mention_notif(app, "student_reply_mention")
    assert notif is not None
    assert notif["type"] == "mention"


# ---------------------------------------------------------------------------
# teacher mention tests
# ---------------------------------------------------------------------------


def test_teacher_receives_mention_notification(app, teacher_client):
    """Student mentioning a teacher creates a mention notification."""
    _approve_coppa(app, "teacher1")

    # second teacher to be mentioned
    other_teacher = app.test_client()
    other_teacher.post(
        "/auth/register",
        data={
            "username": "teacher_mentioned",
            "password": "pass123",
            "role": "teacher",
            "dob": "1985-01-01",
        },
    )
    _approve_coppa(app, "teacher_mentioned")

    teacher_client.post(
        "/posts/new",
        data={
            "title": "Teacher Mention",
            "body": "Hey @teacher_mentioned look at this",
            "topic_id": "",
        },
    )

    notif = _get_mention_notif(app, "teacher_mentioned")
    assert notif is not None
    assert notif["type"] == "mention"
    assert "teacher1" in notif["message"]


def test_teacher_mention_shows_on_notifications_page(app, teacher_client):
    """Mention notification appears on the mentioned teacher's /notifications/ page."""
    _approve_coppa(app, "teacher1")

    other_teacher = app.test_client()
    other_teacher.post(
        "/auth/register",
        data={
            "username": "teacher_notifpage",
            "password": "pass123",
            "role": "teacher",
            "dob": "1985-01-01",
        },
    )
    _approve_coppa(app, "teacher_notifpage")
    other_teacher.post(
        "/auth/login", data={"username": "teacher_notifpage", "password": "pass123"}
    )

    teacher_client.post(
        "/posts/new",
        data={
            "title": "Teacher Notif Page",
            "body": "Hey @teacher_notifpage",
            "topic_id": "",
        },
    )

    resp = other_teacher.get("/notifications/")
    assert resp.status_code == 200
    assert b"mention" in resp.data.lower()
    assert b"teacher1" in resp.data


def test_teacher_mention_increments_bell_count(app, teacher_client):
    """Unread notification count increments for teacher after mention."""
    _approve_coppa(app, "teacher1")

    other_teacher = app.test_client()
    other_teacher.post(
        "/auth/register",
        data={
            "username": "teacher_bell",
            "password": "pass123",
            "role": "teacher",
            "dob": "1985-01-01",
        },
    )
    _approve_coppa(app, "teacher_bell")
    other_teacher.post(
        "/auth/login",
        data={"username": "teacher_bell", "password": "pass123"},
        follow_redirects=True,
    )

    before = _get_unread_count(app, "teacher_bell")

    teacher_client.post(
        "/posts/new",
        data={
            "title": "Teacher Bell",
            "body": "Hey @teacher_bell",
            "topic_id": "",
        },
    )

    after = _get_unread_count(app, "teacher_bell")
    assert after == before + 1


def test_teacher_bell_count_visible_in_nav(app, teacher_client):
    """Nav badge appears for teacher after receiving a mention notification."""
    _approve_coppa(app, "teacher1")

    with app.test_client() as other_teacher:
        other_teacher.post(
            "/auth/register",
            data={
                "username": "teacher_nav",
                "password": "pass123",
                "role": "teacher",
                "dob": "1985-01-01",
            },
        )
        _approve_coppa(app, "teacher_nav")
        other_teacher.post(
            "/auth/login",
            data={"username": "teacher_nav", "password": "pass123"},
            follow_redirects=True,
        )

        teacher_client.post(
            "/posts/new",
            data={
                "title": "Teacher Nav Badge",
                "body": "Hey @teacher_nav",
                "topic_id": "",
            },
        )

        resp = other_teacher.get("/", follow_redirects=True)
        assert resp.status_code == 200
        assert b"nav-badge" in resp.data


def test_teacher_mention_notification_link_valid(app, teacher_client):
    """Mention notification for teacher links to the correct post."""
    _approve_coppa(app, "teacher1")

    other_teacher = app.test_client()
    other_teacher.post(
        "/auth/register",
        data={
            "username": "teacher_linkcheck",
            "password": "pass123",
            "role": "teacher",
            "dob": "1985-01-01",
        },
    )
    _approve_coppa(app, "teacher_linkcheck")

    resp = teacher_client.post(
        "/posts/new",
        data={
            "title": "Teacher Link",
            "body": "Hey @teacher_linkcheck",
            "topic_id": "",
        },
    )
    post_id = resp.headers["Location"].split("/")[-1]

    notif = _get_mention_notif(app, "teacher_linkcheck")
    assert notif is not None
    assert f"/posts/{post_id}" in notif["link"]


def test_self_mention_no_notification_teacher(app, teacher_client):
    """Teacher mentioning themselves does not create a notification."""
    _approve_coppa(app, "teacher1")

    teacher_client.post(
        "/posts/new",
        data={
            "title": "Self Mention Teacher",
            "body": "Look at me @teacher1",
            "topic_id": "",
        },
    )

    notif = _get_mention_notif(app, "teacher1")
    assert notif is None
