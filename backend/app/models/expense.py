from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    date_incurred = Column(DateTime(timezone=True), nullable=False)  # Fecha en que se produjo el gasto
    description = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Usuario que registra
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Fecha de registro
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    category = relationship("Category", back_populates="expenses")
    user = relationship("User", back_populates="expenses")
    company = relationship("Company", back_populates="expenses")
    audit_records = relationship("AuditRecord", back_populates="expense")

    # Indexes for better query performance
    __table_args__ = (
        # Composite index for filtering by company and date range (common query pattern)
        Index('ix_expenses_company_date', company_id, date_incurred),
        
        # Composite index for filtering by company and category (for category expense reports)
        Index('ix_expenses_company_category', company_id, category_id),
        
        # Composite index for filtering by all common dimensions (for detailed filtering)
        Index('ix_expenses_company_category_date', company_id, category_id, date_incurred),
    )