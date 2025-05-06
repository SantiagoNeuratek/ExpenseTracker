import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_current_admin,
    get_company_id,
    get_api_key,
    get_api_key_company
)
from app.models.user import User
from app.models.company import Company
from app.models.apikey import ApiKey
from app.core.config import settings


@pytest.fixture
def mock_db():
    """Fixture para crear un mock de la sesión de base de datos"""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_user():
    """Fixture para crear un usuario mock"""
    mock = MagicMock(spec=User)
    mock.id = 1
    mock.email = "test@example.com"
    mock.is_active = True
    mock.is_admin = False
    mock.company_id = 1
    return mock


@pytest.fixture
def mock_admin_user():
    """Fixture para crear un usuario administrador mock"""
    mock = MagicMock(spec=User)
    mock.id = 2
    mock.email = "admin@example.com"
    mock.is_active = True
    mock.is_admin = True
    mock.company_id = None
    return mock


@pytest.fixture
def mock_company():
    """Fixture para crear una empresa mock"""
    mock = MagicMock(spec=Company)
    mock.id = 1
    mock.name = "Test Company"
    return mock


@pytest.fixture
def valid_token_payload():
    """Fixture para crear un payload válido de token"""
    return {
        "sub": "1",
        "is_admin": False,
        "company_id": 1
    }


@pytest.fixture
def mock_api_key():
    """Fixture para crear un API key mock"""
    mock = MagicMock(spec=ApiKey)
    mock.id = 1
    mock.name = "Test API Key"
    mock.user_id = 1
    mock.company_id = 1
    mock.is_active = True
    mock.key_hash = "hashed_api_key"
    mock.created_at = "2023-01-01T00:00:00"
    return mock


