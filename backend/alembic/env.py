from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Agregar el directorio padre al path de Python para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import Base
from app.models.user import User
from app.models.company import Company
from app.models.category import Category
from app.models.expense import Expense
from app.models.apikey import ApiKey
from app.models.audit import AuditRecord

# this is the Alembic Config object
config = context.config

# Configurar la URL de la base de datos desde las variables de entorno
database_url = os.environ.get("SQLALCHEMY_DATABASE_URI")
if not database_url:
    database_url = f"postgresql://{os.environ.get('POSTGRES_USER', 'postgres')}:{os.environ.get('POSTGRES_PASSWORD', 'postgres')}@{os.environ.get('POSTGRES_SERVER', 'localhost')}:5433/{os.environ.get('POSTGRES_DB', 'expense_tracker')}"

config.set_main_option("sqlalchemy.url", database_url)

# Interpreta el archivo config, que debe estar presente
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData target para 'autogenerate'
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Ejecutar migraciones en modo 'offline'.

    Necesario para ejecutar migraciones en entornos sin conexión directa a la base de datos.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Ejecutar migraciones en modo 'online'.
    """
    # Modificar la configuración para asegurar que la URL esté presente
    section = config.get_section(config.config_ini_section) or {}
    section['sqlalchemy.url'] = config.get_main_option("sqlalchemy.url")

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()