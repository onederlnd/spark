# --- resource library ---
import io


def test_resource_library_requires_login(client, classroom):
    response = client.get(f"/classrooms/{classroom}/resources", follow_redirects=False)
    assert response.status_code == 302


def test_resource_library_forbidden_for_student(auth_client, classroom):
    auth_client.post(
        "/classrooms/join",
        data={"join_code": "MATH01"},
    )
    response = auth_client.get(f"/classrooms/{classroom}/resources")
    assert response.status_code == 403


def test_resource_library_loads_for_teacher(teacher_client, classroom):
    response = teacher_client.get(f"/classrooms/{classroom}/resources")
    assert response.status_code == 200
    assert b"Resource Library" in response.data


def test_resource_library_empty_state(teacher_client, classroom):
    response = teacher_client.get(f"/classrooms/{classroom}/resources")
    assert response.status_code == 200
    assert b"No resources yet" in response.data


# --- add link ---


def test_add_resource_link_requires_login(client, classroom):
    response = client.post(
        f"/classrooms/{classroom}/resources/add-link",
        data={"title": "Khan Academy", "url": "https://khanacademy.org"},
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_add_resource_link_forbidden_for_student(auth_client, classroom):
    response = auth_client.post(
        f"/classrooms/{classroom}/resources/add-link",
        data={"title": "Khan Academy", "url": "https://khanacademy.org"},
    )
    assert response.status_code == 403


def test_add_resource_link_appears_in_library(teacher_client, classroom):
    teacher_client.post(
        f"/classrooms/{classroom}/resources/add-link",
        data={"title": "Khan Academy", "url": "https://khanacademy.org"},
    )
    response = teacher_client.get(f"/classrooms/{classroom}/resources")
    assert response.status_code == 200
    assert b"Khan Academy" in response.data


def test_add_resource_link_missing_title_rejected(teacher_client, classroom):
    response = teacher_client.post(
        f"/classrooms/{classroom}/resources/add-link",
        data={"title": "", "url": "https://khanacademy.org"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Title and URL are required." in response.data


def test_add_resource_link_missing_url_rejected(teacher_client, classroom):
    response = teacher_client.post(
        f"/classrooms/{classroom}/resources/add-link",
        data={"title": "Some Site", "url": ""},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Some Site" not in response.data


# --- add file ---


def test_add_resource_file_requires_login(client, classroom):
    response = client.post(
        f"/classrooms/{classroom}/resources/add-file",
        data={"title": "Notes", "file": (b"hello", "notes.txt")},
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_add_resource_file_appears_in_library(teacher_client, classroom):
    teacher_client.post(
        f"/classrooms/{classroom}/resources/add-file",
        data={
            "title": "Chapter Notes",
            "file": (io.BytesIO(b"PDF content"), "notes.pdf"),
        },
        content_type="multipart/form-data",
    )
    response = teacher_client.get(f"/classrooms/{classroom}/resources")
    assert response.status_code == 200
    assert b"Chapter Notes" in response.data


# --- delete resource ---


def test_delete_resource_requires_login(client, classroom):
    response = client.post(
        f"/classrooms/{classroom}/resources/1/delete",
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_delete_resource_forbidden_for_student(auth_client, classroom):
    response = auth_client.post(f"/classrooms/{classroom}/resources/1/delete")
    assert response.status_code == 403


def test_delete_resource_removes_from_library(teacher_client, classroom):
    teacher_client.post(
        f"/classrooms/{classroom}/resources/add-link",
        data={"title": "Delete Me", "url": "https://deleteme.com"},
    )
    response = teacher_client.get(f"/classrooms/{classroom}/resources")
    assert b"Delete Me" in response.data

    # Extract the resource id from the delete form action in the page
    import re

    match = re.search(
        rf"/classrooms/{classroom}/resources/(\d+)/delete",
        response.data.decode(),
    )
    assert match, "Could not find delete URL for resource in page"
    resource_id = match.group(1)

    teacher_client.post(f"/classrooms/{classroom}/resources/{resource_id}/delete")
    response = teacher_client.get(f"/classrooms/{classroom}/resources")
    assert b"Delete Me" not in response.data


def test_delete_nonexistent_resource(teacher_client, classroom):
    response = teacher_client.post(f"/classrooms/{classroom}/resources/999999/delete")
    assert response.status_code in (302, 404)
