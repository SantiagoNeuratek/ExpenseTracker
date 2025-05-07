from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import pytest
from sqlalchemy.orm import Session
import json
import hashlib
from unittest.mock import patch, MagicMock
from jose import jwt

from app.models.expense import Expense
from app.models.category import Category
from app.models.audit import AuditRecord
from app.models.apikey import ApiKey
from app.models.user import User
from app.core.security import create_api_key, hash_api_key


@pytest.fixture
def test_expense(db: Session):
    """Create a test expense"""
    category = db.query(Category).filter(Category.is_active == True).first()
    if not category:
        pytest.skip("No active categories found in database")
        
    user = db.query(User).filter(User.company_id == category.company_id).first()
    if not user:
        pytest.skip("No users found for the category's company")
    
    expense = Expense(
        amount=150.0,
        date_incurred=datetime.now(),
        description="Test expense for reading",
        category_id=category.id,
        user_id=user.id,
        company_id=category.company_id
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@pytest.fixture
def api_key(db: Session):
    """Create an API key for testing"""
    # Get a company and user
    user = db.query(User).first()
    if not user:
        pytest.skip("No users found in database")
    
    # Create API key
    api_key_value = create_api_key(user.id, user.company_id)  # Corregida la firma
    api_key_hash = hash_api_key(api_key_value)
    
    # Create API key record
    api_key = ApiKey(
        user_id=user.id,
        company_id=user.company_id,
        name="Test API Key",
        key_hash=api_key_hash,
        is_active=True
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return api_key_value


def test_read_expense_by_id(client: TestClient, user_token: str, test_expense: Expense):
    """Test retrieving a specific expense by ID"""
    # Arrange
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Act
    response = client.get(f"/api/v1/expenses/{test_expense.id}", headers=headers)
    
    # Assert
    assert response.status_code == 200
    expense_data = response.json()
    assert expense_data["id"] == test_expense.id
    assert expense_data["amount"] == test_expense.amount
    assert expense_data["description"] == test_expense.description


def test_read_nonexistent_expense(client: TestClient, user_token: str, db: Session):
    """Test retrieving a non-existent expense returns 404"""
    # Arrange
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Find a non-existent ID
    expense = db.query(Expense).first()
    if not expense:
        pytest.skip("No expenses found in database")
        
    non_existent_id = expense.id + 1000  # Assuming this ID doesn't exist
    
    # Act
    response = client.get(f"/api/v1/expenses/{non_existent_id}", headers=headers)
    
    # Assert
    assert response.status_code == 404
    assert "Gasto no encontrado" in response.json()["detail"]


def test_read_expense_from_different_company(client: TestClient, user_token: str, test_expense: Expense, db: Session):
    """Test accessing an expense from a different company returns 404"""
    # Only run if there's more than one company
    companies_count = db.query(Category.company_id).distinct().count()
    if companies_count <= 1:
        pytest.skip("Need at least two companies for this test")
    
    # Create an expense for a different company
    other_company = db.query(Category).filter(Category.company_id != test_expense.company_id).first()
    if not other_company:
        pytest.skip("Could not find another company")
    
    user = db.query(User).filter(User.company_id == other_company.company_id).first()
    if not user:
        pytest.skip("Could not find a user for the other company")
    
    other_expense = Expense(
        amount=200.0,
        date_incurred=datetime.now(),
        description="Other company expense",
        category_id=other_company.id,
        user_id=user.id,
        company_id=other_company.company_id
    )
    db.add(other_expense)
    db.commit()
    db.refresh(other_expense)
    
    # Arrange
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Act
    response = client.get(f"/api/v1/expenses/{other_expense.id}", headers=headers)
    
    # Assert
    assert response.status_code == 404
    assert "Gasto no encontrado" in response.json()["detail"]


def test_get_top_categories_history(client: TestClient, api_key: str, db: Session):
    """Test retrieving top categories of all time with API key auth"""
    # Arrange
    headers = {"api-key": api_key}
    
    # Act
    response = client.get("/api/v1/expenses/top-categories-history", headers=headers)
    
    # Assert
    assert response.status_code == 200
    categories = response.json()
    assert isinstance(categories, list)
    
    # Verify default limit is 3
    assert len(categories) <= 3
    
    # Check structure
    if categories:  # Solo verificar si hay categorías
        for category in categories:
            assert "id" in category
            assert "name" in category
            assert "total_amount" in category


def test_get_top_categories_history_with_custom_limit(client: TestClient, api_key: str):
    """Test retrieving top categories with custom limit"""
    # Arrange
    headers = {"api-key": api_key}
    custom_limit = 2
    
    # Act
    response = client.get(f"/api/v1/expenses/top-categories-history?limit={custom_limit}", headers=headers)
    
    # Assert
    assert response.status_code == 200
    categories = response.json()
    assert len(categories) <= custom_limit


def test_get_top_categories_with_cache(client: TestClient, user_token: str, db: Session):
    """Test that top-categories endpoint uses cache correctly"""
    # Arrange
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Get user's company ID from token
    from app.core.config import settings
    
    token_data = jwt.decode(
        user_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    company_id = token_data.get("company_id")
    
    # Set up cache mock
    cache_key = f"top_categories:{company_id}:{datetime.now().date() - timedelta(days=30)}:{datetime.now().date()}:5"
    cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()
    cached_data = [
        {"id": 1, "name": "Test Category", "total_amount": 500.0}
    ]
    
    # Importar directamente el módulo de cache para mockear el objeto cache
    from app.core.cache import cache as app_cache
    
    # First test - cache miss
    with patch.object(app_cache, "get", return_value=None) as mock_get:
        with patch.object(app_cache, "set", return_value=True) as mock_set:
            response = client.get("/api/v1/expenses/top-categories", headers=headers)
            
            assert response.status_code == 200
            assert isinstance(response.json(), list)
            mock_get.assert_called()
            mock_set.assert_called()
    
    # Second test - cache hit
    with patch.object(app_cache, "get", return_value=json.dumps(cached_data)) as mock_get:
        with patch.object(app_cache, "set", return_value=True) as mock_set:
            response = client.get("/api/v1/expenses/top-categories", headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            assert result == cached_data
            mock_get.assert_called()
            mock_set.assert_not_called()


def test_update_expense_category_not_found(client: TestClient, admin_token: str, test_expense: Expense, db: Session):
    """Test updating an expense with non-existent category returns 404"""
    # Arrange
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get highest category ID and add 1000 to ensure it doesn't exist
    max_category = db.query(Category).order_by(Category.id.desc()).first()
    if not max_category:
        pytest.skip("No categories found in database")
        
    non_existent_category_id = max_category.id + 1000
    
    update_data = {
        "amount": 300.0,
        "description": "Updated with invalid category",
        "category_id": non_existent_category_id
    }
    
    # Act
    response = client.put(
        f"/api/v1/expenses/{test_expense.id}",
        json=update_data,
        headers=headers
    )
    
    # Assert
    assert response.status_code == 404
    assert "Categoría no encontrada" in response.json()["detail"]


def test_update_expense_from_different_company(client: TestClient, admin_token: str, db: Session):
    """Test updating an expense from a different company returns 404"""
    # Create an expense
    expense = db.query(Expense).first()
    if not expense:
        pytest.skip("No expenses found in database")
    
    # Get admin's company from token
    from app.core.config import settings
    
    token_data = jwt.decode(
        admin_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    admin_company_id = token_data.get("company_id")
    
    # If the expense already belongs to admin's company, we need to create one that doesn't
    if expense.company_id == admin_company_id:
        # Find a company different from admin's
        other_company = db.query(Category).filter(Category.company_id != admin_company_id).first()
        if not other_company:
            pytest.skip("Need at least two companies for this test")
            
        user = db.query(User).filter(User.company_id == other_company.company_id).first()
        if not user:
            pytest.skip("Need a user from different company for this test")
            
        expense = Expense(
            amount=123.45,
            date_incurred=datetime.now(),
            description="Expense from different company",
            category_id=other_company.id,
            user_id=user.id,
            company_id=other_company.company_id
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)
    
    # Arrange
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    update_data = {
        "amount": 456.78,
        "description": "Should not update"
    }
    
    # Act
    response = client.put(
        f"/api/v1/expenses/{expense.id}",
        json=update_data,
        headers=headers
    )
    
    # Assert
    assert response.status_code == 404
    assert "Gasto no encontrado" in response.json()["detail"]


def test_delete_nonexistent_expense(client: TestClient, admin_token: str, db: Session):
    """Test deleting a non-existent expense returns 404"""
    # Arrange
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Find a non-existent ID
    expense = db.query(Expense).first()
    if not expense:
        pytest.skip("No expenses found in database")
        
    non_existent_id = expense.id + 1000  # Assuming this ID doesn't exist
    
    # Act
    response = client.delete(f"/api/v1/expenses/{non_existent_id}", headers=headers)
    
    # Assert
    assert response.status_code == 404
    assert "Gasto no encontrado" in response.json()["detail"]


def test_delete_expense_from_different_company(client: TestClient, admin_token: str, db: Session):
    """Test deleting an expense from a different company returns 404"""
    # Get admin's company from token
    from app.core.config import settings
    
    token_data = jwt.decode(
        admin_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    admin_company_id = token_data.get("company_id")
    
    # Find a company different from admin's
    other_company = db.query(Category).filter(Category.company_id != admin_company_id).first()
    if not other_company:
        pytest.skip("Need at least two companies for this test")
        
    user = db.query(User).filter(User.company_id == other_company.company_id).first()
    if not user:
        pytest.skip("Need a user from different company for this test")
        
    # Create an expense for that company
    expense = Expense(
        amount=321.54,
        date_incurred=datetime.now(),
        description="Expense for delete test",
        category_id=other_company.id,
        user_id=user.id,
        company_id=other_company.company_id
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    
    # Arrange
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Act
    response = client.delete(f"/api/v1/expenses/{expense.id}", headers=headers)
    
    # Assert
    assert response.status_code == 404
    assert "Gasto no encontrado" in response.json()["detail"] 