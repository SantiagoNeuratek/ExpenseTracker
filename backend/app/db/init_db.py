import logging
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.company import Company
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    """
    Inicializar la base de datos con datos mínimos necesarios.
    """
    # Crear usuario admin si no existe
    admin_user = db.query(User).filter(User.email == "admin@saas.com").first()

    if not admin_user:
        logger.info("Creando usuario administrador por defecto...")

        # Primero, crear la empresa ORT
        company = db.query(Company).filter(Company.name == "ORT").first()

        if not company:
            logger.info("Creando empresa ORT por defecto...")
            # Logo como bytes (en un entorno real sería una imagen)
            default_logo = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

            company = Company(
                name="ORT",
                address="Cuareim 1451",
                website="https://www.ort.edu.uy",
                logo=default_logo,
            )
            db.add(company)
            db.flush()
        
        # Crear usuario admin
        admin_user = User(
            email="admin@saas.com",
            hashed_password=get_password_hash("Password1"),
            is_admin=True,
            company_id=company.id,
        )
        db.add(admin_user)

        # Crear usuario miembro
        member_user = User(
            email="usuario@ort.com",
            hashed_password=get_password_hash("Password1"),
            is_admin=False,
            company_id=company.id,
        )
        db.add(member_user)

        db.commit()
        logger.info("Base de datos inicializada correctamente.")
