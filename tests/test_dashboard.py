# tests/test_dashboard.py
import re


def _get_join_code(teacher_client, classroom_id):
    response = teacher_client.get(f"/classrooms/{classroom_id}")
    # The join code sits in a div with letter-spacing style in the sidebar
    match = re.search(r'data-join-code="([A-Z0-9]{6})"', response.data.decode())
    return match.group(1).strip() if match else None


def _join_and_submit(
    teacher_client, student_client, classroom, assignment, body="My answer"
):
    join_code = _get_join_code(teacher_client, classroom)
    student_client.post("/classrooms/join", data={"join_code": join_code})
    student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": body},
    )


def test_teacher_dashboard_loads(teacher_client):
    response = teacher_client.get("/classrooms/")
    assert response.status_code == 200


def test_student_dashboard_loads(student_client):
    response = student_client.get("/classrooms/")
    assert response.status_code == 200


def test_teacher_sees_new_classroom_button(teacher_client):
    response = teacher_client.get("/classrooms/")
    assert b"New Classroom" in response.data


def test_student_sees_join_form(student_client):
    response = student_client.get("/classrooms/")
    assert b"join_code" in response.data


def test_teacher_does_not_see_join_form(teacher_client):
    response = teacher_client.get("/classrooms/")
    assert b"join_code" not in response.data


def test_student_does_not_see_new_classroom_button(student_client):
    response = student_client.get("/classrooms/")
    assert b"New Classroom" not in response.data


def test_classroom_appears_on_dashboard(teacher_client, classroom):
    response = teacher_client.get("/classrooms/")
    assert b"Test Classroom" in response.data


def test_student_sees_classroom_after_joining(
    teacher_client, student_client, classroom
):
    join_code = _get_join_code(teacher_client, classroom)
    student_client.post("/classrooms/join", data={"join_code": join_code})

    response = student_client.get("/classrooms/")
    assert b"Test Classroom" in response.data


def test_empty_state_shown_when_no_classrooms(teacher_client):
    response = teacher_client.get("/classrooms/")
    assert b"No classrooms yet" in response.data


def test_student_empty_state(student_client):
    response = student_client.get("/classrooms/")
    assert b"haven't joined any classrooms" in response.data


def test_no_pending_grades_badge_when_no_submissions(
    teacher_client, classroom, assignment
):
    response = teacher_client.get("/classrooms/")
    assert b"to grade" not in response.data


def test_pending_grades_badge_appears_after_submission(
    teacher_client, student_client, classroom, assignment
):
    _join_and_submit(teacher_client, student_client, classroom, assignment)
    response = teacher_client.get("/classrooms/")
    assert b"to grade" in response.data


def test_pending_grades_count_is_correct(
    teacher_client, student_client, classroom, assignment
):
    _join_and_submit(teacher_client, student_client, classroom, assignment)
    response = teacher_client.get("/classrooms/")
    assert b"1 to grade" in response.data


def test_pending_grades_clears_after_grading(
    teacher_client, student_client, classroom, assignment
):
    _join_and_submit(teacher_client, student_client, classroom, assignment)

    # student user_id is 2
    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/grade/2",
        data={"grade": "A", "feedback": ""},
    )

    response = teacher_client.get("/classrooms/")
    assert b"to grade" not in response.data


def test_pending_grades_summary_card_appears(
    teacher_client, student_client, classroom, assignment
):
    _join_and_submit(teacher_client, student_client, classroom, assignment)
    response = teacher_client.get("/classrooms/")
    assert b"Pending Grades" in response.data


def test_pending_grades_summary_card_absent_when_clean(
    teacher_client, classroom, assignment
):
    response = teacher_client.get("/classrooms/")
    assert b"Pending Grades" not in response.data


def test_student_never_sees_pending_grades(
    teacher_client, student_client, classroom, assignment
):
    _join_and_submit(teacher_client, student_client, classroom, assignment)
    response = student_client.get("/classrooms/")
    assert b"Pending Grades" not in response.data
    assert b"to grade" not in response.data
