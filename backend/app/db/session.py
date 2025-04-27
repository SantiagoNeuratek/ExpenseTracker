from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

from app.core.config import settings

# Explicitly build the connection string from individual components
db_user = os.getenv("POSTGRES_USER", settings.POSTGRES_USER)
db_password = os.getenv("POSTGRES_PASSWORD", settings.POSTGRES_PASSWORD)
db_server = os.getenv("POSTGRES_SERVER", settings.POSTGRES_SERVER)
db_name = os.getenv("POSTGRES_DB", settings.POSTGRES_DB)

# Explicitly set db_server to 'db' if running in Docker (which is the default)
if not db_server or db_server == "localhost":
    db_server = "db"

SQLALCHEMY_DATABASE_URI = f"postgresql://{db_user}:{db_password}@{db_server}:5432/{db_name}"

engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Utility para obtener una sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()