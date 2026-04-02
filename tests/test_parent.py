# tests/test_parent.p

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _register_student(app, username="student_parent_test"):
    """Register a student via the generic route and return their user id."""
    c = app.test_client()
    c.post(
        "/auth/register",
        data={
            "username": username,
            "password": "pass123",
            "bio": "",
            "dob": "2000-01-01",
        },
    )
    with app.app_context():
        from app.models import get_db

        row = (
            get_db()
            .execute("SELECT id FROM users WHERE username = ?", (username,))
            .fetchone()
        )
    return row["id"]


def _get_invite_code(app, teacher_client, student_id):
    """Generate a parent invite code for a student and return it."""
    teacher_client.post(f"/parent/invite/{student_id}")
    with app.app_context():
        from app.models import get_db

        row = (
            get_db()
            .execute(
                "SELECT code FROM parent_invite_codes WHERE student_id = ?",
                (student_id,),
            )
            .fetchone()
        )
    return row["code"]


def _register_parent(client, *, first="Jane", last="Smith", password="pass1234"):
    """POST to /parent/register and follow redirects."""
    return client.post(
        "/parent/register",
        data={"first_name": first, "last_name": last, "password": password},
        follow_redirects=True,
    )


def _full_parent_setup(
    app, teacher_client, client, student_username, first="Jane", last="Smith"
):
    """Register a student, generate an invite, and complete parent registration."""
    student_id = _register_student(app, student_username)
    code = _get_invite_code(app, teacher_client, student_id)
    client.post("/parent/join", data={"code": code})
    _register_parent(client, first=first, last=last)
    return student_id


# ---------------------------------------------------------------------------
# invite code generation
# ---------------------------------------------------------------------------


def test_teacher_can_generate_invite_code(app, teacher_client):
    student_id = _register_student(app)
    teacher_client.post(f"/parent/invite/{student_id}")
    with app.app_context():
        from app.models import get_db

        row = (
            get_db()
            .execute(
                "SELECT * FROM parent_invite_codes WHERE student_id = ?", (student_id,)
            )
            .fetchone()
        )
    assert row is not None
    assert row["claimed_at"] is None


def test_generate_code_reuses_existing_unclaimed(app, teacher_client):
    student_id = _register_student(app, "student_reuse")
    teacher_client.post(f"/parent/invite/{student_id}")
    teacher_client.post(f"/parent/invite/{student_id}")
    with app.app_context():
        from app.models import get_db

        count = (
            get_db()
            .execute(
                "SELECT COUNT(*) FROM parent_invite_codes WHERE student_id = ?",
                (student_id,),
            )
            .fetchone()[0]
        )
    assert count == 1


def test_student_cannot_generate_invite_code(app, student_client):
    student_id = _register_student(app, "student_blocked")
    res = student_client.post(f"/parent/invite/{student_id}")
    assert res.status_code == 403


def test_anonymous_cannot_generate_invite_code(app, client):
    student_id = _register_student(app, "student_anon")
    res = client.post(f"/parent/invite/{student_id}", follow_redirects=False)
    assert res.status_code in (302, 403)


def test_generate_code_for_nonexistent_student(app, teacher_client):
    res = teacher_client.post("/parent/invite/99999", follow_redirects=False)
    assert res.status_code == 302


def test_code_generation_blocked_for_non_student(app, teacher_client):
    with app.app_context():
        from app.models import get_db

        teacher = (
            get_db()
            .execute("SELECT id FROM users WHERE username = 'teacher1'")
            .fetchone()
        )
    res = teacher_client.post(f"/parent/invite/{teacher['id']}", follow_redirects=False)
    assert res.status_code == 302
    with app.app_context():
        from app.models import get_db

        row = (
            get_db()
            .execute(
                "SELECT * FROM parent_invite_codes WHERE student_id = ?",
                (teacher["id"],),
            )
            .fetchone()
        )
    assert row is None


# ---------------------------------------------------------------------------
# join flow
# ---------------------------------------------------------------------------


def test_join_get_renders(client):
    res = client.get("/parent/join")
    assert res.status_code == 200
    assert b"Invite Code" in res.data


def test_join_invalid_code(client):
    res = client.post(
        "/parent/join", data={"code": "badcode123"}, follow_redirects=True
    )
    assert res.status_code == 200
    assert b"Invalid invite code" in res.data


