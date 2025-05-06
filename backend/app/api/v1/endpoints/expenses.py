from typing import Any, List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, func

from app.api.deps import (
    get_db,
    get_current_user,
    get_current_admin,
    get_api_key_company,
    get_company_id,
)
from app.models.expense import Expense
from app.models.category import Category
from app.models.audit import AuditRecord
from app.models.user import User
from app.schemas.expense import (
    Expense as ExpenseSchema,
    ExpenseCreate,
    ExpenseUpdate,
    ExpensePagination,
)
from app.schemas.category import TopCategory
from app.services.audit_service import create_expense_audit
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=ExpensePagination)
def read_expenses(
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None, description="Fecha inicial en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha final en formato YYYY-MM-DD"),
    category_id: Optional[int] = Query(None),
    show_inactive: bool = Query(False, description="Incluir gastos inactivos/eliminados"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    company_id: int = Depends(get_company_id),
) -> Any:
    """
    Obtener los gastos con filtros opcionales.
    """
    # Base query
    query = db.query(Expense).filter(Expense.company_id == company_id)

    # Filtrar por gastos activos a menos que se solicite lo contrario
    if not show_inactive:
        query = query.filter(Expense.is_active == True)

    # Convertir strings de fecha a objetos date
    parsed_start_date = None
    parsed_end_date = None
    
    try:
        if start_date:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de fecha inválido. Use YYYY-MM-DD"
        )

    # Aplicar filtros
    if parsed_start_date:
        query = query.filter(Expense.date_incurred >= parsed_start_date)
    if parsed_end_date:
        query = query.filter(Expense.date_incurred <= parsed_end_date)
    if category_id:
        query = query.filter(Expense.category_id == category_id)

    # Contar total de registros
    total = query.count()

    # Obtener página
    expenses = (
        query.order_by(Expense.date_incurred.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Construir respuesta paginada
    response = {"total": total, "page": page, "page_size": page_size, "items": expenses}

    return response


@router.get("/top-categories", response_model=List[TopCategory])
def get_top_categories(
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None, description="Fecha inicial en formato YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Fecha final en formato YYYY-MM-DD"),
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    company_id: int = Depends(get_company_id),
) -> Any:
    """
    Obtener las categorías con más gastos en un período.
    Este endpoint implementa caché para mejorar el rendimiento bajo alta carga.
    """
    import hashlib
    import json
    from app.core.cache import cache
    from datetime import datetime, timedelta
    
    # Convertir strings de fecha a objetos date
    parsed_start_date = None
    parsed_end_date = None
    
    try:
        if start_date:
            parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de fecha inválido. Use YYYY-MM-DD"
        )
    
    # Si no se especifican fechas, usar últimos 30 días
    if parsed_start_date is None:
        parsed_start_date = datetime.now().date() - timedelta(days=30)
    if parsed_end_date is None:
        parsed_end_date = datetime.now().date()

    # Crear una clave de caché única basada en los parámetros
    cache_key = f"top_categories:{company_id}:{parsed_start_date}:{parsed_end_date}:{limit}"
    cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()
    
    # Intentar obtener resultados de caché
    cached_result = cache.get(cache_key_hash)
    if cached_result:
        logger.debug(f"Cache hit for {cache_key}")
        return json.loads(cached_result)
    
    logger.debug(f"Cache miss for {cache_key}")
    
    # Si no hay caché, ejecutar la consulta
    result = (
        db.query(
            Category.id,
            Category.name,
            func.sum(Expense.amount).label("total_amount"),
        )
        .join(Expense, Category.id == Expense.category_id)
        .filter(
            and_(
                Expense.company_id == company_id,
                Expense.date_incurred >= parsed_start_date,
                Expense.date_incurred <= parsed_end_date,
                Expense.is_active == True,
            )
        )
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Expense.amount).desc())
        .limit(limit)
        .all()
    )

    # Formatear resultados
    formatted_result = [
        {"id": row[0], "name": row[1], "total_amount": float(row[2])} for row in result
    ]
    
    # Almacenar en caché por 5 minutos (300 segundos)
    cache.set(cache_key_hash, json.dumps(formatted_result), 300)
    
    return formatted_result


