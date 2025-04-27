from typing import Optional
from pydantic import BaseModel, EmailStr
from pydantic import validator

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
    email: EmailStr | None = None
    password: str | None = None
    is_admin: bool | None = None

# Esquema para la respuesta de usuario
class User(UserBase):
    id: int
    is_active: bool
    company_id: int

    class Config:
        from_attributes = True

# Esquema para registro de usuario
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    
    @validator("password")
    def password_complexity(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/' for c in v):
            raise ValueError("Password must contain at least one special character")
        return v