def test_join_empty_code(client):
    res = client.post("/parent/join", data={"code": ""}, follow_redirects=True)
    assert res.status_code == 200
    assert b"enter an invite code" in res.data.lower()


def test_join_valid_code_redirects_to_register(app, teacher_client, client):
    student_id = _register_student(app, "student_join")
    code = _get_invite_code(app, teacher_client, student_id)
    res = client.post("/parent/join", data={"code": code}, follow_redirects=False)
    assert res.status_code == 302
    assert "register" in res.headers["Location"]


def test_join_already_claimed_code(app, teacher_client, client):
    student_id = _register_student(app, "student_claimed")
    code = _get_invite_code(app, teacher_client, student_id)
    client.post("/parent/join", data={"code": code})
    _register_parent(client)
    c2 = app.test_client()
    res = c2.post("/parent/join", data={"code": code})
    assert b"already been used" in res.data


# ---------------------------------------------------------------------------
# register flow
# ---------------------------------------------------------------------------


def test_register_without_code_in_session_redirects(client):
    res = client.get("/parent/register", follow_redirects=False)
    assert res.status_code == 302
    assert "join" in res.headers["Location"]


def test_register_missing_fields(app, teacher_client, client):
    student_id = _register_student(app, "student_missingfields")
    code = _get_invite_code(app, teacher_client, student_id)
    client.post("/parent/join", data={"code": code})
    res = client.post(
        "/parent/register",
        data={"first_name": "", "last_name": "", "password": ""},
        follow_redirects=True,
    )
    assert b"required" in res.data


def test_register_short_password(app, teacher_client, client):
    student_id = _register_student(app, "student_shortpw")
    code = _get_invite_code(app, teacher_client, student_id)
    client.post("/parent/join", data={"code": code})
    res = client.post(
        "/parent/register",
        data={"first_name": "Jane", "last_name": "Smith", "password": "abc"},
        follow_redirects=True,
    )
    assert b"8 characters" in res.data


def test_register_success_creates_parent_user(app, teacher_client, client):
    _full_parent_setup(app, teacher_client, client, "student_success")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT * FROM users WHERE username LIKE 'parent.jane.smith%'")
            .fetchone()
        )
    assert user is not None
    assert user["role"] == "parent"


def test_register_success_links_parent_to_student(app, teacher_client, client):
    student_id = _full_parent_setup(
        app, teacher_client, client, "student_link", last="Doe"
    )
    with app.app_context():
        from app.models import get_db

        link = (
            get_db()
            .execute("SELECT * FROM parent_student WHERE student_id = ?", (student_id,))
            .fetchone()
        )
    assert link is not None


def test_register_marks_code_claimed(app, teacher_client, client):
    student_id = _register_student(app, "student_markclaimed")
    code = _get_invite_code(app, teacher_client, student_id)
    client.post("/parent/join", data={"code": code})
    _register_parent(client, last="Doe")
    with app.app_context():
        from app.models import get_db

        row = (
            get_db()
            .execute("SELECT * FROM parent_invite_codes WHERE code = ?", (code,))
            .fetchone()
        )
    assert row["claimed_at"] is not None


def test_register_sets_display_name(app, teacher_client, client):
    _full_parent_setup(app, teacher_client, client, "student_displayname", last="Doe")
    with app.app_context():
        from app.models import get_db

        user = (
            get_db()
            .execute("SELECT * FROM users WHERE username LIKE 'parent.jane.doe%'")
            .fetchone()
        )
    assert user["display_name"] == "Jane Doe"


def test_duplicate_username_gets_suffix(app, teacher_client):
    student1 = _register_student(app, "student_dup1")
    student2 = _register_student(app, "student_dup2")
    code1 = _get_invite_code(app, teacher_client, student1)
    code2 = _get_invite_code(app, teacher_client, student2)

    c1 = app.test_client()
    c1.post("/parent/join", data={"code": code1})
    _register_parent(c1, last="Doe")

    c2 = app.test_client()
    c2.post("/parent/join", data={"code": code2})
    _register_parent(c2, last="Doe")

    with app.app_context():
        from app.models import get_db

        rows = (
            get_db()
            .execute(
                "SELECT username FROM users WHERE username LIKE 'parent.jane.doe%'"
            )
            .fetchall()
        )
    usernames = [r["username"] for r in rows]
    assert len(usernames) == 2
    assert "parent.jane.doe" in usernames
    assert "parent.jane.doe1" in usernames


