from typing import Optional
from pydantic import BaseModel
from datetime import datetime

# Esquema base para ApiKey
class ApiKeyBase(BaseModel):
    name: str

# Esquema para crear un ApiKey
class ApiKeyCreate(ApiKeyBase):
    pass

# Esquema para la respuesta de ApiKey (sin mostrar el key completo)
class ApiKey(ApiKeyBase):
    id: int
    is_active: bool
    created_at: datetime
    key_preview: Optional[str] = None  # Versión enmascarada/truncada de la clave

    class Config:
        from_attributes = True

# Esquema para la respuesta de creación de ApiKey (incluye el key)
class ApiKeyCreateResponse(ApiKey):
    key: str
