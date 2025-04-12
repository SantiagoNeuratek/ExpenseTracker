from sqlalchemy import Column, String, Integer, DateTime, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    address = Column(String, nullable=False)
    website = Column(String, nullable=False)
    logo = Column(LargeBinary, nullable=False)  # Almacenamiento de logo en binario
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    users = relationship("User", back_populates="company")
    categories = relationship("Category", back_populates="company")
    expenses = relationship("Expense", back_populates="company")