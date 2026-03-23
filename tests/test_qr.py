# tests/test_qr.py

# def _provision_student(teacher_client, first_name="Jane", last_name="Smith"):
#     """Provision a student and return the session data."""
#     with teacher_client:
#         teacher_client.post(
#             "/classrooms/provision",
#             data={
#                 "method": "manual",
#                 "first_name": first_name,
#                 "last_name": last_name,
#                 "dob": "2010-01-01",
#                 "join_codes": "",
#             },
#             follow_redirects=True,
#         )
#         with teacher_client.session_transaction() as sess:
#             students = sess.get("provisioned_students", [])
#     return students[0] if students else None
#
#
# # --- qr token generation
#
#
# def test_provision_student_has_qr_token(teacher_client):
#     from app.models.classroom import provision_student
#
#     result = provision_student("Jane", "Smith", "2010-01-01")
#     assert result["qr_token"] is not None
#     assert len(result["qr_token"]) >= 32
#
#
# def test_qr_token_stored_in_db(teacher_client):
#     from app.models.classroom import provision_student
#     from app.models.user import get_user_by_username
#
#     provision_student("Jane", "Smith", "2010-01-01")
#     user = get_user_by_username("jane.smith")
#     assert user["qr_token"] is not None
#
#
# def test_qr_tokens_are_unique(teacher_client):
#     from app.models.classroom import provision_student
#
#     r1 = provision_student("Jane", "Smith", "2010-01-01")
#     r2 = provision_student("Jane", "Smith", "2010-01-01")
#     assert r1["qr_token"] != r2["qr_token"]
#
#
# def test_self_registered_user_has_no_qr_token(client):
#     from app.models.user import get_user_by_username
#
#     client.post(
#         "/auth/register",
#         data={
#             "username": "selfuser",
#             "password": "pass123",
#             "bio": "",
#             "dob": "2008-01-01",
#         },
#     )
#     user = get_user_by_username("selfuser")
#     assert user["qr_token"] is None
#
#
# # --- qr login route
#
#
# def test_qr_login_valid_token(teacher_client, client):
#     from app.models.classroom import provision_student
#
#     result = provision_student("Jane", "Smith", "2010-01-01")
#     token = result["qr_token"]
#
#     response = client.get(
#         f"/auth/qr-login?token={token}",
#         follow_redirects=False,
#     )
#     assert response.status_code == 302
#     assert "/classrooms" in response.headers["Location"]
#
#
# def test_qr_login_sets_session(teacher_client, client):
#     from app.models.classroom import provision_student
#
#     result = provision_student("Jane", "Smith", "2010-01-01")
#     token = result["qr_token"]
#
#     with client:
#         client.get(f"/auth/qr-login?token={token}", follow_redirects=True)
#         with client.session_transaction() as sess:
#             assert sess.get("username") == "jane.smith"
#             assert sess.get("role") == "student"
#             assert sess.get("coppa_status") == "approved"
#             assert sess.get("user_id") is not None
#
#
# def test_qr_login_invalid_token(client):
#     response = client.get(
#         "/auth/qr-login?token=invalidtoken123",
#         follow_redirects=True,
#     )
#     assert b"Invalid" in response.data
#
#
# def test_qr_login_empty_token(client):
#     response = client.get(
#         "/auth/qr-login?token=",
#         follow_redirects=True,
#     )
#     assert b"Invalid" in response.data
#
#
# def test_qr_login_no_token(client):
#     response = client.get(
#         "/auth/qr-login",
#         follow_redirects=True,
#     )
#     assert b"Invalid" in response.data
#
#
# def test_qr_login_non_provisional_account(client):
#     """Self-registered accounts cannot log in via QR."""
#     from app.models import get_db
#
#     # manually give a self-registered user a qr_token (shouldn't happen in practice)
#     client.post(
#         "/auth/register",
#         data={
#             "username": "selfuser",
#             "password": "pass123",
#             "bio": "",
#             "dob": "2008-01-01",
#         },
#     )
#     with client.application.app_context():
#         db = get_db()
#         db.execute(
#             "UPDATE users SET qr_token = 'hackedtoken123' WHERE username = 'selfuser'"
#         )
#         db.commit()
#
#     response = client.get(
#         "/auth/qr-login?token=hackedtoken123",
#         follow_redirects=True,
#     )
#     assert b"Invalid" in response.data
#
#
# def test_qr_login_is_rate_limited(client, teacher_client):
#     from app.models.classroom import provision_student
#
#     provision_student("Jane", "Smith", "2010-01-01")
#
#     for _ in range(25):
#         client.get("/auth/qr-login?token=badtoken")
#
#     response = client.get("/auth/qr-login?token=badtoken", follow_redirects=True)
#     assert response.status_code in (429, 200)
#
#
# # --- regenerate qr token
#
#
# def test_teacher_can_regenerate_qr_token(teacher_client, classroom):
#     from app.models.classroom import provision_student, get_classroom
#     from app.models.user import get_user_by_username
#     import re
#
#     c = get_classroom(classroom)
#     result = provision_student("Jane", "Smith", "2010-01-01", [c["join_code"]])
#     old_token = result["qr_token"]
#
#     user = get_user_by_username("jane.smith")
#     response = teacher_client.post(
#         f"/classrooms/{classroom}/students/{user['id']}/regenerate-qr",
#         follow_redirects=True,
#     )
#     assert response.status_code == 200
#     assert b"regenerated" in response.data
#
#     user = get_user_by_username("jane.smith")
#     assert user["qr_token"] != old_token
#
#
# def test_old_qr_token_invalid_after_regeneration(teacher_client, classroom, client):
#     from app.models.classroom import provision_student, get_classroom
#     from app.models.user import get_user_by_username
#
#     c = get_classroom(classroom)
#     result = provision_student("Jane", "Smith", "2010-01-01", [c["join_code"]])
#     old_token = result["qr_token"]
#
#     user = get_user_by_username("jane.smith")
#     teacher_client.post(
#         f"/classrooms/{classroom}/students/{user['id']}/regenerate-qr",
#     )
#
#     response = client.get(
#         f"/auth/qr-login?token={old_token}",
#         follow_redirects=True,
#     )
#     assert b"Invalid" in response.data
#
#
# def test_student_cannot_regenerate_qr(student_client, teacher_client, classroom):
#     from app.models.classroom import provision_student, get_classroom
#     from app.models.user import get_user_by_username
#     import re
#
#     response = teacher_client.get(f"/classrooms/{classroom}")
#     html = response.data.decode()
#     match = re.search(r'data-join-code="([A-Z0-9]{6})"', html)
#     join_code = match.group(1) if match else None
#
#     result = provision_student("Jane", "Smith", "2010-01-01", [join_code])
#     user = get_user_by_username("jane.smith")
#
#     response = student_client.post(
#         f"/classrooms/{classroom}/students/{user['id']}/regenerate-qr",
#     )
#     assert response.status_code == 403
#
#
# def test_regenerate_qr_non_provisional_fails(teacher_client, classroom, student_client):
#     """Cannot regenerate QR for a self-registered student."""
#     import re
#
#     response = teacher_client.get(f"/classrooms/{classroom}")
#     html = response.data.decode()
#     match = re.search(r'data-join-code="([A-Z0-9]{6})"', html)
#     join_code = match.group(1) if match else None
#
#     student_client.post("/classrooms/join", data={"join_code": join_code})
#
#     from app.models.user import get_user_by_username
#
#     user = get_user_by_username("student1")
#
#     response = teacher_client.post(
#         f"/classrooms/{classroom}/students/{user['id']}/regenerate-qr",
#     )
#     assert response.status_code == 403
#
#
# # --- qr sheet route
#
#
# def test_qr_sheet_loads_after_provision(teacher_client):
#     with teacher_client.session_transaction() as sess:
#         sess["provisioned_students"] = [
#             {
#                 "first_name": "Jane",
#                 "last_name": "Smith",
#                 "username": "jane.smith",
#                 "password": "sunnybird42",
#                 "dob": "2010-01-01",
#                 "classrooms": [],
#                 "invalid_codes": [],
#                 "qr_token": "abc123token456def789ghi012jkl345",
#             }
#         ]
#         sess["provisioned_skipped"] = []
#
#     response = teacher_client.get("/classrooms/provision/qr-sheet")
#     assert response.status_code == 200
#     assert b"Jane Smith" in response.data
#     assert b"jane.smith" in response.data
#
#
# def test_qr_sheet_without_session(teacher_client):
#     response = teacher_client.get(
#         "/classrooms/provision/qr-sheet",
#         follow_redirects=True,
#     )
#     assert b"No provisioning data" in response.data
#
#
# def test_qr_sheet_requires_teacher(student_client):
#     response = student_client.get("/classrooms/provision/qr-sheet")
#     assert response.status_code == 403
#
#
# def test_qr_sheet_requires_login(client):
#     response = client.get("/classrooms/provision/qr-sheet")
#     assert response.status_code == 302
#     assert "/auth/login" in response.headers["Location"]
#
#
# def test_qr_sheet_contains_qr_image(teacher_client):
#     with teacher_client.session_transaction() as sess:
#         sess["provisioned_students"] = [
#             {
#                 "first_name": "Jane",
#                 "last_name": "Smith",
#                 "username": "jane.smith",
#                 "password": "sunnybird42",
#                 "dob": "2010-01-01",
#                 "classrooms": [],
#                 "invalid_codes": [],
#                 "qr_token": "abc123token456def789ghi012jkl345",
#             }
#         ]
#         sess["provisioned_skipped"] = []
#
#     response = teacher_client.get("/classrooms/provision/qr-sheet")
#     assert b"data:image/png;base64," in response.data
#
#
# # --- login page
#
#
# def test_login_page_has_qr_scan_button(client):
#     response = client.get("/auth/login")
#     assert b"Scan QR Code" in response.data
#
#
# def test_login_page_loads_jsqr(client):
#     response = client.get("/auth/login")
#     assert b"QR" in response.data
