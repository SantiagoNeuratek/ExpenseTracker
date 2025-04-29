from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base

class AuditRecord(Base):
    __tablename__ = "audit_records"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False)  # "create", "update", "delete"
    entity_type = Column(String, nullable=False)  # Tipo de entidad: "expense", "category", etc.
    entity_id = Column(Integer, nullable=False)  # ID de la entidad
    previous_data = Column(JSON, nullable=True)  # Datos anteriores en caso de update/delete
    new_data = Column(JSON, nullable=True)  # Nuevos datos en caso de create/update
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    expense = relationship("Expense", back_populates="audit_records")
    
    def __repr__(self):
        return f"<AuditRecord(id={self.id}, action={self.action}, entity_type={self.entity_type}, entity_id={self.entity_id})>"