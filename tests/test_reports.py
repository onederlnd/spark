# tests/test_reports.py


def test_student_can_report(auth_client, post):
    """Student should be able to successfully report a post"""
    response = auth_client.post(
        "/moderation/report",
        data={"post_id": post, "reason": "spam", "description": "Test report"},
        follow_redirects=True,
    )
    assert b"Report submitted successfully." in response.data


def test_prevent_duplicate_report(student_client, post):
    """Student can not report a post more than one time"""
    student_client.post("/moderation/report", data={"post_id": post, "reason": "spam"})
    response = student_client.post(
        "/moderation/report",
        data={"post_id": post, "reason": "spam"},
        follow_redirects=True,
    )
    assert b"Already reported" in response.data


def test_teacher_can_view_reports(teacher_client, classroom):
    response = teacher_client.get(f"/moderation/queue/{classroom}")

    assert response.status_code == 200


def test_teacher_can_allow_post(teacher_client, student_client, post):
    student_client.post("/moderation/report", data={"post_id": post, "reason": "spam"})
    response = teacher_client.post(
        f"/moderation/reports/{post}/resolve", follow_redirects=True
    )
    assert b"allowed" in response.data


def test_teacher_can_delete_post(teacher_client, auth_client, post):
    auth_client.post("/moderation/report", data={"post_id": post, "reason": "spam"})
    response = teacher_client.post(
        f"/moderation/reports/{post}/delete", follow_redirects=True
    )
    assert b"deleted" in response.data


def test_report_requires_login(client, post):
    res = client.post(
        "/moderation/report",
        data={
            "post_id": post,
            "reason": "spam",
        },
        follow_redirects=True,
    )
    assert res.status_code in (200, 401, 403)
    assert b"Report submitted" not in res.data


def test_report_missing_reason_rejected(auth_client, post):
    res = auth_client.post(
        "/moderation/report",
        data={
            "post_id": post,
            "reason": "",
        },
        follow_redirects=True,
    )
    assert b"Reason required" in res.data


def test_report_missing_post_id_rejected(auth_client):
    res = auth_client.post(
        "/moderation/report",
        data={
            "reason": "spam",
        },
        follow_redirects=True,
    )
    assert b"Invalid post" in res.data


def test_three_reports_auto_hides_post(app, teacher_client, classroom, post):
    for i in range(3):
        c = app.test_client()
        c.post(
            "/auth/register",
            data={
                "username": f"flagger{i}",
                "password": "pass123",
                "bio": "",
                "dob": "2000-01-01",
            },
        )
        c.post("/auth/login", data={"username": f"flagger{i}", "password": "pass123"})
        c.post(
            "/moderation/report",
            data={
                "post_id": post,
                "reason": "spam",
            },
            follow_redirects=True,
        )

    with app.app_context():
        from app.models import get_db

        p = get_db().execute("SELECT * FROM posts WHERE id = ?", (post,)).fetchone()
    assert p["is_hidden"] == 1


def test_two_reports_does_not_hide_post(app, teacher_client, classroom, post):
    for i in range(2):
        c = app.test_client()
        c.post(
            "/auth/register",
            data={
                "username": f"flagger2_{i}",
                "password": "pass123",
                "bio": "",
                "dob": "2000-01-01",
            },
        )
        c.post("/auth/login", data={"username": f"flagger2_{i}", "password": "pass123"})
        c.post(
            "/moderation/report",
            data={
                "post_id": post,
                "reason": "spam",
            },
            follow_redirects=True,
        )

    with app.app_context():
        from app.models import get_db

        p = get_db().execute("SELECT * FROM posts WHERE id = ?", (post,)).fetchone()
    assert p["is_hidden"] == 0


def test_student_cannot_access_moderation_queue(student_client, classroom):
    res = student_client.get(f"/moderation/queue/{classroom}")
    assert res.status_code == 403


def test_anonymous_cannot_access_moderation_queue(client, classroom):
    res = client.get(f"/moderation/queue/{classroom}", follow_redirects=True)
    assert res.status_code in (200, 401, 403)
    assert b"queue" not in res.data.lower() or b"login" in res.data.lower()


def test_allow_clears_pending_reports(
    teacher_client, auth_client, app, classroom, post
):
    auth_client.post(
        "/moderation/report",
        data={
            "post_id": post,
            "reason": "spam",
        },
        follow_redirects=True,
    )
    teacher_client.post(f"/moderation/reports/{post}/resolve", follow_redirects=True)

    with app.app_context():
        from app.models import get_db

        pending = (
            get_db()
            .execute(
                "SELECT * FROM reports WHERE post_id = ? AND status = 'pending'",
                (post,),
            )
            .fetchall()
        )
    assert len(pending) == 0


