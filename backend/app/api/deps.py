from typing import Any, Dict, List, Optional, Callable, Generator, Union
from fastapi import Depends, HTTPException, status, Header, Query
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.db.session import get_db, SessionLocal
from app.models.user import User
from app.models.company import Company
from app.models.apikey import ApiKey
from app.core.config import settings
from app.core.security import verify_api_key, decode_api_key, hash_api_key
from app.schemas.token import TokenPayload, TokenData
from app.core.logging import set_user_id, set_company_id, log_security_event, get_logger

ALGORITHM = "HS256"

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

# Dependencia para obtener el usuario actual (autenticado con JWT)
def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Obtiene el usuario actual a partir del token JWT.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenData(
            id=int(payload.get("sub")),
            is_admin=payload.get("is_admin", False),
            company_id=payload.get("company_id"),
        )
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == token_data.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return user

# Dependencia para validar que el usuario sea administrador
def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_admin:
        log_security_event(
            logger, 
            "permission_denied", 
            user_id=current_user.id,
            message="Admin access required", 
            data={"company_id": current_user.company_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos suficientes"
        )
    return current_user

# Obtener el company_id del usuario o de un parámetro de consulta
def get_company_id(
    current_user: User = Depends(get_current_user),
    company_id: Optional[int] = Query(None, description="ID de la empresa (solo para administradores)"),
    db: Session = Depends(get_db)
) -> int:
    """
    Determina la empresa actual para la operación.
    - Para usuarios no administradores, usa su company_id asignado.
    - Para administradores, permite especificar un company_id como parámetro de consulta.
    """
    # Si no es admin, solo puede usar su propia empresa
    if not current_user.is_admin:
        if not current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario no tiene empresa asignada"
            )
        return current_user.company_id
    
    # Para administradores, verificar el company_id proporcionado
    if company_id:
        # Verificar que la empresa existe
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada"
            )
        return company_id
    
    # Si el admin no proporciona company_id y tiene uno asignado, usarlo
    if current_user.company_id:
        return current_user.company_id
    
    # Si admin no tiene company_id asignado y no se proporcionó uno, error
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Se requiere especificar company_id para esta operación"
    )

# Dependencia para validar API Key
async def get_api_key(
    db: Session = Depends(get_db),
    api_key: str = Header(None, alias="api-key"),
) -> Dict[str, Any]:
    """
    Verify and return API key details from header.
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
        )
    
    # Hash the API key for comparison with stored hashes
    key_hash = hash_api_key(api_key)
    
    # Find the key in the database
    db_key = db.query(ApiKey).filter(
        ApiKey.key_hash == key_hash,
        ApiKey.is_active == True,
    ).first()
    
    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    # API key found and is valid
    key_data = {
        "key_id": db_key.id,
        "user_id": db_key.user_id,
        "company_id": db_key.company_id,
        "created_at": db_key.created_at,
        "name": db_key.name,
    }
    
    return key_data

# Función auxiliar para extraer el company_id de un API key
def get_api_key_company(api_key_data: Dict[str, Any] = Depends(get_api_key)) -> int:
    """
    Extrae el company_id de un API key validado.
    Para usar en endpoints públicos que requieren identificar la empresa del cliente.
    """
    return api_key_data["company_id"]