from typing import Optional
from pydantic import BaseModel, HttpUrl
from datetime import datetime

# Esquema base para Company
class CompanyBase(BaseModel):
    name: str
    address: str
    website: HttpUrl

# Esquema para crear una empresa
class CompanyCreate(CompanyBase):
    logo: bytes  # Base64 encoded logo

# Esquema para actualizar una empresa
class CompanyUpdate(CompanyBase):
    name: Optional[str] = None
    address: Optional[str] = None
    website: Optional[HttpUrl] = None
    logo: Optional[bytes] = None

# Esquema para la respuesta de empresa
class Company(CompanyBase):
    id: int
    created_at: datetime
    logo: Optional[str] = None  # URL o base64 para frontend

    class Config:
        from_attributes = True