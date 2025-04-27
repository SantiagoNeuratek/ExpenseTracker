import logging
import subprocess
import os
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.company import Company
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    """
    Inicializar la base de datos con datos mínimos necesarios.
    """
    # Run migrations first
    try:
        logger.info("Running database migrations...")
        # Check if tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.bind)
        if not inspector.has_table('users'):
            logger.info("Tables don't exist. Running migrations with alembic...")
            alembic_ini_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'alembic.ini')
            migrations_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'alembic')
            
            if os.path.exists(alembic_ini_path) and os.path.exists(migrations_dir):
                logger.info(f"Alembic config found at {alembic_ini_path}")
                
                # Set environment variables for Alembic to use 'db' as the hostname
                os.environ["POSTGRES_SERVER"] = "db"
                
                # Run migrations
                result = subprocess.run(
                    ["alembic", "upgrade", "head"], 
                    cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    capture_output=True,
                    text=True,
                    env=dict(os.environ)
                )
                logger.info(f"Migration stdout: {result.stdout}")
                if result.stderr:
                    logger.error(f"Migration stderr: {result.stderr}")
                
                # Reconnect to get updated schema
                db.commit()
                
                # Verify tables now exist
                inspector = inspect(db.bind)
                if not inspector.has_table('users'):
                    logger.error("Tables still don't exist after migration!")
                    return
            else:
                logger.error(f"Alembic files not found at {alembic_ini_path}")
                return
    except Exception as e:
        logger.exception(f"Error running migrations: {str(e)}")
        return

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
