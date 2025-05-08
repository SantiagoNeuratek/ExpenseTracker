import logging
import subprocess
import os
import base64
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.company import Company
from app.models.category import Category
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    """
    Inicializar la base de datos con datos mínimos necesarios.
    
    Esta función:
    1. Verifica y ejecuta migraciones si las tablas no existen
    2. Crea una empresa de demostración (ORT) si no existe
    3. Crea categorías de gastos predeterminadas para la empresa
    4. Crea usuarios de demostración (admin global y usuario regular)
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

    try:
        # Crear usuario admin si no existe
        admin_user = db.query(User).filter(User.email == "admin@saas.com").first()

        if not admin_user:
            logger.info("Creando usuario administrador por defecto...")

            # Primero, crear la empresa ORT
            company = db.query(Company).filter(Company.name == "ORT").first()

            if not company:
                logger.info("Creando empresa ORT por defecto...")
                # Logo como base64 string (para cumplir con la definición del modelo)
                default_logo_bytes = b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                default_logo = base64.b64encode(default_logo_bytes).decode('utf-8')

                company = Company(
                    name="ORT",
                    address="Cuareim 1451",
                    website="https://www.ort.edu.uy",
                    logo=default_logo,
                )
                db.add(company)
                db.flush()
                logger.info(f"Empresa ORT creada con ID: {company.id}")
                
                # Crear categorías predeterminadas para la empresa
                default_categories = [
                    {"name": "Viáticos", "description": "Gastos de viaje y transporte", "expense_limit": 5000.0},
                    {"name": "Oficina", "description": "Materiales y suministros de oficina", "expense_limit": 2000.0},
                    {"name": "Alimentación", "description": "Comidas y bebidas", "expense_limit": 1500.0},
                    {"name": "Tecnología", "description": "Equipos y servicios tecnológicos", "expense_limit": 10000.0},
                    {"name": "Marketing", "description": "Publicidad y promoción", "expense_limit": 3000.0},
                    {"name": "Otros", "description": "Gastos varios no categorizados", "expense_limit": None},
                ]
                
                for cat_data in default_categories:
                    category = Category(
                        name=cat_data["name"],
                        description=cat_data["description"],
                        expense_limit=cat_data["expense_limit"],
                        company_id=company.id,
                        is_active=True
                    )
                    db.add(category)
                logger.info(f"Categorías predeterminadas creadas para empresa ORT")
            
            # Crear usuario admin sin company_id (administrador global)
            admin_user = User(
                email="admin@saas.com",
                hashed_password=get_password_hash("Password1"),
                is_admin=True,
                company_id=None,  # Admin global sin empresa asignada
            )
            db.add(admin_user)
            logger.info("Usuario administrador global creado")

            # Crear usuario miembro asociado a ORT
            member_user = User(
                email="usuario@ort.com",
                hashed_password=get_password_hash("Password1"),
                is_admin=False,
                company_id=company.id,
            )
            db.add(member_user)
            logger.info("Usuario regular para empresa ORT creado")

            db.commit()
            logger.info("Base de datos inicializada correctamente.")
        else:
            logger.info("La base de datos ya está inicializada con datos por defecto.")
    except Exception as e:
        db.rollback()
        logger.exception(f"Error al inicializar datos: {str(e)}")