# ---------------------------------------------------------------------------
# dashboard
# ---------------------------------------------------------------------------


def test_dashboard_requires_parent_role(client):
    res = client.get("/parent/dashboard", follow_redirects=False)
    assert res.status_code == 302


def test_student_cannot_access_dashboard(student_client):
    res = student_client.get("/parent/dashboard")
    assert res.status_code == 403


def test_teacher_cannot_access_dashboard(teacher_client):
    res = teacher_client.get("/parent/dashboard")
    assert res.status_code == 403


def test_parent_dashboard_loads(app, teacher_client, client):
    _full_parent_setup(app, teacher_client, client, "student_dash", last="Dash")
    res = client.get("/parent/dashboard")
    assert res.status_code == 200
    assert b"Family Dashboard" in res.data


def test_parent_dashboard_shows_linked_student(app, teacher_client, client):
    _full_parent_setup(app, teacher_client, client, "student_visible", last="Visible")
    res = client.get("/parent/dashboard")
    assert b"student_visible" in res.data


def test_parent_cannot_see_other_students(app, teacher_client, client):
    student1 = _register_student(app, "student_mine")
    _register_student(app, "student_notmine")  # exists in DB but unlinked
    code = _get_invite_code(app, teacher_client, student1)
    client.post("/parent/join", data={"code": code})
    _register_parent(client, last="Mine")
    res = client.get("/parent/dashboard")
    assert b"student_mine" in res.data  # positive assertion: can see their child
    assert b"student_notmine" not in res.data


def test_dashboard_empty_state_renders(app, teacher_client, client):
    _full_parent_setup(app, teacher_client, client, "student_empty", last="Empty")
    res = client.get("/parent/dashboard")
    assert res.status_code == 200
    assert b"No posts yet" in res.data
    assert b"No announcements yet" in res.data


def test_dashboard_shows_student_posts(app, teacher_client, client):
    student_id = _full_parent_setup(
        app, teacher_client, client, "student_withposts", last="Posts"
    )
    with app.app_context():
        from app.models.post import create_post

        create_post(
            user_id=student_id,
            title="My Science Post",
            body="About plants",
            classroom_id=None,
        )
    res = client.get("/parent/dashboard")
    assert b"My Science Post" in res.data


def test_dashboard_does_not_show_hidden_posts(app, teacher_client, client):
    student_id = _full_parent_setup(
        app, teacher_client, client, "student_hiddenposts", last="Hidden"
    )
    with app.app_context():
        from app.models.post import create_post
        from app.models import get_db

        post_id = create_post(
            user_id=student_id,
            title="Hidden Post",
            body="Should not show",
            classroom_id=None,
        )
        get_db().execute("UPDATE posts SET is_hidden = 1 WHERE id = ?", (post_id,))
        get_db().commit()
    res = client.get("/parent/dashboard")
    assert b"Hidden Post" not in res.data


def test_parent_dashboard_shows_multiple_children(app, teacher_client, client):
    student1 = _register_student(app, "student_childA")
    student2 = _register_student(app, "student_childB")
    code1 = _get_invite_code(app, teacher_client, student1)
    code2 = _get_invite_code(app, teacher_client, student2)

    client.post("/parent/join", data={"code": code1})
    _register_parent(client, last="Two")

    with app.app_context():
        from app.models import get_db
        from app.models.parent import claim_invite_code

        parent = (
            get_db()
            .execute("SELECT id FROM users WHERE username LIKE 'parent.jane.two%'")
            .fetchone()
        )
        claim_invite_code(code2, parent["id"])

    res = client.get("/parent/dashboard")
    assert b"student_childA" in res.data
    assert b"student_childB" in res.data


# ---------------------------------------------------------------------------
# multi-child / multi-parent
# ---------------------------------------------------------------------------


def test_parent_can_link_multiple_students(app, teacher_client, client):
    student1 = _register_student(app, "student_multi1")
    student2 = _register_student(app, "student_multi2")
    code1 = _get_invite_code(app, teacher_client, student1)
    code2 = _get_invite_code(app, teacher_client, student2)

    client.post("/parent/join", data={"code": code1})
    _register_parent(client, last="Multi")

    with app.app_context():
        from app.models import get_db
        from app.models.parent import claim_invite_code

        parent = (
            get_db()
            .execute("SELECT id FROM users WHERE username LIKE 'parent.jane.multi%'")
            .fetchone()
        )
        result = claim_invite_code(code2, parent["id"])
    assert result == student2


