from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

from app.core.config import settings

# Use the full database URL from environment if available, otherwise build from components
SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
if not SQLALCHEMY_DATABASE_URI:
    db_user = os.getenv("POSTGRES_USER", settings.POSTGRES_USER)
    db_password = os.getenv("POSTGRES_PASSWORD", settings.POSTGRES_PASSWORD)
    db_server = os.getenv("POSTGRES_SERVER", settings.POSTGRES_SERVER)
    db_name = os.getenv("POSTGRES_DB", settings.POSTGRES_DB)
    
    # Use port 5432 for PostgreSQL within Docker networking, 5433 only for localhost connections
    db_port = "5432"
    if db_server == "localhost":
        db_port = "5433"
        
    SQLALCHEMY_DATABASE_URI = f"postgresql://{db_user}:{db_password}@{db_server}:{db_port}/{db_name}"

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