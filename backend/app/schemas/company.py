from typing import Optional
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime

# Esquema base para Company
class CompanyBase(BaseModel):
    name: str
    address: str
    website: HttpUrl

# Esquema para crear una empresa
class CompanyCreate(CompanyBase):
    logo: Optional[str] = Field(None, description="Base64 encoded logo as string (without data:image prefix)")

# Esquema para actualizar una empresa
class CompanyUpdate(CompanyBase):
    name: Optional[str] = None
    address: Optional[str] = None
    website: Optional[HttpUrl] = None
    logo: Optional[str] = None

# Esquema para la respuesta de empresa
class Company(CompanyBase):
    id: int
    created_at: datetime
    logo: Optional[str] = None  # Base64 encoded string

    class Config:
        from_attributes = True