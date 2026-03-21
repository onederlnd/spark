# tests/test_xss.py


def test_xss_in_classroom_name(teacher_client):
    response = teacher_client.post(
        "/classrooms/new",
        data={"name": '<script>alert("xss")</script>', "description": ""},
        follow_redirects=True,
    )
    assert b"<script>alert" not in response.data


def test_xss_in_classroom_description(teacher_client):
    response = teacher_client.post(
        "/classrooms/new",
        data={"name": "Safe Name", "description": '<script>alert("xss")</script>'},
        follow_redirects=True,
    )
    assert b"<script>alert" not in response.data


def test_xss_in_assignment_title(teacher_client, classroom):
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/new",
        data={
            "title": '<script>alert("xss")</script>',
            "instructions": "Do the thing",
            "due_date": "",
        },
        follow_redirects=True,
    )
    assert b"<script>alert" not in response.data


def test_xss_in_assignment_instructions(teacher_client, classroom):
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/new",
        data={
            "title": "Safe Title",
            "instructions": '<script>alert("xss")</script>',
            "due_date": "",
        },
        follow_redirects=True,
    )
    assert b"<script>alert" not in response.data


def test_xss_in_submission_body(teacher_client, student_client, classroom, assignment):
    import re

    response = teacher_client.get(f"/classrooms/{classroom}")
    join_code = re.search(
        r'data-join-code="([A-Z0-9]{6})"', response.data.decode()
    ).group(1)
    student_client.post("/classrooms/join", data={"join_code": join_code})

    response = student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": '<script>alert("xss")</script>'},
        follow_redirects=True,
    )
    assert b"<script>alert" not in response.data


def test_xss_in_grade_feedback(teacher_client, student_client, classroom, assignment):
    import re

    response = teacher_client.get(f"/classrooms/{classroom}")
    join_code = re.search(
        r'data-join-code="([A-Z0-9]{6})"', response.data.decode()
    ).group(1)
    student_client.post("/classrooms/join", data={"join_code": join_code})
    student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "My answer"},
    )

    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/grade/2",
        data={"grade": "A", "feedback": '<script>alert("xss")</script>'},
        follow_redirects=True,
    )
    assert b"<script>alert" not in response.data


def test_xss_in_filter_word(teacher_client):
    response = teacher_client.post(
        "/classrooms/filter/words",
        data={"action": "add", "word": '<script>alert("xss")</script>'},
        follow_redirects=True,
    )
    assert b"<script>alert" not in response.data


def test_xss_in_username_registration(client):
    response = client.post(
        "/auth/register",
        data={
            "username": '<script>alert("xss")</script>',
            "password": "pass123",
            "bio": "",
            "dob": "2008-01-01",
        },
        follow_redirects=True,
    )
    assert b"<script>alert" not in response.data
