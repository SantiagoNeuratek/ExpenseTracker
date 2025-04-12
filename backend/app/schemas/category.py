from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

# Esquema base para Category
class CategoryBase(BaseModel):
    name: str
    description: str
    expense_limit: Optional[float] = None

# Esquema para crear una categoría
class CategoryCreate(CategoryBase):
    pass

# Esquema para actualizar una categoría
class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    expense_limit: Optional[float] = None
    is_active: Optional[bool] = None

# Esquema para la respuesta de categoría
class Category(CategoryBase):
    id: int
    company_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Esquema para top categorías
class TopCategory(BaseModel):
    id: int
    name: str
    total_amount: float