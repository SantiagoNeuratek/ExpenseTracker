from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import pytest
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.category import Category
from app.models.audit import AuditRecord


def test_create_expense(client: TestClient, user_token: str, db: Session):
    """Test creating a new expense"""
    # Arrange
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Get a valid category for the test
    category = db.query(Category).filter(Category.is_active == True).first()
    
    expense_data = {
        "amount": 75.50,
        "date_incurred": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        "description": "Test expense creation",
        "category_id": category.id
    }
    
    # Act
    response = client.post("/api/v1/expenses", json=expense_data, headers=headers)
    
    # Assert
    assert response.status_code == 200
    created_expense = response.json()
    assert created_expense["amount"] == expense_data["amount"]
    assert expense_data["date_incurred"] in created_expense["date_incurred"]  # Check date part
    assert created_expense["description"] == expense_data["description"]
    assert created_expense["category_id"] == expense_data["category_id"]
    
    # Verify expense was created in database
    db_expense = db.query(Expense).filter(Expense.id == created_expense["id"]).first()
    assert db_expense is not None
    assert db_expense.amount == expense_data["amount"]
    assert db_expense.description == expense_data["description"]


def test_create_expense_exceeding_limit(client: TestClient, user_token: str, db: Session):
    """Test creating an expense that exceeds category limit returns error"""
    # Arrange
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Find or create a category with an expense limit
    category = db.query(Category).filter(Category.expense_limit.isnot(None)).first()
    if not category:
        # Create a new category with limit if none exists
        category = Category(
            name="Test Category with Limit",
            description="Category with expense limit",
            expense_limit=100.0,
            company_id=db.query(Category).first().company_id  # Use the same company
        )
        db.add(category)
        db.commit()
        db.refresh(category)
    
    # Create expense that exceeds the limit
    expense_data = {
        "amount": category.expense_limit + 50.0,  # Exceed limit by 50
        "date_incurred": datetime.now().strftime("%Y-%m-%d"),
        "description": "Test expense limit",
        "category_id": category.id
    }
    
    # Act
    response = client.post("/api/v1/expenses", json=expense_data, headers=headers)
    
    # Assert
    assert response.status_code == 400
    assert "excede el límite de gastos" in response.json()["detail"]


def test_get_expenses(client: TestClient, user_token: str, db: Session):
    """Test retrieving expenses with pagination"""
    # Arrange
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Create a few test expenses first if there aren't any
    if db.query(Expense).count() == 0:
        category = db.query(Category).filter(Category.is_active == True).first()
        user = db.query(Category).filter(Category.id == category.id).first().company.users[0]
        
        # Create 3 test expenses
        for i in range(3):
            expense = Expense(
                amount=50.0 + i * 10,
                date_incurred=datetime.now() - timedelta(days=i),
                description=f"Test expense {i+1}",
                category_id=category.id,
                user_id=user.id,
                company_id=user.company_id
            )
            db.add(expense)
        db.commit()
    
    # Act - Get expenses with default pagination
    response = client.get("/api/v1/expenses", headers=headers)
    
    # Assert
    assert response.status_code == 200
    expenses_data = response.json()
    assert "total" in expenses_data
    assert "page" in expenses_data
    assert "page_size" in expenses_data
    assert "items" in expenses_data
    assert isinstance(expenses_data["items"], list)
    assert len(expenses_data["items"]) > 0
    
    # Check pagination
    response_page2 = client.get("/api/v1/expenses?page=2&page_size=1", headers=headers)
    assert response_page2.status_code == 200
    expenses_page2 = response_page2.json()
    assert expenses_page2["page"] == 2
    assert expenses_page2["page_size"] == 1
    
    # If there are multiple expenses, page 1 and page 2 should have different items
    if expenses_data["total"] > 1:
        assert expenses_data["items"][0]["id"] != expenses_page2["items"][0]["id"]


