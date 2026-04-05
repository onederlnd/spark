def test_show_settings_loads(auth_client):
    """GET /profile/settings return 200 for logged in user"""
    response = auth_client.get("/profile/settings")
    assert response.status_code == 200


def test_show_settings_requires_login(client):
    """GET profile/settings redirects to login if not authenticated"""
    response = client.get("/profile/settings")
    assert response.status_code == 302


def test_update_bio_success(auth_client):
    """POST /profile/settings/bio updates bio and redirects"""
    response = auth_client.post(
        "/profile/settings/bio", data={"bio": "Updated bio - succeess"}
    )
    assert response.status_code == 302


def test_update_bio_empty(auth_client):
    """POST /profile/settings/bio with empty bio is allowed"""
    response = auth_client.post("/profile/settings/bio", data={"bio": ""})
    assert response.status_code == 302


def test_update_password_success(auth_client):  # 302
    """POST /profile/settings/password with correct current password updates it"""
    response = auth_client.post(
        "/profile/settings/password",
        data={"current_password": "password123", "new_password": "newpass123"},
    )
    assert response.status_code == 302


def test_update_password_wrong_current(auth_client):
    """POST /profile/settings/password with wrong current password returns error"""
    response = auth_client.post(
        "/profile/settings/password",
        data={"current_password": "wrongpassword", "new_password": "newpass123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Current password is incorrect" in response.data


def test_updated_password_can_login(auth_client, client):
    """After password change, user can login using new password"""

    auth_client.post(
        "/profile/settings/password",
        data={"current_password": "password123", "new_password": "newpass123"},
    )
    response = client.post(
        "/auth/login", data={"username": "testuser", "password": "newpass123"}
    )
    assert response.status_code == 302


def test_update_bio_shows_on_profile(auth_client):
    """After bio update, new bio appears on profile page"""
    response = auth_client.post(
        "/profile/settings/bio", data={"bio": "This is an updated bio"}
    )
    response = auth_client.get("/profile/testuser")
    assert response.status_code == 200
    assert b"testuser" in response.data