def test_multiple_parents_can_link_to_same_student(app, teacher_client, db):
    student_id = _register_student(app, "student_twoparents")
    code_a = _get_invite_code(app, teacher_client, student_id)

    c_a = app.test_client()
    c_a.post("/parent/join", data={"code": code_a})
    _register_parent(c_a, last="Alpha")

    teacher_client.post(f"/parent/invite/{student_id}")
    code_b = db.execute(
        "SELECT code FROM parent_invite_codes WHERE student_id = ? AND claimed_at IS NULL",
        (student_id,),
    ).fetchone()["code"]

    c_b = app.test_client()
    c_b.post("/parent/join", data={"code": code_b})
    _register_parent(c_b, last="Beta")

    with app.app_context():
        from app.models.parent import get_parents_for_student

        parents = get_parents_for_student(student_id)
    assert len(parents) == 2


# ---------------------------------------------------------------------------
# model functions
# ---------------------------------------------------------------------------


def test_is_parent_of_true(app, teacher_client):
    student_id = _register_student(app, "student_isparent")
    with app.app_context():
        from app.models.parent import (
            generate_parent_invite_code,
            claim_invite_code,
            is_parent_of,
        )
        from app.models.user import create_user, get_user_by_username

        create_user(
            username="parent_check",
            password="pass1234",
            role="parent",
            bio="",
            dob="1980-01-01",
        )
        parent = get_user_by_username("parent_check")
        code = generate_parent_invite_code(student_id, parent["id"])
        claim_invite_code(code, parent["id"])
        assert is_parent_of(parent["id"], student_id) is True


def test_is_parent_of_false(app):
    student_id = _register_student(app, "student_notparent")
    with app.app_context():
        from app.models.parent import is_parent_of
        from app.models.user import create_user, get_user_by_username

        create_user(
            username="parent_notlinked",
            password="pass1234",
            role="parent",
            bio="",
            dob="1980-01-01",
        )
        parent = get_user_by_username("parent_notlinked")
        assert is_parent_of(parent["id"], student_id) is False


def test_get_parents_for_student_empty(app):
    student_id = _register_student(app, "student_noparents")
    with app.app_context():
        from app.models.parent import get_parents_for_student

        parents = get_parents_for_student(student_id)
    assert len(parents) == 0


# ---------------------------------------------------------------------------
# route access restrictions
# ---------------------------------------------------------------------------


def test_parent_cannot_access_feed(app, teacher_client, client):
    _full_parent_setup(app, teacher_client, client, "student_feedblock", last="Feed")
    res = client.get("/", follow_redirects=True)
    assert b"Family Dashboard" in res.data or res.status_code in (302, 403)


def test_parent_cannot_access_classrooms(app, teacher_client, client):
    _full_parent_setup(app, teacher_client, client, "student_classblock", last="Class")
    res = client.get("/classrooms/", follow_redirects=True)
    assert b"Family Dashboard" in res.data or res.status_code == 403


def test_parent_cannot_create_post(app, teacher_client, client):
    _full_parent_setup(app, teacher_client, client, "student_postblock", last="Post")
    client.post(
        "/posts/new",
        data={"title": "Parent post", "body": "Should not work"},
        follow_redirects=True,
    )
    with app.app_context():
        from app.models import get_db

        row = (
            get_db()
            .execute("SELECT * FROM posts WHERE title = 'Parent post'")
            .fetchone()
        )
    assert row is None


def test_parent_cannot_submit_bug_report(app, teacher_client, client):
    _full_parent_setup(app, teacher_client, client, "student_bugblock", last="Bug")
    client.post(
        "/bug-reports/submit",
        data={
            "title": "Parent bug",
            "description": "Should not work",
            "severity": "low",
        },
        follow_redirects=True,
    )
    with app.app_context():
        from app.models import get_db

        row = (
            get_db()
            .execute("SELECT * FROM bug_reports WHERE title = 'Parent bug'")
            .fetchone()
        )
    assert row is None
