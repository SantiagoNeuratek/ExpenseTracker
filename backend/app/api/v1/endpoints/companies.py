from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Body, File, UploadFile
from sqlalchemy.orm import Session
import base64

from app.api.deps import get_db, get_current_admin, get_current_user
from app.models.company import Company
from app.models.user import User
from app.core.security import get_password_hash
from app.schemas.company import Company as CompanySchema, CompanyCreate
from app.schemas.user import UserCreate
from app.utils.email import send_new_account_email

router = APIRouter()


@router.post("", response_model=CompanySchema)
def create_company(
    *,
    db: Session = Depends(get_db),
    company_in: CompanyCreate,
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Crear una nueva empresa.
    """
    # Verificar si existe otra empresa con el mismo nombre
    db_company = db.query(Company).filter(Company.name == company_in.name).first()
    if db_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una empresa con este nombre.",
        )

    # Crear la empresa
    company = Company(
        name=company_in.name,
        address=company_in.address,
        website=str(company_in.website),
        logo=company_in.logo,
    )
    db.add(company)
    db.commit()
    db.refresh(company)

    return company


@router.get("/{company_id}", response_model=CompanySchema)
def read_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Obtener una empresa por ID.
    """
    # Solo se puede acceder a la empresa a la que pertenece el usuario
    if current_user.company_id != company_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para acceder a esta empresa",
        )

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada"
        )

    return company


@router.post("/{company_id}/invite", status_code=status.HTTP_201_CREATED)
def invite_user(
    company_id: int,
    email: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Invitar a un usuario a la empresa.
    """
    # Verificar que la empresa existe
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada"
        )

    # Verificar que el usuario no exista ya
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya existe en el sistema",
        )

    # Generar una contraseña temporal
    temp_password = (
        "ChangeMe123!"  # En producción, usar algo como secrets.token_urlsafe(8)
    )

    # Crear usuario con contraseña temporal
    user_in = UserCreate(
        email=email, password=temp_password, company_id=company_id, is_admin=False
    )

    # Crear usuario en base de datos
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        company_id=user_in.company_id,
        is_admin=user_in.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Enviar email de invitación
    send_new_account_email(
        email_to=user.email,
        company_name=company.name,
        username=user.email,
        password=temp_password,
    )

    return {"status": "success", "message": f"Invitación enviada a {email}"}
