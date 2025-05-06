from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

# Esquema base para AuditRecord
class AuditRecordBase(BaseModel):
    action: str
    entity_type: str
    entity_id: int
    previous_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None

# Esquema para la respuesta de auditoría
class AuditRecord(AuditRecordBase):
    id: int
    user_id: int
    expense_id: Optional[int] = None
    created_at: datetime
    
    # Usuario que realizó la acción (se agregará en la respuesta)
    user_email: Optional[str] = None
    entity_description: Optional[str] = None  # Descripción de la entidad (ej: nombre de categoría, descripción de gasto)

    class Config:
        from_attributes = True

# Esquema para paginación de registros de auditoría
class AuditRecordPagination(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AuditRecord] 