import os
import pytest
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.main import app
from app.api.deps import get_db, get_current_user, get_current_admin
from app.models.user import User
from app.models.company import Company
from app.models.category import Category
from app.core.security import create_access_token


# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def setup_db() -> Generator:
    # Create all tables in the database
    Base.metadata.create_all(bind=engine)
    yield
    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(setup_db) -> Generator:
    # Create a fresh database session for each test
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    # Setup test data
    setup_test_data(session)
    
    yield session
    
    # Rollback the transaction and close the connection
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db) -> Generator:
    # Override the get_db dependency to use our test database
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    # Override the authentication dependencies
    def override_get_current_user():
        return get_test_user(db)
    
    def override_get_current_admin():
        return get_test_admin(db)
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_admin] = override_get_current_admin
    
    with TestClient(app) as c:
        yield c
    
    # Reset overrides
    app.dependency_overrides = {}


@pytest.fixture(scope="function")
def admin_token(db) -> str:
    # Create an admin token for API authentication
    admin = get_test_admin(db)
    return create_access_token(
        admin.id, admin.company_id, admin.is_admin
    )


@pytest.fixture(scope="function")
def user_token(db) -> str:
    # Create a regular user token for API authentication
    user = get_test_user(db)
    return create_access_token(
        user.id, user.company_id, user.is_admin
    )


def setup_test_data(db: Session) -> None:
    """Set up initial test data"""
    # Create test company
    company = Company(
        name="Test Company",
        address="123 Test St",
        website="https://test.com",
        logo=b"test_logo_data"
    )
    db.add(company)
    db.flush()
    
    # Create admin user
    admin = User(
        email="admin@test.com",
        hashed_password="$2b$12$MQRCzgH4oWAx/T7qVl.aDu8Y3k7MJscmlMV7AUUSTLkrYRTV1sWWC",  # password
        is_admin=True,
        is_active=True,
        company_id=company.id
    )
    db.add(admin)
    
    # Create regular user
    user = User(
        email="user@test.com",
        hashed_password="$2b$12$MQRCzgH4oWAx/T7qVl.aDu8Y3k7MJscmlMV7AUUSTLkrYRTV1sWWC",  # password
        is_admin=False,
        is_active=True,
        company_id=company.id
    )
    db.add(user)
    
    # Create test categories
    categories = [
        Category(
            name="Test Category 1",
            description="Test description 1",
            expense_limit=100.0,
            company_id=company.id
        ),
        Category(
            name="Test Category 2",
            description="Test description 2",
            company_id=company.id
        )
    ]
    for category in categories:
        db.add(category)
    
    db.commit()


def get_test_admin(db: Session) -> User:
    """Get the test admin user"""
    return db.query(User).filter(User.email == "admin@test.com").first()


def get_test_user(db: Session) -> User:
    """Get the test regular user"""
    return db.query(User).filter(User.email == "user@test.com").first()
