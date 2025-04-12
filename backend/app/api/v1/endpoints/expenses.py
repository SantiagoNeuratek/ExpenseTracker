from typing import Any, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.api.deps import (
    get_db,
    get_current_user,
    get_current_admin,
    get_api_key_company,
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

router = APIRouter()


@router.get("", response_model=ExpensePagination)
def read_expenses(
    db: Session = Depends(get_db),
    start_date: date = Query(None),
    end_date: date = Query(None),
    category_id: int = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Obtener los gastos con filtros opcionales.
    """
    # Base query
    query = db.query(Expense).filter(Expense.company_id == current_user.company_id)

    # Aplicar filtros
    if start_date:
        query = query.filter(Expense.date_incurred >= start_date)
    if end_date:
        query = query.filter(Expense.date_incurred <= end_date)
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


@router.post("", response_model=ExpenseSchema)
def create_expense(
    *,
    db: Session = Depends(get_db),
    expense_in: ExpenseCreate,
    current_user: User = Depends(get_current_user),
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
                Category.company_id == current_user.company_id,
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
    if category.expense_limit and expense_in.amount > category.expense_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El monto excede el límite de gastos de la categoría ({category.expense_limit})",
        )

    # Crear el gasto
    expense = Expense(
        amount=expense_in.amount,
        date_incurred=expense_in.date_incurred,
        description=expense_in.description,
        category_id=expense_in.category_id,
        user_id=current_user.id,
        company_id=current_user.company_id,
    )

    db.add(expense)
    db.commit()
    db.refresh(expense)

    # Agregar categoría para la respuesta
    setattr(expense, "category_name", category.name)

    return expense


@router.put("/{expense_id}", response_model=ExpenseSchema)
def update_expense(
    *,
    db: Session = Depends(get_db),
    expense_id: int,
    expense_in: ExpenseUpdate,
    current_user: User = Depends(get_current_admin),  # Solo administradores
) -> Any:
    """
    Actualizar un gasto (solo administradores).
    """
    expense = (
        db.query(Expense)
        .filter(
            and_(
                Expense.id == expense_id, Expense.company_id == current_user.company_id
            )
        )
        .first()
    )

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Gasto no encontrado"
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
                    Category.company_id == current_user.company_id,
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
        if category.expense_limit and amount > category.expense_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El monto excede el límite de gastos de la categoría ({category.expense_limit})",
            )

    # Actualizar los campos
    if expense_in.amount is not None:
        expense.amount = expense_in.amount
    if expense_in.date_incurred is not None:
        expense.date_incurred = expense_in.date_incurred
    if expense_in.description is not None:
        expense.description = expense_in.description
    if expense_in.category_id is not None:
        expense.category_id = expense_in.category_id

    # Registrar auditoría
    audit = AuditRecord(
        action="update",
        previous_data=previous_data,
        user_id=current_user.id,
        expense_id=expense.id,
    )

    db.add(expense)
    db.add(audit)
    db.commit()
    db.refresh(expense)

    # Obtener el nombre de la categoría para la respuesta
    category = db.query(Category).filter(Category.id == expense.category_id).first()
    setattr(expense, "category_name", category.name if category else None)

    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_200_OK)
def delete_expense(
    *,
    db: Session = Depends(get_db),
    expense_id: int,
    current_user: User = Depends(get_current_admin),  # Solo administradores
) -> Any:
    """
    Eliminar un gasto y registrarlo en auditoría (solo administradores).
    """
    expense = (
        db.query(Expense)
        .filter(
            and_(
                Expense.id == expense_id, Expense.company_id == current_user.company_id
            )
        )
        .first()
    )

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Gasto no encontrado"
        )

    # Guardar datos para auditoría
    previous_data = {
        "amount": expense.amount,
        "date_incurred": expense.date_incurred.isoformat(),
        "description": expense.description,
        "category_id": expense.category_id,
    }

    # Registrar auditoría
    audit = AuditRecord(
        action="delete",
        previous_data=previous_data,
        user_id=current_user.id,
        expense_id=expense.id,
    )

    db.add(audit)
    db.delete(expense)
    db.commit()

    return {"status": "success", "message": "Gasto eliminado"}


@router.get("/top-categories", response_model=List[TopCategory])
def get_top_categories(
    db: Session = Depends(get_db),
    company_id: int = Depends(get_api_key_company),  # Validación con API key
) -> Any:
    """
    Obtener las 3 categorías con más gastos acumulados (endpoint público con API key).
    """
    top_categories = (
        db.query(
            Category.id, Category.name, func.sum(Expense.amount).label("total_amount")
        )
        .join(Expense, Category.id == Expense.category_id)
        .filter(and_(Category.company_id == company_id, Category.is_active == True))
        .group_by(Category.id, Category.name)
        .order_by(func.sum(Expense.amount).desc())
        .limit(3)
        .all()
    )

    # Formatear resultado
    result = [
        {"id": cat_id, "name": name, "total_amount": float(total_amount)}
        for cat_id, name, total_amount in top_categories
    ]

    return result


@router.get("/by-category", response_model=List[ExpenseSchema])
def get_expenses_by_category(
    category_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    company_id: int = Depends(get_api_key_company),  # Validación con API key
) -> Any:
    """
    Obtener gastos filtrados por categoría y rango de fechas (endpoint público con API key).
    """
    # Verificar que la categoría pertenece a la empresa
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

    # Obtener gastos
    expenses = (
        db.query(Expense)
        .filter(
            and_(
                Expense.category_id == category_id,
                Expense.company_id == company_id,
                Expense.date_incurred >= start_date,
                Expense.date_incurred <= end_date,
            )
        )
        .all()
    )

    # Agregar nombre de categoría a cada gasto
    for expense in expenses:
        setattr(expense, "category_name", category.name)

    return expenses
