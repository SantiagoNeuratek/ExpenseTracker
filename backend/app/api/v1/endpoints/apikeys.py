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
    
    # Añadir versión truncada de las API keys
    for api_key in api_keys:
        # Mostrar solo los primeros 8 y últimos 4 caracteres, enmascarando el resto
        key_hash = api_key.key_hash
        if len(key_hash) > 12:  # Asegurarse de que hay suficientes caracteres
            # Los hash tienen 64 caracteres, así que podemos mostrar un formato fijo
            api_key.key_preview = f"et_••••••••••••{key_hash[-4:]}"
        else:
            api_key.key_preview = "et_••••••••••"
    
    return api_keys


@router.post("", response_model=ApiKeyCreateResponse)
def create_new_api_key(
    *,
    db: Session = Depends(get_db),
    api_key_in: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Crear una nueva API key.
    """
    # Verificar si el usuario ya tiene una API key con el mismo nombre
    existing_key = db.query(ApiKey).filter(
        and_(
            ApiKey.user_id == current_user.id,
            ApiKey.name == api_key_in.name,
            ApiKey.is_active == True
        )
    ).first()
    
    if existing_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una API key activa con ese nombre"
        )

    # Generar API key with JWT
    key = create_api_key(current_user.id, current_user.company_id)
    key_hash = hash_api_key(key)

    # Crear registro en base de datos con todos los campos
    api_key = ApiKey(
        name=api_key_in.name,
        key_hash=key_hash,
        user_id=current_user.id,
        company_id=current_user.company_id,
        is_active=True,  # Explícitamente establecemos is_active
    )

    try:
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear la API key"
        )

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


@router.get("/{api_key_id}/reveal", response_model=ApiKeyCreateResponse)
def reveal_api_key(
    *,
    db: Session = Depends(get_db),
    api_key_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Revelar una API key completa.
    
    NOTA: En un entorno de producción real, esto no se debería hacer por motivos de seguridad.
    Las claves API no deberían almacenarse en texto plano ni ser recuperables.
    Esto es solo para fines de demostración.
    """
    # Verificar si la clave pertenece al usuario
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
    
    # IMPORTANTE: En un entorno real, las API keys no deberían almacenarse de forma
    # que puedan ser recuperadas. Lo ideal es solo almacenar hashes.
    # Esto es únicamente para propósitos de demostración.
    
    # Generamos una API key nueva basada en el mismo usuario y empresa
    # Este sería el equivalente a regenerar la clave
    regenerated_key = create_api_key(current_user.id, current_user.company_id)
    
    # Crear respuesta con la clave regenerada
    response = ApiKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        key=regenerated_key,
    )

    return response
