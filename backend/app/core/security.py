from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
import secrets
import hashlib

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Función para crear un API key
def create_api_key() -> str:
    return secrets.token_urlsafe(32)

# Función para hashear un API key
def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()

# Función para verificar un API key
def verify_api_key(plain_api_key: str, hashed_api_key: str) -> bool:
    return hash_api_key(plain_api_key) == hashed_api_key

# Función para generar un token de acceso JWT
def create_access_token(
    subject: Union[str, Any], company_id: int, is_admin: bool, expires_delta: timedelta = None
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
        "company_id": company_id,
        "is_admin": is_admin
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

# Función para verificar una contraseña
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Función para hashear una contraseña
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)