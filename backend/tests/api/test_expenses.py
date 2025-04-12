from fastapi.testclient import TestClient
from datetime import datetime, timedelta


def test_create_expense(client: TestClient, user_token: str):
    headers = {"Authorization": f"Bearer {user_token}"}

    # Datos del gasto a crear
    expense_data = {
        "amount": 150.75,
        "date_incurred": (datetime.now() - timedelta(days=1)).isoformat(),
        "description": "Test expense",
        "category_id": 1,  # Usar una categoría existente
    }

    response = client.post("/api/v1/expenses", json=expense_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["amount"] == expense_data["amount"]
    assert response.json()["description"] == expense_data["description"]
    assert response.json()["category_id"] == expense_data["category_id"]
    assert "id" in response.json()


def test_read_expenses(client: TestClient, user_token: str):
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.get("/api/v1/expenses", headers=headers)
    assert response.status_code == 200
    assert "items" in response.json()
    assert "total" in response.json()
    assert "page" in response.json()
    assert "page_size" in response.json()


def test_read_expenses_with_filter(client: TestClient, user_token: str):
    headers = {"Authorization": f"Bearer {user_token}"}

    # Filtrar por fechas y categoría
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    response = client.get(
        f"/api/v1/expenses?start_date={start_date}&end_date={end_date}&category_id=1",
        headers=headers,
    )
    assert response.status_code == 200
    assert "items" in response.json()


def test_update_expense_admin_only(
    client: TestClient, user_token: str, admin_token: str
):
    headers_user = {"Authorization": f"Bearer {user_token}"}
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    # Primero, crear un gasto
    expense_data = {
        "amount": 50.25,
        "date_incurred": datetime.now().isoformat(),
        "description": "Test update expense",
        "category_id": 1,
    }

    create_response = client.post(
        "/api/v1/expenses", json=expense_data, headers=headers_user
    )
    assert create_response.status_code == 200
    expense_id = create_response.json()["id"]

    # Intentar actualizar con usuario normal (debe fallar)
    update_data = {"amount": 75.50}

    user_update_response = client.put(
        f"/api/v1/expenses/{expense_id}", json=update_data, headers=headers_user
    )
    assert user_update_response.status_code == 403  # Acceso denegado

    # Actualizar con administrador (debe funcionar)
    admin_update_response = client.put(
        f"/api/v1/expenses/{expense_id}", json=update_data, headers=headers_admin
    )
    assert admin_update_response.status_code == 200
    assert admin_update_response.json()["amount"] == update_data["amount"]


def test_delete_expense_admin_only(
    client: TestClient, user_token: str, admin_token: str
):
    headers_user = {"Authorization": f"Bearer {user_token}"}
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    # Primero, crear un gasto
    expense_data = {
        "amount": 35.60,
        "date_incurred": datetime.now().isoformat(),
        "description": "Test delete expense",
        "category_id": 1,
    }

    create_response = client.post(
        "/api/v1/expenses", json=expense_data, headers=headers_user
    )
    assert create_response.status_code == 200
    expense_id = create_response.json()["id"]

    # Intentar eliminar con usuario normal (debe fallar)
    user_delete_response = client.delete(
        f"/api/v1/expenses/{expense_id}", headers=headers_user
    )
    assert user_delete_response.status_code == 403  # Acceso denegado

    # Eliminar con administrador (debe funcionar)
    admin_delete_response = client.delete(
        f"/api/v1/expenses/{expense_id}", headers=headers_admin
    )
    assert admin_delete_response.status_code == 200
    assert "success" in admin_delete_response.json()["status"]
