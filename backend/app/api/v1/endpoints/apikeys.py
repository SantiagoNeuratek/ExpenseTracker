from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.api.deps import get_db, get_current_user
from app.models.apikey import ApiKey
from app.models.user import User
from app.core.security import create_api_key, hash_api_key
from app.schemas.apikey import (
    ApiKey as ApiKeySchema,
    ApiKeyCreate,
    ApiKeyCreateResponse,
)

router = APIRouter()


@router.get("", response_model=List[ApiKeySchema])
def read_api_keys(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtener todas las API keys del usuario.
    """
    api_keys = (
        db.query(ApiKey)
        .filter(and_(ApiKey.user_id == current_user.id, ApiKey.is_active == True))
        .all()
    )
    return api_keys


@router.post("", response_model=ApiKeyCreateResponse)
def create_api_key(
    *,
    db: Session = Depends(get_db),
    api_key_in: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Crear una nueva API key.
    """
    # Generar API key
    key = create_api_key()
    key_hash = hash_api_key(key)

    # Crear registro en base de datos
    api_key = ApiKey(
        name=api_key_in.name,
        key_hash=key_hash,
        user_id=current_user.id,
        company_id=current_user.company_id,
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    # Crear respuesta (incluye la key en texto plano, solo visible esta vez)
    response = ApiKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        key=key,
    )

    return response


@router.delete("/{api_key_id}", status_code=status.HTTP_200_OK)
def delete_api_key(
    *,
    db: Session = Depends(get_db),
    api_key_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Desactivar una API key.
    """
    api_key = (
        db.query(ApiKey)
        .filter(
            and_(
                ApiKey.id == api_key_id,
                ApiKey.user_id == current_user.id,
                ApiKey.is_active == True,
            )
        )
        .first()
    )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key no encontrada"
        )

    # Desactivar API key
    api_key.is_active = False

    db.add(api_key)
    db.commit()

    return {"status": "success", "message": "API key desactivada"}
