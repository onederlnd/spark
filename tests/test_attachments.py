# tests/test_attachments.py
import io
import os
import pytest


def _make_file(
    content=b"hello world", filename="test.pdf", content_type="application/pdf"
):
    return (io.BytesIO(content), filename)


# --- model tests


def test_allowed_file_valid(app):
    with app.app_context():
        from app.models.attachments import allowed_file

        assert allowed_file("report.pdf")
        assert allowed_file("photo.jpg")
        assert allowed_file("notes.docx")
        assert allowed_file("data.xlsx")


def test_allowed_file_invalid(app):
    with app.app_context():
        from app.models.attachments import allowed_file

        assert not allowed_file("script.exe")
        assert not allowed_file("malware.sh")
        assert not allowed_file("noextension")


def test_save_file_too_large(app):
    with app.app_context():
        from app.models.attachments import save_file, MAX_FILE_SIZE

        big = io.BytesIO(b"x" * (MAX_FILE_SIZE + 1))
        big.seek(0)

        class FakeFile:
            filename = "big.pdf"

            def seek(self, *a):
                big.seek(*a)

            def tell(self):
                return big.tell()

            def save(self, path):
                pass

        with pytest.raises(ValueError, match="too large"):
            save_file(FakeFile(), "test", app)


def test_save_file_bad_extension(app):
    with app.app_context():
        from app.models.attachments import save_file

        class FakeFile:
            filename = "bad.exe"

            def seek(self, *a):
                pass

            def tell(self):
                return 100

            def save(self, path):
                pass

        with pytest.raises(ValueError, match="not allowed"):
            save_file(FakeFile(), "test", app)


def test_save_file_empty(app):
    with app.app_context():
        from app.models.attachments import save_file

        class FakeFile:
            filename = "empty.pdf"

            def seek(self, *a):
                pass

            def tell(self):
                return 0

            def save(self, path):
                pass

        with pytest.raises(ValueError, match="empty"):
            save_file(FakeFile(), "test", app)


# --- assignment attachment routes


def test_upload_assignment_attachment(teacher_client, classroom, assignment):
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/attachments",
        data={"file": _make_file(b"pdf content", "worksheet.pdf")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"worksheet.pdf" in response.data


def test_upload_assignment_attachment_wrong_type(teacher_client, classroom, assignment):
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/attachments",
        data={"file": _make_file(b"bad", "virus.exe")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"not allowed" in response.data


def test_upload_assignment_attachment_student_forbidden(
    student_client, app, classroom, assignment
):
    from app.models.classroom import get_classroom

    with app.app_context():
        c = get_classroom(classroom)
    student_client.post("/classrooms/join", data={"join_code": c["join_code"]})

    response = student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/attachments",
        data={"file": _make_file(b"pdf", "test.pdf")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 403


def test_download_assignment_attachment(
    teacher_client, student_client, app, classroom, assignment
):
    from app.models.classroom import get_classroom

    with app.app_context():
        c = get_classroom(classroom)

    # upload as teacher
    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/attachments",
        data={"file": _make_file(b"pdf content", "notes.pdf")},
        content_type="multipart/form-data",
    )

    # get attachment id
    with app.app_context():
        from app.models.attachments import get_assignment_attachments

        attachments = get_assignment_attachments(assignment)
    assert len(attachments) == 1
    attachment_id = attachments[0]["id"]

    # student joins and downloads
    student_client.post("/classrooms/join", data={"join_code": c["join_code"]})
    response = student_client.get(
        f"/classrooms/{classroom}/assignments/{assignment}/attachments/{attachment_id}/download"
    )
    assert response.status_code == 200
    assert response.data == b"pdf content"


def test_download_assignment_attachment_non_member(
    client, teacher_client, classroom, assignment
):
    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/attachments",
        data={"file": _make_file(b"pdf", "notes.pdf")},
        content_type="multipart/form-data",
    )
    with teacher_client.application.app_context():
        from app.models.attachments import get_assignment_attachments

        attachments = get_assignment_attachments(assignment)
    attachment_id = attachments[0]["id"]

    response = client.get(
        f"/classrooms/{classroom}/assignments/{assignment}/attachments/{attachment_id}/download"
    )
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_delete_assignment_attachment(teacher_client, app, classroom, assignment):
    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/attachments",
        data={"file": _make_file(b"pdf", "delete_me.pdf")},
        content_type="multipart/form-data",
    )
    with app.app_context():
        from app.models.attachments import get_assignment_attachments

        attachments = get_assignment_attachments(assignment)
    attachment_id = attachments[0]["id"]

    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/attachments/{attachment_id}/delete",
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        from app.models.attachments import get_assignment_attachments

        assert len(get_assignment_attachments(assignment)) == 0


def test_delete_assignment_attachment_student_forbidden(
    student_client, teacher_client, app, classroom, assignment
):
    from app.models.classroom import get_classroom

    with app.app_context():
        c = get_classroom(classroom)

    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/attachments",
        data={"file": _make_file(b"pdf", "test.pdf")},
        content_type="multipart/form-data",
    )
    with app.app_context():
        from app.models.attachments import get_assignment_attachments

        attachments = get_assignment_attachments(assignment)
    attachment_id = attachments[0]["id"]

    student_client.post("/classrooms/join", data={"join_code": c["join_code"]})
    response = student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/attachments/{attachment_id}/delete",
    )
    assert response.status_code == 403


# --- submission attachment routes


