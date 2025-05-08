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


@router.get("", response_model=List[CompanySchema])
def list_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> Any:
    """
    Obtener todas las empresas.
    Solo accesible para administradores.
    """
    companies = db.query(Company).order_by(Company.name).all()
    
    # No need to convert - logos are already stored as base64 strings
    return companies


@router.post("", response_model=CompanySchema, status_code=status.HTTP_201_CREATED)
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

    # Ensure the logo is properly handled
    logo_string = None
    if company_in.logo:
        # The logo comes in as bytes but needs to be stored as a string
        # Make sure we're not dealing with a placeholder 1x1 pixel
        try:
            # The base64 should already be decoded from the frontend
            logo_string = company_in.logo.decode('utf-8') if isinstance(company_in.logo, bytes) else company_in.logo
            
            # Validate the logo is not the empty 1x1 pixel
            if logo_string == "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==":
                logo_string = None
                print("Warning: Empty 1x1 pixel logo detected and ignored")
        except Exception as e:
            print(f"Error processing logo: {e}")
            logo_string = None

    # Crear la empresa
    company = Company(
        name=company_in.name,
        address=company_in.address,
        website=str(company_in.website),
        logo=logo_string,  # Store as string
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    
    # No need to convert the logo - it's already a string
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
    
    # No need to convert - logos are already stored as base64 strings
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
    if existing_user and existing_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya existe en el sistema",
        )

    # Create user with pending registration status
    if existing_user:
        # User exists but isn't active - update their company
        existing_user.company_id = company_id
        db.add(existing_user)
        db.commit()
        db.refresh(existing_user)
        user = existing_user
    else:
        # Create a new user with PENDING_REGISTRATION status
        user = User(
            email=email,
            hashed_password="PENDING_REGISTRATION",  # Placeholder until user completes registration
            company_id=company_id,
            is_admin=False,
            is_active=False,  # Will be set to True when they complete registration
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Enviar email de invitación
    email_sent = send_new_account_email(
        email_to=user.email,
        company_name=company.name,
        username=user.email,
        password="",  # No longer needed as we're using invitation links
    )
    
    # Respuesta con estado del envío de correo
    if email_sent:
        return {
            "status": "success", 
            "message": f"Invitación enviada exitosamente a {email}",
            "email_sent": True
        }
    else:
        # El usuario fue creado, pero el correo no se envió
        return {
            "status": "partial_success",
            "message": f"Usuario {email} creado, pero hubo un problema al enviar el correo de invitación. Verifica la configuración SMTP.",
            "email_sent": False
        }
