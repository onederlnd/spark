def test_teacher_sees_announcement_option(teacher_client, classroom):
    """Announcement tab is visible to teachers who have a classroom."""
    response = teacher_client.get("/posts/new")
    assert response.status_code == 200
    assert b"announcement" in response.data.lower()
    assert b"tab-announcement" in response.data


def test_student_does_not_see_announcement_option(auth_client):
    """Announcement tab is not visible to students."""
    response = auth_client.get("/posts/new")
    assert response.status_code == 200
    assert b"Post Type" not in response.data
    assert b"Select a classroom" not in response.data


def test_teacher_classroom_appears_in_dropdown(teacher_client, classroom):
    """Teacher's classroom name appears in the announcement classroom dropdown."""
    response = teacher_client.get("/posts/new")
    assert response.status_code == 200
    assert b"Test Classroom" in response.data


def test_teacher_cannot_see_other_teachers_classroom(app, teacher_client, classroom):
    """Teacher only sees their own classrooms in the dropdown."""
    other = app.test_client(use_cookies=True)
    other.post(
        "/auth/register",
        data={
            "username": "otherteacher",
            "password": "pass123",
            "role": "teacher",
            "dob": "1985-03-10",
        },
    )
    other.post("/auth/login", data={"username": "otherteacher", "password": "pass123"})
    other.post("/classrooms/new", data={"name": "Other Teacher Classroom"})

    response = teacher_client.get("/posts/new")
    assert b"Test Classroom" in response.data
    assert b"Other Teacher Classroom" not in response.data


def test_create_announcement_success(teacher_client, classroom):
    """Teacher can post an announcement to their classroom."""
    response = teacher_client.post(
        "/posts/new",
        data={
            "title": "No class Friday",
            "body": "Field trip day — no homework.",
            "post_type": "announcement",
            "classroom_id": classroom,
        },
    )
    assert response.status_code == 302
    assert f"/classrooms/{classroom}" in response.headers["Location"]


def test_announcement_saved_to_db(app, teacher_client, classroom):
    """Announcement is persisted with post_type='announcement'."""
    teacher_client.post(
        "/posts/new",
        data={
            "title": "DB Announcement",
            "body": "Check the DB.",
            "post_type": "announcement",
            "classroom_id": classroom,
        },
    )
    with app.app_context():
        from app.models import get_db

        db = get_db()
        post = db.execute(
            "SELECT * FROM posts WHERE title = 'DB Announcement'"
        ).fetchone()
        assert post is not None
        assert post["post_type"] == "announcement"
        assert post["classroom_id"] == classroom


def test_announcement_requires_classroom(teacher_client, classroom):
    """Announcement without a classroom selection returns an error."""
    response = teacher_client.post(
        "/posts/new",
        data={
            "title": "No Classroom",
            "body": "This should fail.",
            "post_type": "announcement",
            "classroom_id": "",
        },
    )
    assert response.status_code == 200
    assert b"select a classroom" in response.data.lower()


def test_announcement_to_foreign_classroom_forbidden(app, teacher_client):
    """Teacher cannot post an announcement to another teacher's classroom."""
    other = app.test_client(use_cookies=True)
    other.post(
        "/auth/register",
        data={
            "username": "otherteacher3",
            "password": "pass123",
            "role": "teacher",
            "dob": "1985-03-10",
        },
    )
    other.post("/auth/login", data={"username": "otherteacher3", "password": "pass123"})
    other.post("/classrooms/new", data={"name": "Foreign Classroom"})

    with app.app_context():
        from app.models import get_db

        db = get_db()
        foreign = db.execute(
            "SELECT id FROM classrooms WHERE name = 'Foreign Classroom'"
        ).fetchone()
        foreign_id = foreign["id"]

    response = teacher_client.post(
        "/posts/new",
        data={
            "title": "Sneaky Announcement",
            "body": "Should be blocked.",
            "post_type": "announcement",
            "classroom_id": foreign_id,
        },
    )
    assert response.status_code == 403


def test_student_cannot_post_announcement(app, student_client, classroom):
    """Student posting with post_type=announcement is blocked."""
    # enroll student first
    with app.app_context():
        from app.models import get_db

        db = get_db()
        student = db.execute(
            "SELECT id FROM users WHERE username = 'student1'"
        ).fetchone()
        db.execute(
            "INSERT OR IGNORE INTO classroom_members (classroom_id, user_id, role) VALUES (?, ?, 'student')",
            (classroom, student["id"]),
        )
        db.commit()

    response = student_client.post(
        "/posts/new",
        data={
            "title": "Student Announcement",
            "body": "Should not work.",
            "post_type": "announcement",
            "classroom_id": classroom,
        },
    )
    assert response.status_code == 403


def test_announcement_appears_in_announcements_feed(app, teacher_client, classroom):
    """Posted announcement shows up in the announcements feed."""
    teacher_client.post(
        "/posts/new",
        data={
            "title": "Feed Announcement",
            "body": "Check the feed.",
            "post_type": "announcement",
            "classroom_id": classroom,
        },
    )
    response = teacher_client.get("/feed/announcements")
    assert response.status_code == 200
    assert b"Feed Announcement" in response.data


