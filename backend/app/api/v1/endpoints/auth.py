from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash, verify_invitation_token
from app.models.user import User
from app.models.company import Company
from app.schemas.token import Token
from app.schemas.user import User as UserSchema, UserUpdate, UserRegister

router = APIRouter()


@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email o contraseña incorrectos",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, user.company_id, user.is_admin, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_user)) -> Any:
    """
    Get current user
    """
    return current_user


@router.put("/me", response_model=UserSchema)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    password: str = Body(None),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update own user.
    """
    current_user_data = UserUpdate(password=password)

    if current_user_data.password:
        hashed_password = get_password_hash(current_user_data.password)
        current_user.hashed_password = hashed_password

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/invitation/verify/{token}", response_model=dict)
def verify_invitation_token_endpoint(
    *,
    db: Session = Depends(get_db),
    token: str,
) -> Any:
    """
    Verify an invitation token and return information about the invitation.
    """
    # Verificar el token
    email = verify_invitation_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de invitación inválido o expirado"
        )
    
    # Buscar el usuario invitado
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado. La invitación puede haber sido revocada."
        )
    
    # Verificar que el usuario no esté ya activo
    if user.is_active and user.hashed_password != "PENDING_REGISTRATION":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya completó su registro anteriormente"
        )
    
    # Obtener información de la empresa
    company = db.query(Company).filter(Company.id == user.company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada. La invitación no se puede procesar."
        )
    
    # Devolver información para la página de registro
    return {
        "valid": True,
        "email": email,
        "companyName": company.name
    }


@router.post("/invitation/accept/{token}", response_model=Token)
def accept_invitation(
    *,
    db: Session = Depends(get_db),
    token: str,
    password: str = Body(..., embed=True),
) -> Any:
    """
    Accept an invitation and set the user's password.
    """
    # Verificar el token
    email = verify_invitation_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de invitación inválido o expirado"
        )
    
    # Buscar el usuario invitado
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado. La invitación puede haber sido revocada."
        )
    
    # Verificar que el usuario no esté ya activo
    if user.is_active and user.hashed_password != "PENDING_REGISTRATION":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya completó su registro anteriormente"
        )
    
    # Actualizar la contraseña y activar la cuenta
    user.hashed_password = get_password_hash(password)
    user.is_active = True
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generar token de acceso
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, user.company_id, user.is_admin, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/register", response_model=Token)
def register_new_user(
    *,
    db: Session = Depends(get_db),
    token: str = Query(..., description="Invitation token"),
    user_in: UserRegister = Body(...),
) -> Any:
    """
    Register a new user with an invitation token.
    """
    # Verify the invitation token
    email = verify_invitation_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation token",
        )
    
    # Check if the email matches the token
    if email != user_in.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email does not match the invitation",
        )
    
    # Check if the user already exists and is active
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. The invitation may have been revoked.",
        )
    
    if user.is_active and user.hashed_password != "PENDING_REGISTRATION":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has already completed registration",
        )
    
    # Update the user with the new password
    user.hashed_password = get_password_hash(user_in.password)
    user.is_active = True
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, user.company_id, user.is_admin, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