def test_get_expenses_with_filter(client: TestClient, user_token: str, db: Session):
    """Test filtering expenses by date range and category"""
    # Arrange
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Create an expense with a specific date for testing
    category = db.query(Category).filter(Category.is_active == True).first()
    user = db.query(Category).filter(Category.id == category.id).first().company.users[0]
    
    test_date = datetime.now() - timedelta(days=30)
    test_expense = Expense(
        amount=123.45,
        date_incurred=test_date,
        description="Test expense for date filter",
        category_id=category.id,
        user_id=user.id,
        company_id=user.company_id
    )
    db.add(test_expense)
    db.commit()
    db.refresh(test_expense)
    
    # Act - Filter by date range that includes our test expense
    start_date = (test_date - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (test_date + timedelta(days=1)).strftime("%Y-%m-%d")
    
    response = client.get(
        f"/api/v1/expenses?start_date={start_date}&end_date={end_date}",
        headers=headers
    )
    
    # Assert
    assert response.status_code == 200
    expenses_data = response.json()
    assert isinstance(expenses_data["items"], list)
    assert any(expense["id"] == test_expense.id for expense in expenses_data["items"])
    
    # Act - Filter by category
    response = client.get(
        f"/api/v1/expenses?category_id={category.id}",
        headers=headers
    )
    
    # Assert
    assert response.status_code == 200
    expenses_data = response.json()
    assert isinstance(expenses_data["items"], list)
    assert all(expense["category_id"] == category.id for expense in expenses_data["items"])


def test_update_expense(client: TestClient, admin_token: str, db: Session):
    """Test updating an expense as admin creates audit trail"""
    # Remove the skip decorator to run this test
    # Arrange
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get an existing expense
    expense = db.query(Expense).first()
    if not expense:
        # Create test expense if none exists
        category = db.query(Category).filter(Category.is_active == True).first()
        user = db.query(Category).filter(Category.id == category.id).first().company.users[0]
        
        expense = Expense(
            amount=200.0,
            date_incurred=datetime.now(),
            description="Test expense for update",
            category_id=category.id,
            user_id=user.id,
            company_id=user.company_id
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)
    
    original_amount = expense.amount
    
    update_data = {
        "amount": original_amount + 100.0,
        "description": "Updated description for testing"
    }
    
    # Act
    response = client.put(
        f"/api/v1/expenses/{expense.id}",
        json=update_data,
        headers=headers
    )
    
    # Assert
    assert response.status_code == 200
    updated_expense = response.json()
    assert updated_expense["amount"] == update_data["amount"]
    assert updated_expense["description"] == update_data["description"]
    
    # Verify database update
    db.refresh(expense)
    assert expense.amount == update_data["amount"]
    assert expense.description == update_data["description"]
    
    # Verify audit trail was created
    audit_records = db.query(AuditRecord).filter(
        AuditRecord.expense_id == expense.id
    ).all()
    
    assert len(audit_records) > 0
    latest_audit = audit_records[-1]
    assert latest_audit.action == "update"
    assert "amount" in latest_audit.previous_data
    assert float(latest_audit.previous_data["amount"]) == original_amount


def test_delete_expense(client: TestClient, admin_token: str, db: Session):
    """Test delete expense creates an audit trail and properly removes the expense"""
    # Arrange
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create a test expense to delete
    category = db.query(Category).filter(Category.is_active == True).first()
    user = db.query(Category).filter(Category.id == category.id).first().company.users[0]
    
    expense = Expense(
        amount=150.0,
        date_incurred=datetime.now(),
        description="Test expense for deletion",
        category_id=category.id,
        user_id=user.id,
        company_id=user.company_id
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    
    # Remember the ID for checking audit trail
    expense_id = expense.id
    
    # Act
    response = client.delete(
        f"/api/v1/expenses/{expense_id}",
        headers=headers
    )
    
    # Assert
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify expense was deleted
    deleted_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    assert deleted_expense is None
    
    # Verify audit trail was created
    audit_records = db.query(AuditRecord).filter(
        AuditRecord.expense_id == expense_id
    ).all()
    
    assert len(audit_records) > 0
    latest_audit = audit_records[-1]
    assert latest_audit.action == "delete"
    assert "amount" in latest_audit.previous_data
    assert float(latest_audit.previous_data["amount"]) == 150.0


def test_get_top_categories(client: TestClient, db: Session):
    """Test the public API for getting top 3 categories by spending"""
    # Arrange - Create a test API key first
    from app.models.apikey import ApiKey
    from app.core.security import create_api_key, hash_api_key
    
    # Get a user and company
    user = db.query(Category).first().company.users[0]
    company_id = user.company_id
    
    # Create API key if it doesn't exist
    api_key_record = db.query(ApiKey).filter(
        ApiKey.user_id == user.id,
        ApiKey.is_active == True
    ).first()
    
    if not api_key_record:
        api_key = create_api_key(user.id, company_id)
        api_key_hash = hash_api_key(api_key)
        
        api_key_record = ApiKey(
            name="Test API Key",
            key_hash=api_key_hash,
            user_id=user.id,
            company_id=company_id
        )
        db.add(api_key_record)
        db.commit()
    else:
        # This is a test simplification - in a real scenario you'd use the original API key
        # For test purposes, we're creating a new one with the same hash
        api_key = create_api_key(user.id, company_id)
    
    # Create some test expenses if there aren't any
    categories = db.query(Category).filter(Category.company_id == company_id).limit(3).all()
    if len(categories) < 3:
        # Create additional categories if needed
        for i in range(3 - len(categories)):
            category = Category(
                name=f"Test Category {i+1}",
                description=f"Test category {i+1} for top categories test",
                company_id=company_id,
                is_active=True
            )
            db.add(category)
        db.commit()
        categories = db.query(Category).filter(Category.company_id == company_id).limit(3).all()
    
    # Create expenses for each category with different amounts to test the order
    for i, category in enumerate(categories):
        # Create an expense with amount based on index to ensure different totals
        expense = Expense(
            amount=100.0 * (3 - i),  # First category gets highest amount
            date_incurred=datetime.now(),
            description=f"Test expense for top categories",
            category_id=category.id,
            user_id=user.id,
            company_id=company_id
        )
        db.add(expense)
    db.commit()
    
    # Act
    headers = {"api-key": api_key}
    response = client.get("/api/v1/expenses/top-categories", headers=headers)
    
    # Assert
    assert response.status_code == 200
    top_categories = response.json()
    assert isinstance(top_categories, list)
    assert 1 <= len(top_categories) <= 3  # Should return up to 3 categories
    
    # Check structure of response
    for category in top_categories:
        assert "id" in category
        assert "name" in category
        assert "total_amount" in category
    
    # Verify the categories are ordered by amount (highest first)
    if len(top_categories) >= 2:
        assert top_categories[0]["total_amount"] >= top_categories[1]["total_amount"]

def test_get_expenses_by_category(client: TestClient, db: Session):
    """Test the API endpoint for getting expenses by category with a date range"""
    # Arrange - Create a test API key
    from app.models.apikey import ApiKey
    from app.core.security import create_api_key, hash_api_key
    
    # Get a user and company
    user = db.query(Category).first().company.users[0]
    company_id = user.company_id
    
    # Create API key if it doesn't exist
    api_key_record = db.query(ApiKey).filter(
        ApiKey.user_id == user.id,
        ApiKey.is_active == True
    ).first()
    
    if not api_key_record:
        api_key = create_api_key(user.id, company_id)
        api_key_hash = hash_api_key(api_key)
        
        api_key_record = ApiKey(
            name="Test API Key",
            key_hash=api_key_hash,
            user_id=user.id,
            company_id=company_id
        )
        db.add(api_key_record)
        db.commit()
    else:
        # For test purposes
        api_key = create_api_key(user.id, company_id)
    
    # Get a category
    category = db.query(Category).filter(
        Category.company_id == company_id,
        Category.is_active == True
    ).first()
    
    # Create test expenses in a specific date range
    test_date = datetime.now() - timedelta(days=15)
    for i in range(3):
        expense = Expense(
            amount=50.0 + i * 10,
            date_incurred=test_date + timedelta(days=i),
            description=f"Test expense {i+1} for by-category endpoint",
            category_id=category.id,
            user_id=user.id,
            company_id=company_id
        )
        db.add(expense)
    db.commit()
    
    # Set up date range
    start_date = (test_date - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (test_date + timedelta(days=5)).strftime("%Y-%m-%d")
    
    # Act
    headers = {"api-key": api_key}
    response = client.get(
        f"/api/v1/expenses/by-category?category_id={category.id}&start_date={start_date}&end_date={end_date}",
        headers=headers
    )
    
    # Assert
    assert response.status_code == 200
    expenses = response.json()
    assert isinstance(expenses, list)
    assert len(expenses) >= 3  # Should have at least our 3 test expenses
    
    # Check that all expenses are for the correct category
    for expense in expenses:
        assert expense["category_id"] == category.id
        # Check the date is within range
        expense_date = datetime.fromisoformat(expense["date_incurred"].replace('Z', '+00:00'))
        assert datetime.fromisoformat(start_date) <= expense_date <= datetime.fromisoformat(end_date)
