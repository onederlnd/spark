# tests/test_legal.py


def test_terms_page_loads(client):
    """Terms of Service page is publicly accessible"""
    response = client.get("/auth/terms")
    assert response.status_code == 200


def test_privacy_page_loads(client):
    """Privacy page is publicly accessible"""
    response = client.get("/auth/privacy")
    assert response.status_code == 200