def test_get_current_user_valid_token(mock_db, mock_user, valid_token_payload):
    """Test get_current_user con un token válido"""
    # Arrange
    token = jwt.encode(valid_token_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    
    # Act
    with patch("app.api.deps.TokenData") as mock_token_data:
        result = get_current_user(db=mock_db, token=token)
    
    # Assert
    assert result == mock_user
    mock_db.query.assert_called_once_with(User)
    mock_db.query.return_value.filter.assert_called_once()


def test_get_current_user_invalid_token(mock_db):
    """Test get_current_user con un token inválido"""
    # Arrange
    invalid_token = "invalid.token.string"
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(db=mock_db, token=invalid_token)
    
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


def test_get_current_user_nonexistent_user(mock_db, valid_token_payload):
    """Test get_current_user cuando el usuario no existe"""
    # Arrange
    token = jwt.encode(valid_token_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # Act & Assert
    with patch("app.api.deps.TokenData"):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(db=mock_db, token=token)
    
    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


def test_get_current_user_inactive_user(mock_db, valid_token_payload):
    """Test get_current_user con un usuario inactivo"""
    # Arrange
    token = jwt.encode(valid_token_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    inactive_user = MagicMock(spec=User)
    inactive_user.id = 1
    inactive_user.is_active = False
    
    mock_db.query.return_value.filter.return_value.first.return_value = inactive_user
    
    # Act & Assert
    with patch("app.api.deps.TokenData"):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(db=mock_db, token=token)
    
    assert exc_info.value.status_code == 400
    assert "Inactive user" in exc_info.value.detail


def test_get_current_admin_with_admin_user(mock_admin_user):
    """Test get_current_admin con un usuario administrador"""
    # Act
    result = get_current_admin(current_user=mock_admin_user)
    
    # Assert
    assert result == mock_admin_user


def test_get_current_admin_with_regular_user(mock_user):
    """Test get_current_admin con un usuario regular"""
    # Act & Assert
    with patch("app.api.deps.log_security_event"):
        with pytest.raises(HTTPException) as exc_info:
            get_current_admin(current_user=mock_user)
    
    assert exc_info.value.status_code == 403
    assert "No tiene permisos suficientes" in exc_info.value.detail


def test_get_company_id_regular_user(mock_user, mock_db):
    """Test get_company_id con un usuario regular"""
    # Act
    result = get_company_id(current_user=mock_user, company_id=None, db=mock_db)
    
    # Assert
    assert result == mock_user.company_id


def test_get_company_id_regular_user_no_company(mock_db):
    """Test get_company_id con un usuario regular sin empresa asignada"""
    # Arrange
    user_without_company = MagicMock(spec=User)
    user_without_company.is_admin = False
    user_without_company.company_id = None
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        get_company_id(current_user=user_without_company, company_id=None, db=mock_db)
    
    assert exc_info.value.status_code == 400
    assert "Usuario no tiene empresa asignada" in exc_info.value.detail


def test_get_company_id_admin_with_param(mock_admin_user, mock_company, mock_db):
    """Test get_company_id con un administrador y company_id proporcionado"""
    # Arrange
    company_id = 1
    mock_db.query.return_value.filter.return_value.first.return_value = mock_company
    
    # Act
    result = get_company_id(current_user=mock_admin_user, company_id=company_id, db=mock_db)
    
    # Assert
    assert result == company_id
    mock_db.query.assert_called_once_with(Company)
    mock_db.query.return_value.filter.assert_called_once()


def test_get_company_id_admin_nonexistent_company(mock_admin_user, mock_db):
    """Test get_company_id con un administrador y un company_id inexistente"""
    # Arrange
    company_id = 999
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        get_company_id(current_user=mock_admin_user, company_id=company_id, db=mock_db)
    
    assert exc_info.value.status_code == 404
    assert "Empresa no encontrada" in exc_info.value.detail


def test_get_company_id_admin_with_assigned_company(mock_db):
    """Test get_company_id con un administrador que tiene empresa asignada"""
    # Arrange
    admin_with_company = MagicMock(spec=User)
    admin_with_company.is_admin = True
    admin_with_company.company_id = 1
    
    # Act
    result = get_company_id(current_user=admin_with_company, company_id=None, db=mock_db)
    
    # Assert
    assert result == admin_with_company.company_id


def test_get_company_id_admin_without_company_param(mock_admin_user, mock_db):
    """Test get_company_id con un administrador sin empresa asignada ni parámetro"""
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        get_company_id(current_user=mock_admin_user, company_id=None, db=mock_db)
    
    assert exc_info.value.status_code == 400
    assert "Se requiere especificar company_id" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_api_key_valid(mock_db, mock_api_key):
    """Test get_api_key con una API key válida"""
    # Arrange
    api_key = "valid_api_key"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_api_key
    
    # Act
    with patch("app.api.deps.hash_api_key", return_value="hashed_api_key"):
        result = await get_api_key(db=mock_db, api_key=api_key)
    
    # Assert
    assert result["key_id"] == mock_api_key.id
    assert result["user_id"] == mock_api_key.user_id
    assert result["company_id"] == mock_api_key.company_id
    assert result["name"] == mock_api_key.name


@pytest.mark.asyncio
async def test_get_api_key_missing(mock_db):
    """Test get_api_key cuando no se proporciona una API key"""
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_api_key(db=mock_db, api_key=None)
    
    assert exc_info.value.status_code == 401
    assert "API key is missing" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_api_key_invalid(mock_db):
    """Test get_api_key con una API key inválida"""
    # Arrange
    api_key = "invalid_api_key"
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # Act & Assert
    with patch("app.api.deps.hash_api_key", return_value="hashed_api_key"):
        with pytest.raises(HTTPException) as exc_info:
            await get_api_key(db=mock_db, api_key=api_key)
    
    assert exc_info.value.status_code == 401
    assert "Invalid API key" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_api_key_company(mock_api_key):
    """Test get_api_key_company"""
    # Arrange
    api_key_data = {
        "key_id": mock_api_key.id,
        "user_id": mock_api_key.user_id,
        "company_id": mock_api_key.company_id,
        "name": mock_api_key.name,
        "created_at": mock_api_key.created_at
    }
    
    # Act
    result = get_api_key_company(api_key_data=api_key_data)
    
    # Assert
    assert result == mock_api_key.company_id 