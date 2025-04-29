from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.models.audit import AuditRecord
from app.models.user import User

def create_audit_record(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: int,
    user_id: int,
    previous_data: Optional[Dict[str, Any]] = None,
    new_data: Optional[Dict[str, Any]] = None,
    expense_id: Optional[int] = None,
) -> AuditRecord:
    """
    Crear un registro de auditoría.
    
    Args:
        db: Sesión de base de datos
        action: Acción realizada (create, update, delete)
        entity_type: Tipo de entidad (expense, category, etc.)
        entity_id: ID de la entidad
        user_id: ID del usuario que realizó la acción
        previous_data: Datos anteriores para update/delete
        new_data: Nuevos datos para create/update
        expense_id: ID del gasto (para mantener compatibilidad)
        
    Returns:
        Registro de auditoría creado
    """
    audit_record = AuditRecord(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        previous_data=previous_data,
        new_data=new_data,
        expense_id=expense_id if entity_type == "expense" else None,
    )
    
    db.add(audit_record)
    db.flush()  # Asegurar que se crea el ID
    
    return audit_record


def create_expense_audit(
    db: Session,
    action: str,
    expense_id: int,
    user: User,
    previous_data: Optional[Dict[str, Any]] = None,
    new_data: Optional[Dict[str, Any]] = None,
) -> AuditRecord:
    """
    Función de utilidad para auditar operaciones en gastos.
    
    Args:
        db: Sesión de base de datos
        action: Acción realizada (create, update, delete)
        expense_id: ID del gasto
        user: Usuario que realizó la acción
        previous_data: Datos anteriores
        new_data: Nuevos datos
        
    Returns:
        Registro de auditoría creado
    """
    return create_audit_record(
        db=db,
        action=action,
        entity_type="expense",
        entity_id=expense_id,
        user_id=user.id,
        previous_data=previous_data,
        new_data=new_data,
        expense_id=expense_id,
    ) 