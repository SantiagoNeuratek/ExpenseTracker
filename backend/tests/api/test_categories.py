from fastapi.testclient import TestClient


def test_create_category(client: TestClient, user_token: str):
    headers = {"Authorization": f"Bearer {user_token}"}
    category_data = {
        "name": "New Test Category",
        "description": "A new test category",
        "expense_limit": 200.0,
    }
    response = client.post("/api/v1/categories", json=category_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == category_data["name"]
    assert response.json()["description"] == category_data["description"]
    assert response.json()["expense_limit"] == category_data["expense_limit"]
    assert "id" in response.json()


def test_read_categories(client: TestClient, user_token: str):
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.get("/api/v1/categories", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert (
        len(response.json()) >= 2
    )  # Tenemos al menos las 2 categorías iniciales + la nueva


def test_read_category(client: TestClient, user_token: str):
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.get("/api/v1/categories/1", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["name"] == "Category 1"


def test_update_category(client: TestClient, user_token: str):
    headers = {"Authorization": f"Bearer {user_token}"}
    update_data = {"description": "Updated description"}
    response = client.put("/api/v1/categories/1", json=update_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["description"] == "Updated description"


def test_delete_category(client: TestClient, user_token: str):
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.delete("/api/v1/categories/2", headers=headers)
    assert response.status_code == 200

    # Verificar que la categoría se marcó como inactiva
    response = client.get("/api/v1/categories/2", headers=headers)
    assert response.status_code == 404  # Ya no debería encontrarse


def test_create_category_duplicate_name(client: TestClient, user_token: str):
    headers = {"Authorization": f"Bearer {user_token}"}

    # Primero creamos una categoría
    category_data = {
        "name": "Test Duplicate",
        "description": "This is a test for duplicates",
        "expense_limit": None,
    }
    response = client.post("/api/v1/categories", json=category_data, headers=headers)
    assert response.status_code == 200

    # Ahora intentamos crear otra con el mismo nombre
    response = client.post("/api/v1/categories", json=category_data, headers=headers)
    assert response.status_code == 400
    assert "Ya existe una categoría con este nombre" in response.json()["detail"]


def test_update_category_not_found(client: TestClient, user_token: str):
    headers = {"Authorization": f"Bearer {user_token}"}
    update_data = {"description": "This category doesn't exist"}
    response = client.put("/api/v1/categories/9999", json=update_data, headers=headers)
    assert response.status_code == 404
    assert "Categoría no encontrada" in response.json()["detail"]


def test_delete_category_not_found(client: TestClient, user_token: str):
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.delete("/api/v1/categories/9999", headers=headers)
    assert response.status_code == 404
    assert "Categoría no encontrada" in response.json()["detail"]
