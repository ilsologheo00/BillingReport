def test_login_success(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "change-me"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


def test_customers_requires_auth(client):
    resp = client.get("/api/customers")
    assert resp.status_code in (401, 403)