def test_allow_sets_report_status_to_allowed(
    teacher_client, auth_client, app, classroom, post
):
    auth_client.post(
        "/moderation/report",
        data={
            "post_id": post,
            "reason": "spam",
        },
        follow_redirects=True,
    )
    teacher_client.post(f"/moderation/reports/{post}/resolve", follow_redirects=True)

    with app.app_context():
        from app.models import get_db

        report = (
            get_db()
            .execute("SELECT * FROM reports WHERE post_id = ?", (post,))
            .fetchone()
        )
    assert report["status"] == "allowed"


def test_delete_sets_report_status_to_deleted(
    teacher_client, auth_client, app, classroom, post
):
    auth_client.post(
        "/moderation/report",
        data={
            "post_id": post,
            "reason": "spam",
        },
        follow_redirects=True,
    )
    teacher_client.post(f"/moderation/reports/{post}/delete", follow_redirects=True)

    with app.app_context():
        from app.models import get_db

        report = (
            get_db()
            .execute("SELECT * FROM reports WHERE post_id = ?", (post,))
            .fetchone()
        )
    assert report["status"] == "deleted"


def test_delete_removes_post(teacher_client, auth_client, app, classroom, post):
    auth_client.post(
        "/moderation/report",
        data={
            "post_id": post,
            "reason": "spam",
        },
        follow_redirects=True,
    )
    teacher_client.post(f"/moderation/reports/{post}/delete", follow_redirects=True)

    with app.app_context():
        from app.models import get_db

        p = get_db().execute("SELECT * FROM posts WHERE id = ?", (post,)).fetchone()
    assert p is None or p["deleted"] == 1


def test_resolve_nonexistent_post_returns_404(teacher_client):
    res = teacher_client.post(
        "/moderation/reports/99999/resolve", follow_redirects=True
    )
    assert res.status_code == 404


def test_delete_nonexistent_post_returns_404(teacher_client):
    res = teacher_client.post("/moderation/reports/99999/delete", follow_redirects=True)
    assert res.status_code == 404


def test_student_cannot_resolve_post(student_client, auth_client, classroom, post):
    auth_client.post(
        "/moderation/report",
        data={
            "post_id": post,
            "reason": "spam",
        },
        follow_redirects=True,
    )
    res = student_client.post(
        f"/moderation/reports/{post}/resolve", follow_redirects=True
    )
    assert res.status_code in (200, 403)
    assert b"Post reviewed and allowed" not in res.data


def test_student_cannot_delete_post(student_client, auth_client, classroom, post):
    auth_client.post(
        "/moderation/report",
        data={
            "post_id": post,
            "reason": "spam",
        },
        follow_redirects=True,
    )
    res = student_client.post(
        f"/moderation/reports/{post}/delete", follow_redirects=True
    )
    assert res.status_code in (200, 403)
    assert b"Post deleted" not in res.data


def test_resolved_reports_not_in_queue(teacher_client, auth_client, classroom, post):
    auth_client.post(
        "/moderation/report",
        data={
            "post_id": post,
            "reason": "spam",
        },
        follow_redirects=True,
    )
    teacher_client.post(f"/moderation/reports/{post}/resolve", follow_redirects=True)
    res = teacher_client.get(f"/moderation/queue/{classroom}")
    assert res.status_code == 200
    assert b"Test Post" not in res.data


def test_auto_flag_creates_system_report(app, teacher_client, classroom, post):
    with app.app_context():
        from app.models.report import auto_flag_post

        auto_flag_post(post, ["badword", "inappropriate"])

        from app.models import get_db

        report = (
            get_db()
            .execute(
                "SELECT * FROM reports WHERE post_id = ? AND reported_by_user_id IS NULL",
                (post,),
            )
            .fetchone()
        )
    assert report is not None
    assert "badword" in report["description"]
    assert report["status"] == "pending"


def test_auto_flag_hides_post(app, teacher_client, classroom, post):
    with app.app_context():
        from app.models.report import auto_flag_post

        auto_flag_post(post, ["badword"])

        from app.models import get_db

        p = get_db().execute("SELECT * FROM posts WHERE id = ?", (post,)).fetchone()
    assert p["is_hidden"] == 1
