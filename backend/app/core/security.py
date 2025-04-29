from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt
from passlib.context import CryptContext
import secrets
import hashlib

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Función para crear un API key
def create_api_key(user_id: int, company_id: int) -> str:
    """
    Create a JWT-based API key that includes user and company information.
    The key is prefixed with "et_" to identify it as an Expense Tracker API key.
    """
    # Create payload with user and company info
    payload = {
        "sub": str(user_id),
        "company_id": company_id,
        "type": "api_key",
        # No expiration for API keys, they're valid until deleted
    }
    
    # Create JWT token
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    # Add prefix to easily identify our API keys
    return f"et_{token}"

def decode_api_key(api_key: str) -> Union[dict, None]:
    """
    Decode an API key and return the payload if valid.
    Returns None if the key is invalid.
    """
    if not api_key.startswith("et_"):
        return None
    
    # Remove the prefix
    token = api_key[3:]
    
    try:
        # Decode the token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "api_key":
            return None
        return payload
    except jwt.JWTError:
        return None

# Función para hashear un API key
def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()

# Función para verificar un API key
def verify_api_key(plain_api_key: str, hashed_api_key: str) -> bool:
    return hash_api_key(plain_api_key) == hashed_api_key

# Función para generar un token de acceso JWT
def create_access_token(
    subject: Union[str, Any], company_id: Optional[int], is_admin: bool, expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "is_admin": is_admin
    }
    
    # Solo incluir company_id si existe (los admins pueden no tener company_id)
    if company_id is not None:
        to_encode["company_id"] = company_id
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

# Función para verificar una contraseña
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Función para hashear una contraseña
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_invitation_token(email: str) -> str:
    """
    Create a JWT token that can be used for validating user invitations.
    The token includes the email and expires in 24 hours.
    """
    expires_delta = timedelta(hours=24)
    to_encode = {"exp": datetime.utcnow() + expires_delta, "sub": email, "type": "invitation"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_invitation_token(token: str) -> Union[str, None]:
    """
    Verify an invitation token and return the email if valid.
    Return None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "invitation":
            return None
        email: str = payload.get("sub")
        return email
    except jwt.JWTError:
        return None