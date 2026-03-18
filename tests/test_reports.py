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
    response = teacher_client.get(f"/moderation/reports?classroom_id={classroom}")

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
