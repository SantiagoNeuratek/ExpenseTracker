from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, or_, String

from app.api.deps import get_db, get_current_admin, get_company_id
from app.models.audit import AuditRecord
from app.models.user import User
from app.models.expense import Expense
from app.models.category import Category
from app.schemas.audit import AuditRecord as AuditRecordSchema
from app.schemas.audit import AuditRecordPagination
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("", response_model=AuditRecordPagination)
def read_audit_records(
    db: Session = Depends(get_db),
    entity_type: Optional[str] = Query(None, description="Filtrar por tipo de entidad (expense, category, etc.)"),
    action: Optional[str] = Query(None, description="Filtrar por acción (create, update, delete)"),
    user_id: Optional[int] = Query(None, description="Filtrar por ID de usuario"),
    start_date: Optional[str] = Query(None, description="Fecha inicial en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha final en formato YYYY-MM-DD"),
    search: Optional[str] = Query(None, description="Buscar en los datos de entidad"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_admin),  # Solo admins
    company_id: int = Depends(get_company_id),
) -> Any:
    """
    Obtener registros de auditoría con filtros opcionales.
    Solo accesible para administradores.
    """
    from datetime import datetime, timedelta

    # Base query
    query = db.query(AuditRecord)

    # Convertir strings de fecha a objetos date
    parsed_start_date = None
    parsed_end_date = None
    
    try:
        if start_date:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            # Ajustar para incluir todo el día
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de fecha inválido. Use YYYY-MM-DD"
        )

    # Aplicar filtros
    if entity_type:
        query = query.filter(AuditRecord.entity_type == entity_type)
    if action:
        query = query.filter(AuditRecord.action == action)
    if user_id:
        query = query.filter(AuditRecord.user_id == user_id)
    if parsed_start_date:
        query = query.filter(AuditRecord.created_at >= parsed_start_date)
    if parsed_end_date:
        query = query.filter(AuditRecord.created_at <= parsed_end_date)
    
    # Filtrado por texto en datos JSON si se proporciona búsqueda
    if search and search.strip():
        search_term = f"%{search.lower()}%"
        # Buscar coincidencias aproximadas en los datos JSON
        query = query.filter(
            or_(
                AuditRecord.previous_data.cast(String).ilike(search_term),
                AuditRecord.new_data.cast(String).ilike(search_term)
            )
        )
    
    # Esto asume que queremos restringir los registros de auditoría a una empresa específica
    # Si los registros de auditoría no tienen una relación directa con la empresa, podría necesitar filtro adicional
    
    # Para gastos, filtrar por empresa a través de la relación con gastos
    expenses_subquery = db.query(Expense.id).filter(Expense.company_id == company_id).subquery()
    
    query = query.filter(
        # Registros de auditoría para gastos de esta empresa
        or_(
            and_(
                AuditRecord.entity_type == "expense",
                AuditRecord.entity_id.in_(expenses_subquery)
            ),
            # Incluir otros tipos de entidades según sea necesario
            # Por ejemplo, categorías, API keys, etc. que pertenezcan a esta empresa
            and_(
                AuditRecord.entity_type == "category",
                # Aquí iría una subconsulta similar para categorías
            )
        )
    )
    
    # Ordenar por fecha de creación (más reciente primero)
    query = query.order_by(desc(AuditRecord.created_at))
    
    # Contar el total para la paginación
    total = query.count()
    
    # Aplicar paginación
    records = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Enriquecer los registros con información adicional
    enriched_records = []
    for record in records:
        # Obtener el email del usuario que realizó la acción
        user = db.query(User).filter(User.id == record.user_id).first()
        user_email = user.email if user else "Usuario desconocido"
        
        # Añadir atributos
        setattr(record, "user_email", user_email)
        
        # Obtener descripción de la entidad según el tipo
        entity_description = "No disponible"
        if record.entity_type == "expense" and record.expense_id:
            expense = db.query(Expense).filter(Expense.id == record.expense_id).first()
            if expense:
                entity_description = expense.description or f"Gasto #{expense.id}"
            elif record.new_data and "description" in record.new_data:
                entity_description = record.new_data.get("description") or f"Gasto #{record.entity_id}"
            elif record.previous_data and "description" in record.previous_data:
                entity_description = record.previous_data.get("description") or f"Gasto #{record.entity_id}"
        elif record.entity_type == "category":
            # Similar lógica para categorías
            # Busca la categoría o usa los datos almacenados en los datos de auditoría
            category_id = record.entity_id
            category = db.query(Category).filter(Category.id == category_id).first()
            if category:
                entity_description = category.name
            elif record.new_data and "name" in record.new_data:
                entity_description = record.new_data.get("name") or f"Categoría #{category_id}"
            elif record.previous_data and "name" in record.previous_data:
                entity_description = record.previous_data.get("name") or f"Categoría #{category_id}"
        
        setattr(record, "entity_description", entity_description)
        enriched_records.append(record)
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": enriched_records
    }

@router.get("/actions", response_model=List[str])
def get_audit_actions(
    current_user: User = Depends(get_current_admin),  # Solo admins
) -> Any:
    """
    Obtener lista de acciones de auditoría disponibles.
    """
    return ["create", "update", "delete"]

@router.get("/entity-types", response_model=List[str])
def get_entity_types(
    current_user: User = Depends(get_current_admin),  # Solo admins
) -> Any:
    """
    Obtener lista de tipos de entidades disponibles.
    """
    return ["expense", "category"]  # Ampliar con otros tipos según sea necesario

@router.get("/{record_id}", response_model=AuditRecordSchema)
def read_audit_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),  # Solo admins
) -> Any:
    """
    Obtener un registro de auditoría por ID.
    """
    record = db.query(AuditRecord).filter(AuditRecord.id == record_id).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de auditoría no encontrado"
        )
    
    # Obtener el email del usuario que realizó la acción
    user = db.query(User).filter(User.id == record.user_id).first()
    user_email = user.email if user else "Usuario desconocido"
    
    # Añadir atributos adicionales
    setattr(record, "user_email", user_email)
    
    # Obtener descripción de la entidad según el tipo
    entity_description = "No disponible"
    if record.entity_type == "expense" and record.expense_id:
        expense = db.query(Expense).filter(Expense.id == record.expense_id).first()
        if expense:
            entity_description = expense.description or f"Gasto #{expense.id}"
    elif record.entity_type == "category":
        # Similar lógica para categorías
        category_id = record.entity_id
        category = db.query(Category).filter(Category.id == category_id).first()
        if category:
            entity_description = category.name
    
    setattr(record, "entity_description", entity_description)
    
    return record 