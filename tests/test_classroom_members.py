# tests/test_classroom_members.py


def _join_classroom(app, username, password, join_code):
    """Helper: register, login, and join a classroom. Returns the client."""
    client = app.test_client()
    client.post(
        "/auth/register",
        data={"username": username, "password": password, "dob": "2005-06-01"},
    )
    client.post("/auth/login", data={"username": username, "password": password})
    client.post("/classrooms/join", data={"join_code": join_code})
    return client


def _get_join_code(app, classroom_id):
    from app.models.classroom import get_classroom

    with app.app_context():
        return get_classroom(classroom_id)["join_code"]


# --- student appears in sidebar member list


def test_joined_student_appears_in_sidebar(app, teacher_client, classroom):
    join_code = _get_join_code(app, classroom)
    _join_classroom(app, "sidebar_student", "pass123", join_code)

    response = teacher_client.get(f"/classrooms/{classroom}/")
    assert b"sidebar_student" in response.data


def test_multiple_students_appear_in_sidebar(app, teacher_client, classroom):
    join_code = _get_join_code(app, classroom)
    _join_classroom(app, "student_a", "pass123", join_code)
    _join_classroom(app, "student_b", "pass123", join_code)

    response = teacher_client.get(f"/classrooms/{classroom}/")
    assert b"student_a" in response.data
    assert b"student_b" in response.data


def test_member_count_updates_after_join(app, teacher_client, classroom):
    join_code = _get_join_code(app, classroom)
    _join_classroom(app, "count_student", "pass123", join_code)

    response = teacher_client.get(f"/classrooms/{classroom}/")
    # sidebar shows "Members (N)" — should be at least 2 (teacher + student)
    assert b"Members (2)" in response.data


# --- student appears in teacher's students card


def test_joined_student_appears_in_students_card(app, teacher_client, classroom):
    join_code = _get_join_code(app, classroom)
    _join_classroom(app, "card_student", "pass123", join_code)

    response = teacher_client.get(f"/classrooms/{classroom}/")
    assert b"card_student" in response.data
    assert b"Students (1)" in response.data


def test_students_card_shows_correct_count(app, teacher_client, classroom):
    join_code = _get_join_code(app, classroom)
    _join_classroom(app, "s1", "pass123", join_code)
    _join_classroom(app, "s2", "pass123", join_code)
    _join_classroom(app, "s3", "pass123", join_code)

    response = teacher_client.get(f"/classrooms/{classroom}/")
    assert b"Students (3)" in response.data


def test_teacher_not_counted_as_student(app, teacher_client, classroom):
    """Teacher should appear in sidebar members but not in the students card."""
    response = teacher_client.get(f"/classrooms/{classroom}/")
    # no students joined — students card should show 0
    assert b"Students (0)" in response.data


def test_students_card_hidden_from_students(app, teacher_client, classroom):
    """Students card (with QR/regenerate controls) is only shown to teachers."""
    join_code = _get_join_code(app, classroom)
    student = _join_classroom(app, "view_student", "pass123", join_code)

    response = student.get(f"/classrooms/{classroom}/")
    assert b"Regenerate QR" not in response.data


# --- provisional students


def test_provisional_student_shows_provisioned_label(app, teacher_client, classroom):
    from app.models.classroom import provision_student, get_classroom

    with app.app_context():
        c = get_classroom(classroom)
        provision_student("Prov", "Student", "2012-01-01", [c["join_code"]])

    response = teacher_client.get(f"/classrooms/{classroom}/")
    assert b"prov.student" in response.data
    assert b"provisioned" in response.data


def test_provisional_student_shows_regenerate_qr_button(app, teacher_client, classroom):
    from app.models.classroom import provision_student, get_classroom

    with app.app_context():
        c = get_classroom(classroom)
        provision_student("Qr", "Student", "2012-01-01", [c["join_code"]])

    response = teacher_client.get(f"/classrooms/{classroom}/")
    assert b"Regenerate QR" in response.data


def test_non_provisional_student_has_no_regenerate_button(
    app, teacher_client, classroom
):
    join_code = _get_join_code(app, classroom)
    _join_classroom(app, "regular_student", "pass123", join_code)

    response = teacher_client.get(f"/classrooms/{classroom}/")
    assert b"regular_student" in response.data
    assert b"Regenerate QR" not in response.data


# --- empty state


def test_no_students_shows_empty_message(teacher_client, classroom):
    response = teacher_client.get(f"/classrooms/{classroom}/")
    assert b"No students yet" in response.data


def test_student_sees_own_username_in_sidebar(app, teacher_client, classroom):
    join_code = _get_join_code(app, classroom)
    student = _join_classroom(app, "self_student", "pass123", join_code)

    response = student.get(f"/classrooms/{classroom}/")
    assert b"self_student" in response.data