@router.get("/by-category", response_model=List[ExpenseSchema])
def get_expenses_by_category(
    category_id: int,
    start_date: str = Query(..., description="Fecha inicial en formato YYYY-MM-DD"),
    end_date: str = Query(..., description="Fecha final en formato YYYY-MM-DD"),
    db: Session = Depends(get_db),
    company_id: int = Depends(get_api_key_company),
) -> Any:
    """
    Obtener gastos por categoría y período.
    Este endpoint público requiere una API KEY válida para identificar la empresa.
    """
    # Convertir strings de fecha a objetos date
    parsed_start_date = None
    parsed_end_date = None
    
    try:
        parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de fecha inválido. Use YYYY-MM-DD"
        )
    
    # Verificar que la categoría existe y pertenece a la empresa
    category = (
        db.query(Category)
        .filter(
            and_(
                Category.id == category_id,
                Category.company_id == company_id,
                Category.is_active == True,
            )
        )
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada"
        )

    # Obtener los gastos
    expenses = (
        db.query(Expense)
        .filter(
            and_(
                Expense.category_id == category_id,
                Expense.company_id == company_id,
                Expense.date_incurred >= parsed_start_date,
                Expense.date_incurred <= parsed_end_date,
                Expense.is_active == True,
            )
        )
        .order_by(Expense.date_incurred.desc())
        .all()
    )

    # Agregar categoría para la respuesta
    for expense in expenses:
        setattr(expense, "category_name", category.name)

    return expenses


@router.get("/top-categories-history", response_model=List[TopCategory])
def get_top_categories_history(
    db: Session = Depends(get_db),
    company_id: int = Depends(get_api_key_company),
    limit: int = Query(3, description="Número de categorías a devolver"),
) -> Any:
    """
    Obtener las 3 categorías con más gastos acumulados de la historia para la empresa.
    Este endpoint público requiere una API KEY válida para identificar la empresa.
    """
    result = (
        db.query(
            Category.id,
            Category.name,
            func.sum(Expense.amount).label("total_amount"),
        )
        .join(Expense, Category.id == Expense.category_id)
        .filter(
            and_(
                Expense.company_id == company_id,
                Expense.is_active == True,
            )
        )
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Expense.amount).desc())
        .limit(limit)
        .all()
    )

    return [
        {"id": row[0], "name": row[1], "total_amount": float(row[2])} for row in result
    ]


@router.get("/{expense_id}", response_model=ExpenseSchema)
def read_expense(
    *,
    db: Session = Depends(get_db),
    expense_id: int,
    current_user: User = Depends(get_current_user),
    company_id: int = Depends(get_company_id),
) -> Any:
    """
    Obtener un gasto por su ID.
    """
    expense = (
        db.query(Expense)
        .filter(
            and_(
                Expense.id == expense_id, 
                Expense.company_id == company_id,
                Expense.is_active == True
            )
        )
        .first()
    )

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Gasto no encontrado o inactivo"
        )

    # Añadir información de categoría
    category = db.query(Category).filter(Category.id == expense.category_id).first()
    setattr(expense, "category_name", category.name if category else None)

    return expense


@router.post("", response_model=ExpenseSchema)
def create_expense(
    *,
    db: Session = Depends(get_db),
    expense_in: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    company_id: int = Depends(get_company_id),
) -> Any:
    """
    Crear un nuevo gasto.
    """
    # Verificar que la categoría existe y pertenece a la empresa del usuario
    category = (
        db.query(Category)
        .filter(
            and_(
                Category.id == expense_in.category_id,
                Category.company_id == company_id,
                Category.is_active == True,
            )
        )
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada"
        )

    # Verificar límite de gastos si existe
    if category.expense_limit is not None and expense_in.amount > category.expense_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El monto excede el límite de gastos de la categoría ({category.expense_limit})",
        )

    try:
        # Crear el gasto
        expense = Expense(
            amount=expense_in.amount,
            date_incurred=expense_in.date_incurred,
            description=expense_in.description,
            category_id=expense_in.category_id,
            user_id=current_user.id,
            company_id=company_id,
        )

        db.add(expense)
        db.flush()  # Para obtener el ID generado
        
        # Preparar datos para auditoría
        new_data = {
            "amount": expense.amount,
            "date_incurred": expense.date_incurred.isoformat(),
            "description": expense.description,
            "category_id": expense.category_id,
            "is_active": expense.is_active
        }
        
        # Registrar auditoría de creación
        create_expense_audit(
            db=db,
            action="create",
            expense_id=expense.id,
            user=current_user,
            new_data=new_data
        )

        db.commit()
        db.refresh(expense)

        # Agregar categoría para la respuesta
        setattr(expense, "category_name", category.name)

        return expense
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el gasto: {str(e)}"
        )


