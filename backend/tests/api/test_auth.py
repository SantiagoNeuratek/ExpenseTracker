from fastapi.testclient import TestClient


def test_login(client: TestClient):
    login_data = {"username": "admin@test.com", "password": "password"}
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_invalid_credentials(client: TestClient):
    login_data = {"username": "admin@test.com", "password": "wrong_password"}
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 400
    assert "Email o contraseña incorrectos" in response.json()["detail"]


def test_me(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "admin@test.com"
    assert response.json()["is_admin"] == True
