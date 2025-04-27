from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Boolean, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    expense_limit = Column(Float, nullable=True)  # Límite de gasto opcional por categoría
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    company = relationship("Company", back_populates="categories")
    expenses = relationship("Expense", back_populates="category")
    
    # Indexes for better query performance
    __table_args__ = (
        # Composite index for filtering active categories by company
        Index('ix_categories_company_active', company_id, is_active),
        
        # Index for name uniqueness check within company (common validation query)
        Index('ix_categories_company_name', company_id, name, unique=True),
    )