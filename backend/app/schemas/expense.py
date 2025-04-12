from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

# Esquema base para Expense
class ExpenseBase(BaseModel):
    amount: float
    date_incurred: datetime
    description: Optional[str] = None
    category_id: int

# Esquema para crear un gasto
class ExpenseCreate(ExpenseBase):
    pass

# Esquema para actualizar un gasto
class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    date_incurred: Optional[datetime] = None
    description: Optional[str] = None
    category_id: Optional[int] = None

# Esquema para la respuesta de gasto
class Expense(ExpenseBase):
    id: int
    user_id: int
    company_id: int
    created_at: datetime
    category_name: Optional[str] = None

    class Config:
        from_attributes = True

# Esquema para respuesta de gastos paginados
class ExpensePagination(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Expense]