def _submit_assignment(student_client, classroom, assignment):
    student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}",
        data={"body": "My answer"},
    )


def test_upload_submission_attachment(student_client, app, classroom, assignment):
    from app.models.classroom import get_classroom

    with app.app_context():
        c = get_classroom(classroom)
    student_client.post("/classrooms/join", data={"join_code": c["join_code"]})
    _submit_assignment(student_client, classroom, assignment)

    response = student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/submission/attachments",
        data={"file": _make_file(b"my work", "essay.pdf")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"essay.pdf" in response.data


def test_upload_submission_attachment_teacher_forbidden(
    teacher_client, classroom, assignment
):
    response = teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/submission/attachments",
        data={"file": _make_file(b"pdf", "test.pdf")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 403


def test_download_submission_attachment_by_student(
    student_client, app, classroom, assignment
):
    from app.models.classroom import get_classroom

    with app.app_context():
        c = get_classroom(classroom)
    student_client.post("/classrooms/join", data={"join_code": c["join_code"]})
    _submit_assignment(student_client, classroom, assignment)

    student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/submission/attachments",
        data={"file": _make_file(b"essay content", "essay.pdf")},
        content_type="multipart/form-data",
    )

    with app.app_context():
        from app.models.classroom import get_submission
        from app.models.attachments import get_submission_attachments

        # need student user id — student1 is user id 2
        submission = get_submission(assignment, 2)
        attachments = get_submission_attachments(submission["id"])
    attachment_id = attachments[0]["id"]

    response = student_client.get(
        f"/classrooms/{classroom}/assignments/{assignment}/submission/attachments/{attachment_id}/download"
    )
    assert response.status_code == 200
    assert response.data == b"essay content"


def test_download_submission_attachment_by_teacher(
    teacher_client, student_client, app, classroom, assignment
):
    from app.models.classroom import get_classroom

    with app.app_context():
        c = get_classroom(classroom)
    student_client.post("/classrooms/join", data={"join_code": c["join_code"]})
    _submit_assignment(student_client, classroom, assignment)

    student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/submission/attachments",
        data={"file": _make_file(b"work", "work.pdf")},
        content_type="multipart/form-data",
    )

    with app.app_context():
        from app.models.classroom import get_submission
        from app.models.attachments import get_submission_attachments

        submission = get_submission(assignment, 2)
        attachments = get_submission_attachments(submission["id"])
    attachment_id = attachments[0]["id"]

    response = teacher_client.get(
        f"/classrooms/{classroom}/assignments/{assignment}/submission/attachments/{attachment_id}/download"
    )
    assert response.status_code == 200


def test_delete_submission_attachment(student_client, app, classroom, assignment):
    from app.models.classroom import get_classroom

    with app.app_context():
        c = get_classroom(classroom)
    student_client.post("/classrooms/join", data={"join_code": c["join_code"]})
    _submit_assignment(student_client, classroom, assignment)

    student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/submission/attachments",
        data={"file": _make_file(b"work", "delete_me.pdf")},
        content_type="multipart/form-data",
    )

    with app.app_context():
        from app.models.classroom import get_submission
        from app.models.attachments import get_submission_attachments

        submission = get_submission(assignment, 2)
        attachments = get_submission_attachments(submission["id"])
    attachment_id = attachments[0]["id"]

    response = student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/submission/attachments/{attachment_id}/delete",
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        from app.models.classroom import get_submission
        from app.models.attachments import get_submission_attachments

        submission = get_submission(assignment, 2)
        assert len(get_submission_attachments(submission["id"])) == 0


def test_student_cannot_delete_other_students_attachment(
    student_client, app, classroom, assignment
):
    """A second student cannot delete the first student's attachment."""
    from app.models.classroom import get_classroom, get_submission
    from app.models.attachments import get_submission_attachments

    with app.app_context():
        c = get_classroom(classroom)

    student_client.post("/classrooms/join", data={"join_code": c["join_code"]})
    _submit_assignment(student_client, classroom, assignment)
    student_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/submission/attachments",
        data={"file": _make_file(b"work", "mine.pdf")},
        content_type="multipart/form-data",
    )

    with app.app_context():
        submission = get_submission(assignment, 2)
        attachments = get_submission_attachments(submission["id"])
    attachment_id = attachments[0]["id"]

    # second student tries to delete
    other = app.test_client()
    other.post(
        "/auth/register",
        data={"username": "other_student", "password": "pass123", "dob": "2005-01-01"},
    )
    other.post("/auth/login", data={"username": "other_student", "password": "pass123"})
    other.post("/classrooms/join", data={"join_code": c["join_code"]})

    response = other.post(
        f"/classrooms/{classroom}/assignments/{assignment}/submission/attachments/{attachment_id}/delete",
    )
    assert response.status_code == 403


def test_attachment_not_accessible_to_non_member(
    client, teacher_client, classroom, assignment
):
    teacher_client.post(
        f"/classrooms/{classroom}/assignments/{assignment}/attachments",
        data={"file": _make_file(b"pdf", "secret.pdf")},
        content_type="multipart/form-data",
    )
    with teacher_client.application.app_context():
        from app.models.attachments import get_assignment_attachments

        attachments = get_assignment_attachments(assignment)
    attachment_id = attachments[0]["id"]

    response = client.get(
        f"/classrooms/{classroom}/assignments/{assignment}/attachments/{attachment_id}/download"
    )
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]
