from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.api.deps import get_db, get_current_user, get_company_id
from app.models.category import Category
from app.models.user import User
from app.schemas.category import (
    Category as CategorySchema,
    CategoryCreate,
    CategoryUpdate,
)

router = APIRouter()


@router.get("", response_model=List[CategorySchema])
def read_categories(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    company_id: int = Depends(get_company_id),
) -> Any:
    """
    Retrieve categories by company.
    """
    # Mostrar solo categorías activas
    categories = (
        db.query(Category)
        .filter(
            and_(
                Category.company_id == company_id,
                Category.is_active == True,
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return categories


@router.post("", response_model=CategorySchema)
def create_category(
    *,
    db: Session = Depends(get_db),
    category_in: CategoryCreate,
    current_user: User = Depends(get_current_user),
    company_id: int = Depends(get_company_id),
) -> Any:
    """
    Crear una nueva categoría.
    """
    # Verificar si ya existe una categoría con el mismo nombre en esta empresa
    existing_category = (
        db.query(Category)
        .filter(
            and_(
                Category.name == category_in.name,
                Category.company_id == company_id,
                Category.is_active == True,
            )
        )
        .first()
    )

    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una categoría con este nombre en la empresa",
        )

    # Crear la categoría
    category = Category(
        name=category_in.name,
        description=category_in.description,
        expense_limit=category_in.expense_limit,
        company_id=company_id,
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.get("/{category_id}", response_model=CategorySchema)
def read_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    company_id: int = Depends(get_company_id),
) -> Any:
    """
    Obtener una categoría por ID.
    """
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

    return category


@router.put("/{category_id}", response_model=CategorySchema)
def update_category(
    *,
    db: Session = Depends(get_db),
    category_id: int,
    category_in: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    company_id: int = Depends(get_company_id),
) -> Any:
    """
    Actualizar una categoría.
    """
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

    # Verificar unicidad del nombre si se está actualizando
    if category_in.name and category_in.name != category.name:
        existing_category = (
            db.query(Category)
            .filter(
                and_(
                    Category.name == category_in.name,
                    Category.company_id == company_id,
                    Category.id != category_id,
                    Category.is_active == True,
                )
            )
            .first()
        )

        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una categoría con este nombre en la empresa",
            )

    # Actualizar los campos
    if category_in.name is not None:
        category.name = category_in.name
    if category_in.description is not None:
        category.description = category_in.description
    if category_in.expense_limit is not None:
        category.expense_limit = category_in.expense_limit

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.delete("/{category_id}", response_model=dict)
def delete_category(
    *,
    db: Session = Depends(get_db),
    category_id: int,
    current_user: User = Depends(get_current_user),
    company_id: int = Depends(get_company_id),
) -> Any:
    """
    Eliminación lógica de una categoría.
    """
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

    # Eliminación lógica
    category.is_active = False

    db.add(category)
    db.commit()
    db.refresh(category)

    return {"message": "Categoría eliminada"}
