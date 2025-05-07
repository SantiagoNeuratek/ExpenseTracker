from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[int] = None
    company_id: Optional[int] = None
    is_admin: bool

class TokenData(BaseModel):
    id: int
    is_admin: bool
    company_id: Optional[int] = None