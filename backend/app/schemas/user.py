from typing import Optional
from pydantic import BaseModel, EmailStr

# Esquema base para User
class UserBase(BaseModel):
    email: EmailStr
    is_admin: bool = False

# Esquema para crear un usuario (desde la API)
class UserCreate(UserBase):
    password: str
    company_id: int

# Esquema para crear un usuario por invitación
class UserInvite(BaseModel):
    email: EmailStr

# Esquema para actualizar un usuario
class UserUpdate(BaseModel):
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

# Esquema para la respuesta de usuario
class User(UserBase):
    id: int
    is_active: bool
    company_id: int

    class Config:
        from_attributes = True