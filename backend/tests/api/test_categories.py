import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch

from app.models.category import Category


def test_get_categories(client: TestClient, user_token: str):
    """Test getting all categories for the user's company"""
    # Arrange
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Act
    response = client.get("/api/v1/categories", headers=headers)
    
    # Assert
    assert response.status_code == 200
    categories = response.json()
    assert isinstance(categories, list)
    assert len(categories) >= 2  # At least the two test categories
    
    # Check structure of returned categories
    for category in categories:
        assert "id" in category
        assert "name" in category
        assert "description" in category
        assert "company_id" in category
        assert "expense_limit" in category
        assert "is_active" in category


def test_create_category(client: TestClient, user_token: str, db: Session):
    """Test creating a new category"""
    # Arrange
    headers = {"Authorization": f"Bearer {user_token}"}
    category_data = {
        "name": "New Test Category",
        "description": "A new test category",
        "expense_limit": 200.0,
    }
    
    # Act
    response = client.post("/api/v1/categories", json=category_data, headers=headers)
    
    # Assert
    assert response.status_code == 200
    created_category = response.json()
    assert created_category["name"] == category_data["name"]
    assert created_category["description"] == category_data["description"]
    assert created_category["expense_limit"] == category_data["expense_limit"]
    assert "id" in created_category
    
    # Verify category was actually created in database
    db_category = db.query(Category).filter(Category.id == created_category["id"]).first()
    assert db_category is not None
    assert db_category.name == category_data["name"]


def test_create_category_with_duplicate_name(client: TestClient, user_token: str, db: Session):
    """Test creating a category with a name that already exists returns an error"""
    # Arrange
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Get existing category name
    existing_category = db.query(Category).first()
    
    category_data = {
        "name": existing_category.name,  # Use existing name to trigger duplicate error
        "description": "Duplicate category test",
        "expense_limit": 150.0,
    }
    
    # Act
    response = client.post("/api/v1/categories", json=category_data, headers=headers)
    
    # Assert
    assert response.status_code == 400
    assert "Ya existe una categoría con este nombre" in response.json()["detail"]


def test_get_category_by_id(client: TestClient, user_token: str, db: Session):
    """Test getting a single category by ID"""
    # Arrange
    headers = {"Authorization": f"Bearer {user_token}"}
    existing_category = db.query(Category).first()
    
    # Act
    response = client.get(f"/api/v1/categories/{existing_category.id}", headers=headers)
    
    # Assert
    assert response.status_code == 200
    category = response.json()
    assert category["id"] == existing_category.id
    assert category["name"] == existing_category.name
    assert category["description"] == existing_category.description


def test_get_category_not_found(client: TestClient, user_token: str):
    """Test getting a non-existent category returns 404"""
    # Arrange
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Act
    response = client.get("/api/v1/categories/99999", headers=headers)
    
    # Assert
    assert response.status_code == 404
    assert "Categoría no encontrada" in response.json()["detail"]


def test_update_category(client: TestClient, user_token: str, db: Session):
    """Test updating a category"""
    # Arrange
    headers = {"Authorization": f"Bearer {user_token}"}
    existing_category = db.query(Category).first()
    
    update_data = {
        "name": f"Updated {existing_category.name}",
        "description": "Updated description",
        "expense_limit": 300.0,
    }
    
    # Act
    response = client.put(
        f"/api/v1/categories/{existing_category.id}", 
        json=update_data, 
        headers=headers
    )
    
    # Assert
    assert response.status_code == 200
    updated_category = response.json()
    assert updated_category["name"] == update_data["name"]
    assert updated_category["description"] == update_data["description"]
    assert updated_category["expense_limit"] == update_data["expense_limit"]
    
    # Verify the update happened in database
    db.refresh(existing_category)
    assert existing_category.name == update_data["name"]
    assert existing_category.description == update_data["description"]
    assert existing_category.expense_limit == update_data["expense_limit"]


def test_delete_category(client: TestClient, admin_token: str, db: Session):
    """Test soft deleting a category (setting is_active to False)"""
    # Arrange
    headers = {"Authorization": f"Bearer {admin_token}"}
    existing_category = db.query(Category).first()
    
    # Act
    response = client.delete(f"/api/v1/categories/{existing_category.id}", headers=headers)
    
    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == "Categoría eliminada"
    
    # Verify category was soft deleted in database
    db.refresh(existing_category)
    assert existing_category.is_active is False


def test_unauthorized_access(client: TestClient):
    """Test that unauthorized access returns 401"""
    # Restaurar la dependencia original para este test
    from app.api.deps import get_current_user, get_current_admin
    from app.main import app
    
    # Guardamos los overrides anteriores
    previous_overrides = app.dependency_overrides.copy()
    
    # Aseguramos que no haya override para la autenticación
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]
    if get_current_admin in app.dependency_overrides:
        del app.dependency_overrides[get_current_admin]
    
    try:
        # Intentar acceder sin token
        response = client.get("/api/v1/categories/", headers={})
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
    finally:
        # Restaurar los overrides originales
        app.dependency_overrides = previous_overrides
