# tests/test_provisioning.py
import io
import csv


def _make_csv(rows):
    """Helper to build a CSV file-like object from a list of dicts."""
    output = io.StringIO()
    writer = csv.DictWriter(
        output, fieldnames=["first_name", "last_name", "dob", "join_codes"]
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    output.seek(0)
    return (io.BytesIO(output.read().encode()), "students.csv")


# --- username generation


def test_generate_username_basic(app):
    with app.app_context():
        from app.models.classroom import generate_username

        username = generate_username("Jane", "Smith")
        assert username == "jane.smith"


def test_generate_username_collision(app, teacher_client):
    with app.app_context():
        from app.models.classroom import generate_username, provision_student

        provision_student("Jane", "Smith", "2010-01-01")
        username = generate_username("Jane", "Smith")
        assert username == "jane.smith2"


def test_generate_username_non_ascii(app):
    with app.app_context():
        from app.models.classroom import generate_username

        username = generate_username("José", "García")
        assert username == "jose.garcia"


def test_generate_username_multiple_collisions(app):
    with app.app_context():
        from app.models.classroom import generate_username, provision_student

        provision_student("Jane", "Smith", "2010-01-01")
        provision_student("Jane", "Smith", "2010-01-01")
        username = generate_username("Jane", "Smith")
        assert username == "jane.smith3"


# --- password generation


def test_generate_password_format(app):
    with app.app_context():
        from app.models.classroom import generate_password

        password = generate_password()
        # should end with two digits
        assert password[-2:].isdigit()
        # should be all lowercase + digits
        assert password.replace(" ", "").islower() or password[-2:].isdigit()


def test_generate_password_length(app):
    with app.app_context():
        from app.models.classroom import generate_password

        password = generate_password()
        assert len(password) >= 12


def test_generate_password_unique(app):
    with app.app_context():
        from app.models.classroom import generate_password

        passwords = {generate_password() for _ in range(20)}
        assert len(passwords) > 1


# --- provision_student


def test_provision_student_creates_account(teacher_client):
    from app.models.classroom import provision_student
    from app.models.user import get_user_by_username

    provision_student("Alice", "Jones", "2010-06-15")
    user = get_user_by_username("alice.jones")
    assert user is not None
    assert user["role"] == "student"


def test_provision_student_coppa_approved(teacher_client):
    from app.models.classroom import provision_student
    from app.models.user import get_user_by_username

    # under-13 student provisioned by teacher should be approved
    provision_student("Young", "Kid", "2015-01-01")
    user = get_user_by_username("young.kid")
    assert user["coppa_status"] == "approved"


def test_provision_student_provisional_flag(teacher_client):

    from app.models.classroom import provision_student
    from app.models.user import get_user_by_username

    provision_student("Bob", "Brown", "2010-01-01")
    user = get_user_by_username("bob.brown")
    assert user["provisional"] == 1


def test_provision_student_returns_credentials(teacher_client):
    from app.models.classroom import provision_student

    result = provision_student("Carol", "White", "2010-01-01")
    assert result["username"] == "carol.white"
    assert result["password"]
    assert result["first_name"] == "Carol"
    assert result["last_name"] == "White"


def test_provision_student_with_valid_join_code(teacher_client, classroom):
    from app.models.classroom import (
        provision_student,
        get_classroom,
        get_member_role,
    )

    c = get_classroom(classroom)
    result = provision_student("Dave", "Green", "2010-01-01", [c["join_code"]])
    assert c["name"] in result["classrooms"]
    from app.models.user import get_user_by_username

    user = get_user_by_username("dave.green")
    role = get_member_role(classroom, user["id"])
    assert role == "student"


def test_provision_student_with_invalid_join_code(teacher_client):
    from app.models.classroom import provision_student

    result = provision_student("Eve", "Black", "2010-01-01", ["XXXXXX"])
    assert "XXXXXX" in result["invalid_codes"]
    assert result["classrooms"] == []


def test_provision_student_no_join_code(teacher_client):
    from app.models.classroom import provision_student

    result = provision_student("Frank", "Gray", "2010-01-01")
    assert result["classrooms"] == []
    assert result["invalid_codes"] == []


def test_provision_student_invalid_dob(teacher_client):
    from app.models.classroom import provision_student
    import pytest

    with pytest.raises(ValueError):
        provision_student("Bad", "Date", "not-a-date")


def test_provision_student_multiple_join_codes(teacher_client, classroom):
    from app.models.classroom import (
        provision_student,
        get_classroom,
        create_classroom,
    )

    c1 = get_classroom(classroom)
    c2_id = create_classroom(1, "Second Class", "")
    c2 = get_classroom(c2_id)
    result = provision_student(
        "Multi", "Class", "2010-01-01", [c1["join_code"], c2["join_code"]]
    )
    assert len(result["classrooms"]) == 2


# --- provision_students_bulk


def test_bulk_provision_basic(teacher_client):
    from app.models.classroom import provision_students_bulk

    rows = [
        {
            "first_name": "Ann",
            "last_name": "Lee",
            "dob": "2010-01-01",
            "join_codes": "",
        },
        {
            "first_name": "Ben",
            "last_name": "Kim",
            "dob": "2011-03-15",
            "join_codes": "",
        },
    ]
    students, skipped = provision_students_bulk(rows)
    assert len(students) == 2
    assert len(skipped) == 0


def test_bulk_provision_skips_missing_name(teacher_client):
    from app.models.classroom import provision_students_bulk

    rows = [
        {
            "first_name": "",
            "last_name": "Lee",
            "dob": "2010-01-01",
            "join_codes": "",
        },
    ]
    students, skipped = provision_students_bulk(rows)
    assert len(students) == 0
    assert len(skipped) == 1


def test_bulk_provision_skips_missing_dob(teacher_client):
    from app.models.classroom import provision_students_bulk

    rows = [
        {"first_name": "Ann", "last_name": "Lee", "dob": "", "join_codes": ""},
    ]
    students, skipped = provision_students_bulk(rows)
    assert len(students) == 0
    assert len(skipped) == 1


def test_bulk_provision_skips_invalid_dob(teacher_client):
    from app.models.classroom import provision_students_bulk

    rows = [
        {
            "first_name": "Ann",
            "last_name": "Lee",
            "dob": "not-a-date",
            "join_codes": "",
        },
    ]
    students, skipped = provision_students_bulk(rows)
    assert len(students) == 0
    assert len(skipped) == 1


def test_bulk_provision_partial_success(teacher_client):
    from app.models.classroom import provision_students_bulk

    rows = [
        {
            "first_name": "Ann",
            "last_name": "Lee",
            "dob": "2010-01-01",
            "join_codes": "",
        },
        {
            "first_name": "",
            "last_name": "Bad",
            "dob": "2010-01-01",
            "join_codes": "",
        },
    ]
    students, skipped = provision_students_bulk(rows)
    assert len(students) == 1
    assert len(skipped) == 1


def test_bulk_provision_notes_invalid_join_code(teacher_client):
    from app.models.classroom import provision_students_bulk

    rows = [
        {
            "first_name": "Ann",
            "last_name": "Lee",
            "dob": "2010-01-01",
            "join_codes": "XXXXXX",
        },
    ]
    students, skipped = provision_students_bulk(rows)
    assert len(students) == 1  # account still created
    assert any("XXXXXX" in s for s in skipped)


# --- provision route


def test_provision_page_loads(teacher_client):
    response = teacher_client.get("/classrooms/provision")
    assert response.status_code == 200
    assert b"Add Students" in response.data


def test_provision_page_requires_teacher(student_client):
    response = student_client.get("/classrooms/provision")
    assert response.status_code == 403


def test_provision_page_requires_login(client):
    response = client.get("/classrooms/provision")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_provision_prefills_join_code(teacher_client):
    response = teacher_client.get("/classrooms/provision?join_code=ABC123")
    assert b"ABC123" in response.data


def test_manual_provision_redirects_to_credentials(teacher_client):
    response = teacher_client.post(
        "/classrooms/provision",
        data={
            "method": "manual",
            "first_name": "Jane",
            "last_name": "Smith",
            "dob": "2010-01-01",
            "join_codes": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "credentials" in response.headers["Location"]


def test_manual_provision_missing_fields(teacher_client):
    response = teacher_client.post(
        "/classrooms/provision",
        data={
            "method": "manual",
            "first_name": "",
            "last_name": "",
            "dob": "",
            "join_codes": "",
        },
        follow_redirects=True,
    )
    assert b"required" in response.data


def test_csv_provision_valid(teacher_client):
    csv_data, filename = _make_csv(
        [
            {
                "first_name": "Ann",
                "last_name": "Lee",
                "dob": "2010-01-01",
                "join_codes": "",
            },
            {
                "first_name": "Ben",
                "last_name": "Kim",
                "dob": "2011-03-15",
                "join_codes": "",
            },
        ]
    )
    response = teacher_client.post(
        "/classrooms/provision",
        data={"method": "csv", "csv_file": (csv_data, filename)},
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "credentials" in response.headers["Location"]


def test_csv_provision_missing_columns(teacher_client):
    output = io.BytesIO(b"name,age\nJane,10\n")
    response = teacher_client.post(
        "/classrooms/provision",
        data={"method": "csv", "csv_file": (output, "bad.csv")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"columns" in response.data


def test_csv_provision_wrong_extension(teacher_client):
    response = teacher_client.post(
        "/classrooms/provision",
        data={"method": "csv", "csv_file": (io.BytesIO(b"data"), "students.txt")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"valid .csv" in response.data


# --- credentials route


def test_credentials_page_loads_after_provision(teacher_client):
    with teacher_client.session_transaction() as sess:
        sess["provisioned_students"] = [
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "username": "jane.smith",
                "password": "sunnybird42",
                "dob": "2010-01-01",
                "classrooms": [],
                "invalid_codes": [],
            }
        ]
        sess["provisioned_skipped"] = []
    response = teacher_client.get("/classrooms/provision/credentials")
    assert response.status_code == 200
    assert b"jane.smith" in response.data


def test_credentials_page_without_session(teacher_client):
    response = teacher_client.get(
        "/classrooms/provision/credentials-csv",
        follow_redirects=True,
    )
    assert b"No provisioning data" in response.data


def test_credentials_shows_password(teacher_client):
    with teacher_client.session_transaction() as sess:
        sess["provisioned_students"] = [
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "username": "jane.smith",
                "password": "sunnybird42",
                "dob": "2010-01-01",
                "classrooms": [],
                "invalid_codes": [],
            }
        ]
        sess["provisioned_skipped"] = []

    response = teacher_client.get("/classrooms/provision/credentials")
    assert b"jane.smith" in response.data
    assert b"Print" in response.data
    assert b"Download CSV" in response.data


# --- credentials CSV download


def test_credentials_csv_download(teacher_client):
    with teacher_client.session_transaction() as sess:
        sess["provisioned_students"] = [
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "username": "jane.smith",
                "password": "sunnybird42",
                "dob": "2010-01-01",
                "classrooms": [],
                "invalid_codes": [],
            }
        ]
        sess["provisioned_skipped"] = []
    response = teacher_client.get("/classrooms/provision/credentials-csv")
    assert response.status_code == 200
    assert response.content_type == "text/csv; charset=utf-8"
    assert b"jane.smith" in response.data


def test_credentials_csv_without_session(teacher_client):
    response = teacher_client.get(
        "/classrooms/provision/credentials-csv",
        follow_redirects=True,
    )
    assert b"No provisioning data" in response.data


# --- template CSV download


def test_template_csv_download(teacher_client):
    response = teacher_client.get("/classrooms/provision/template.csv")
    assert response.status_code == 200
    assert response.content_type == "text/csv; charset=utf-8"
    assert b"first_name" in response.data
    assert b"last_name" in response.data
    assert b"dob" in response.data
    assert b"join_codes" in response.data
