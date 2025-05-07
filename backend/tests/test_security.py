import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
import time
from jose import jwt
import hashlib
from app.core.security import (
    create_api_key,
    decode_api_key,
    hash_api_key,
    verify_api_key,
    create_access_token,
    verify_password,
    get_password_hash,
    create_invitation_token,
    verify_invitation_token
)
from app.core.config import settings


def test_create_api_key():
    """Test creating an API key"""
    # Arrange
    user_id = 123
    company_id = 456
    
    # Act
    api_key = create_api_key(user_id, company_id)
    
    # Assert
    assert api_key.startswith("et_")
    
    # Verify the API key can be decoded
    payload = decode_api_key(api_key)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["company_id"] == company_id
    assert payload["type"] == "api_key"


def test_decode_api_key_invalid_prefix():
    """Test decoding API key with invalid prefix"""
    # Arrange
    token = jwt.encode({"sub": "1", "company_id": 1, "type": "api_key"}, settings.SECRET_KEY, algorithm="HS256")
    invalid_api_key = f"invalid_{token}"
    
    # Act
    payload = decode_api_key(invalid_api_key)
    
    # Assert
    assert payload is None


def test_decode_api_key_invalid_token():
    """Test decoding invalid API key token"""
    # Arrange
    invalid_token = "et_invalid.token.string"
    
    # Act
    payload = decode_api_key(invalid_token)
    
    # Assert
    assert payload is None


def test_decode_api_key_invalid_type():
    """Test decoding API key with valid JWT but incorrect type"""
    # Arrange
    token = jwt.encode({"sub": "1", "company_id": 1, "type": "not_api_key"}, settings.SECRET_KEY, algorithm="HS256")
    api_key = f"et_{token}"
    
    # Act
    payload = decode_api_key(api_key)
    
    # Assert
    assert payload is None


def test_hash_api_key():
    """Test hashing API key"""
    # Arrange
    api_key = "et_sample_api_key"
    
    # Act
    hashed_key = hash_api_key(api_key)
    
    # Assert
    assert isinstance(hashed_key, str)
    assert len(hashed_key) > 0
    assert hashed_key != api_key


def test_verify_api_key():
    """Test verifying API key against hashed key"""
    # Arrange
    api_key = "et_sample_api_key"
    hashed_key = hash_api_key(api_key)
    
    # Act & Assert
    assert verify_api_key(api_key, hashed_key) is True
    assert verify_api_key("wrong_api_key", hashed_key) is False


def test_create_access_token_custom_expiry():
    """Test creating access token with custom expiry"""
    # Arrange
    user_id = 123
    company_id = 456
    is_admin = True
    expires_delta = timedelta(minutes=30)
    
    # Act
    token = create_access_token(user_id, company_id, is_admin, expires_delta)
    
    # Assert
    assert token is not None
    
    # Verify token contents
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == str(user_id)
    assert payload["company_id"] == company_id
    assert payload["is_admin"] is True
    
    # Solo verificamos que existe una fecha de expiración
    assert "exp" in payload
    
    # Check expiry is in the future (más de 29 minutos desde ahora)
    exp_time = datetime.fromtimestamp(payload["exp"])
    now = datetime.now()
    time_diff = exp_time - now
    assert time_diff.total_seconds() > 29 * 60  # Al menos 29 minutos


def test_create_access_token_default_expiry():
    """Test creating access token with default expiry"""
    # Arrange
    user_id = 123
    company_id = 456
    is_admin = False
    
    # Act
    token = create_access_token(user_id, company_id, is_admin)
    
    # Assert
    assert token is not None
    
    # Verify token contents
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == str(user_id)
    assert payload["company_id"] == company_id
    assert payload["is_admin"] is False
    
    # Check expiry exists
    assert "exp" in payload


def test_create_access_token_for_admin_without_company():
    """Test creating access token for admin without company ID"""
    # Arrange
    user_id = 123
    company_id = None  # Admin sin empresa
    is_admin = True
    
    # Act
    token = create_access_token(user_id, company_id, is_admin)
    
    # Assert
    assert token is not None
    
    # Verify token contents
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == str(user_id)
    assert "company_id" not in payload  # No debe incluir company_id
    assert payload["is_admin"] is True


def test_password_hashing_and_verification():
    """Test password hashing and verification"""
    # Arrange
    password = "secure_password123"
    
    # Act
    hashed_password = get_password_hash(password)
    
    # Assert
    assert hashed_password != password
    assert verify_password(password, hashed_password) is True
    assert verify_password("wrong_password", hashed_password) is False


def test_create_and_verify_invitation_token():
    """Test creating and verifying invitation token"""
    # Arrange
    email = "test@example.com"
    
    # Act
    token = create_invitation_token(email)
    verified_email = verify_invitation_token(token)
    
    # Assert
    assert token is not None
    assert verified_email == email


def test_verify_invitation_token_invalid():
    """Test verifying invalid invitation token"""
    # Arrange
    invalid_token = "invalid.token.string"
    
    # Act
    result = verify_invitation_token(invalid_token)
    
    # Assert
    assert result is None


def test_verify_invitation_token_wrong_type():
    """Test verifying token with wrong type"""
    # Arrange
    email = "test@example.com"
    expires = datetime.utcnow() + timedelta(hours=24)
    payload = {"exp": expires, "sub": email, "type": "not_invitation"}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    # Act
    result = verify_invitation_token(token)
    
    # Assert
    assert result is None 