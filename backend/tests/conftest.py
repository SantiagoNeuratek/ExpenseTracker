import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.main import app
from app.api.deps import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.models.company import Company
from app.models.category import Category

# Crear una base de datos en memoria para testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db():
    # Crear las tablas en la base de datos de prueba
    Base.metadata.create_all(bind=engine)

    # Crear una sesión para las pruebas
    session = TestingSessionLocal()

    # Crear datos de prueba
    # Logo como bytes (para pruebas)
    test_logo = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    # Crear empresa de prueba
    company = Company(
        id=1,
        name="Test Company",
        address="Test Address",
        website="https://test.com",
        logo=test_logo,
    )
    session.add(company)
    session.flush()

    # Crear usuario administrador
    admin_user = User(
        id=1,
        email="admin@test.com",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
        is_admin=True,
        company_id=company.id,
    )

    # Crear usuario miembro
    member_user = User(
        id=2,
        email="user@test.com",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
        is_admin=False,
        company_id=company.id,
    )

    # Crear categorías de prueba
    categories = [
        Category(
            id=1,
            name="Category 1",
            description="Test Category 1",
            company_id=company.id,
        ),
        Category(
            id=2,
            name="Category 2",
            description="Test Category 2",
            expense_limit=100.0,
            company_id=company.id,
        ),
    ]

    session.add(admin_user)
    session.add(member_user)
    session.add_all(categories)

    session.commit()

    yield session

    # Limpiar la base de datos después de las pruebas
    session.close()


@pytest.fixture(scope="module")
def client(db):
    # Sobreescribir la dependencia para usar la base de datos de prueba
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def admin_token():
    return create_access_token(1, 1, True)


@pytest.fixture(scope="module")
def user_token():
    return create_access_token(2, 1, False)