# --- announcement edge cases ---


def test_announcement_excluded_from_main_feed(app, teacher_client, classroom):
    """Announcements should not appear in the main post feed."""
    teacher_client.post(
        "/posts/new",
        data={
            "title": "Main Feed Exclusion Test",
            "body": "Should not be in main feed.",
            "post_type": "announcement",
            "classroom_id": classroom,
        },
    )
    response = teacher_client.get("/feed/")
    assert response.status_code == 200
    assert b"Main Feed Exclusion Test" not in response.data


def test_announcement_visible_to_enrolled_student(
    app, teacher_client, student_client, classroom
):
    """Enrolled student can see the announcement in their feed."""
    with app.app_context():
        from app.models import get_db

        db = get_db()
        student = db.execute(
            "SELECT id FROM users WHERE username = 'student1'"
        ).fetchone()
        db.execute(
            "INSERT OR IGNORE INTO classroom_members (classroom_id, user_id, role) VALUES (?, ?, 'student')",
            (classroom, student["id"]),
        )
        db.commit()

    teacher_client.post(
        "/posts/new",
        data={
            "title": "Student Visible Announcement",
            "body": "Enrolled students should see this.",
            "post_type": "announcement",
            "classroom_id": classroom,
        },
    )
    response = student_client.get("/feed/announcements")
    assert response.status_code == 200
    assert b"Student Visible Announcement" in response.data


def test_announcement_hidden_from_unenrolled_student(app, teacher_client, classroom):
    """Student not in the classroom cannot see the announcement."""
    other = app.test_client(use_cookies=True)
    other.post(
        "/auth/register",
        data={
            "username": "outsider",
            "password": "pass123",
            "dob": "2005-06-01",
        },
    )
    other.post("/auth/login", data={"username": "outsider", "password": "pass123"})

    teacher_client.post(
        "/posts/new",
        data={
            "title": "Private Classroom Announcement",
            "body": "Only enrolled students should see this.",
            "post_type": "announcement",
            "classroom_id": classroom,
        },
    )
    response = other.get("/feed/announcements")
    assert response.status_code == 200
    assert b"Private Classroom Announcement" not in response.data


def test_announcement_blocked_word_rejected(app, teacher_client, classroom):
    """Content filter applies to announcement title and body."""
    from app.utils.content_filter import add_word

    with app.app_context():
        add_word("badword", user_id=1)

    response = teacher_client.post(
        "/posts/new",
        data={
            "title": "Clean Title",
            "body": "This contains badword here.",
            "post_type": "announcement",
            "classroom_id": classroom,
        },
    )
    assert response.status_code == 200
    assert b"not allowed" in response.data


def test_announcement_blocked_word_in_title_rejected(app, teacher_client, classroom):
    """Content filter applies to announcement title."""
    from app.utils.content_filter import add_word

    with app.app_context():
        add_word("badword", user_id=1)

    response = teacher_client.post(
        "/posts/new",
        data={
            "title": "badword in title",
            "body": "Clean body.",
            "post_type": "announcement",
            "classroom_id": classroom,
        },
    )
    assert response.status_code == 200
    assert b"not allowed" in response.data


def test_announcement_empty_title_rejected(teacher_client, classroom):
    """Announcement with empty title returns an error."""
    response = teacher_client.post(
        "/posts/new",
        data={
            "title": "",
            "body": "Valid body.",
            "post_type": "announcement",
            "classroom_id": classroom,
        },
    )
    assert response.status_code == 200
    assert b"required" in response.data


def test_announcement_empty_body_rejected(teacher_client, classroom):
    """Announcement with empty body returns an error."""
    response = teacher_client.post(
        "/posts/new",
        data={
            "title": "Valid Title",
            "body": "",
            "post_type": "announcement",
            "classroom_id": classroom,
        },
    )
    assert response.status_code == 200
    assert b"required" in response.data


def test_announcement_reply(app, teacher_client, student_client, classroom):
    """Enrolled student can reply to an announcement."""
    with app.app_context():
        from app.models import get_db

        db = get_db()
        student = db.execute(
            "SELECT id FROM users WHERE username = 'student1'"
        ).fetchone()
        db.execute(
            "INSERT OR IGNORE INTO classroom_members (classroom_id, user_id, role) VALUES (?, ?, 'student')",
            (classroom, student["id"]),
        )
        db.commit()

    teacher_client.post(
        "/posts/new",
        data={
            "title": "Replyable Announcement",
            "body": "Can students reply?",
            "post_type": "announcement",
            "classroom_id": classroom,
        },
    )

    with app.app_context():
        from app.models import get_db

        db = get_db()
        post = db.execute(
            "SELECT id FROM posts WHERE title = 'Replyable Announcement'"
        ).fetchone()
        post_id = post["id"]

    response = student_client.post(
        f"/posts/{post_id}/reply",
        data={"body": "Yes we can!"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Yes we can!" in response.data
