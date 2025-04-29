from typing import Generator, Optional
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
from app.schemas.token import TokenPayload
from app.core.logging import set_user_id, set_company_id, log_security_event, get_logger

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

# Dependencia para obtener el usuario actual (autenticado con JWT)
def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError) as e:
        log_security_event(
            logger, 
            "auth_failed", 
            message="Token validation failed", 
            data={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo validar las credenciales",
        )
    
    user = db.query(User).filter(User.id == token_data.sub).first()
    if not user:
        log_security_event(
            logger, 
            "auth_failed", 
            message="User not found", 
            data={"user_id": token_data.sub}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    if not user.is_active:
        log_security_event(
            logger, 
            "auth_failed", 
            user_id=user.id,
            message="Inactive user", 
            data={"company_id": user.company_id}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Usuario inactivo"
        )
    
    # Set user and company ID in the logging context
    set_user_id(user.id)
    if user.company_id is not None:
        set_company_id(user.company_id)
    
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
def get_api_key_company(
    api_key: str = Header(..., description="API Key for authentication")
) -> int:
    """
    Dependency to validate API key and return the associated company_id.
    """
    # Decode the JWT API key
    payload = decode_api_key(api_key)
    if not payload:
        log_security_event(
            logger, 
            "api_key_invalid", 
            message="Invalid API key format"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Get company_id from payload
    company_id = payload.get("company_id")
    user_id = payload.get("sub")
    
    if not company_id:
        log_security_event(
            logger, 
            "api_key_invalid", 
            message="Missing company_id in API key",
            data={"user_id": user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid API Key format",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Get DB session to verify the key exists and is active
    db = SessionLocal()
    try:
        # Hash the API key to find it in the database
        api_key_hash = hash_api_key(api_key)
        api_key_record = (
            db.query(ApiKey)
            .filter(ApiKey.key_hash == api_key_hash, ApiKey.is_active == True)
            .first()
        )
        
        if not api_key_record:
            log_security_event(
                logger, 
                "api_key_inactive", 
                user_id=int(user_id) if user_id else None,
                message="API Key not found or inactive", 
                data={"company_id": company_id}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key not found or inactive",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        # Set company ID in the logging context
        set_company_id(company_id)
        if user_id:
            set_user_id(int(user_id))
        
        return company_id
    finally:
        db.close()