@router.put("/{expense_id}", response_model=ExpenseSchema)
def update_expense(
    *,
    db: Session = Depends(get_db),
    expense_id: int,
    expense_in: ExpenseUpdate,
    current_user: User = Depends(get_current_admin),  # Solo administradores
    company_id: int = Depends(get_company_id),
) -> Any:
    """
    Actualizar un gasto (solo administradores).
    """
    expense = (
        db.query(Expense)
        .filter(
            and_(
                Expense.id == expense_id, 
                Expense.company_id == company_id,
                Expense.is_active == True
            )
        )
        .first()
    )

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Gasto no encontrado o inactivo"
        )

    # Guardar datos anteriores para auditoría
    previous_data = {
        "amount": expense.amount,
        "date_incurred": expense.date_incurred.isoformat(),
        "description": expense.description,
        "category_id": expense.category_id,
    }

    # Verificar categoría si se está actualizando
    if expense_in.category_id is not None:
        category = (
            db.query(Category)
            .filter(
                and_(
                    Category.id == expense_in.category_id,
                    Category.company_id == company_id,
                    Category.is_active == True,
                )
            )
            .first()
        )

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada"
            )

        # Verificar límite de gastos si cambia la categoría o el monto
        amount = expense_in.amount if expense_in.amount is not None else expense.amount
        if category.expense_limit is not None and amount > category.expense_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El monto excede el límite de gastos de la categoría ({category.expense_limit})",
            )

    try:
        # Actualizar los campos
        if expense_in.amount is not None:
            expense.amount = expense_in.amount
        if expense_in.date_incurred is not None:
            expense.date_incurred = expense_in.date_incurred
        if expense_in.description is not None:
            expense.description = expense_in.description
        if expense_in.category_id is not None:
            expense.category_id = expense_in.category_id

        # Preparar nuevos datos para auditoría
        new_data = {
            "amount": expense.amount,
            "date_incurred": expense.date_incurred.isoformat(),
            "description": expense.description,
            "category_id": expense.category_id,
        }
        
        # Registrar auditoría usando el servicio
        create_expense_audit(
            db=db,
            action="update",
            expense_id=expense.id,
            user=current_user,
            previous_data=previous_data,
            new_data=new_data
        )

        # Guardar cambios
        db.add(expense)
        db.commit()
        db.refresh(expense)

        category = db.query(Category).filter(Category.id == expense.category_id).first()
        setattr(expense, "category_name", category.name if category else None)

        return expense
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el gasto: {str(e)}"
        )


@router.delete("/{expense_id}", status_code=status.HTTP_200_OK)
def delete_expense(
    *,
    db: Session = Depends(get_db),
    expense_id: int,
    current_user: User = Depends(get_current_admin),  # Solo administradores
    company_id: int = Depends(get_company_id),
) -> Any:
    """
    Eliminar lógicamente un gasto (solo administradores).
    """
    expense = (
        db.query(Expense)
        .filter(and_(
            Expense.id == expense_id, 
            Expense.company_id == company_id,
            Expense.is_active == True
        ))
        .first()
    )

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Gasto no encontrado o ya inactivo"
        )

    # Guardar datos para auditoría
    previous_data = {
        "amount": expense.amount,
        "date_incurred": expense.date_incurred.isoformat(),
        "description": expense.description,
        "category_id": expense.category_id,
        "is_active": expense.is_active
    }

    try:
        # Marcar el gasto como inactivo en lugar de eliminarlo
        expense.is_active = False
        
        # Preparar nuevos datos para auditoría
        new_data = {
            "is_active": False
        }
        
        # Registrar auditoría usando el servicio
        create_expense_audit(
            db=db,
            action="delete",
            expense_id=expense.id,
            user=current_user,
            previous_data=previous_data,
            new_data=new_data
        )
        
        # Commit final para aplicar todos los cambios
        db.commit()
        
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar el gasto: {str(e)}"
        )
