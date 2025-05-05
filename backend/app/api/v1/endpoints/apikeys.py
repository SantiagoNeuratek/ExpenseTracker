from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.api.deps import get_db, get_current_user
from app.models.apikey import ApiKey
from app.models.user import User
from app.models.company import Company
from app.core.security import create_api_key, hash_api_key
from app.schemas.apikey import (
    ApiKey as ApiKeySchema,
    ApiKeyCreate,
    ApiKeyCreateResponse,
)
from app.core.logging import get_logger
from app.core.cache import cache

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=List[ApiKeySchema])
def read_api_keys(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Any:
    """
    Obtener todas las API keys del usuario.
    Este endpoint implementa caché para mejorar el rendimiento bajo alta carga.
    """
    import hashlib
    import json
    
    # Crear una clave de caché única basada en el usuario
    cache_key = f"api_keys:{current_user.id}"
    cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()
    
    # Intentar obtener resultados de caché
    cached_result = cache.get(cache_key_hash)
    if cached_result:
        logger.debug(f"Cache hit for {cache_key}")
        return json.loads(cached_result)
    
    logger.debug(f"Cache miss for {cache_key}")
    
    # Si no hay caché, ejecutar la consulta
    api_keys = (
        db.query(ApiKey)
        .filter(and_(ApiKey.user_id == current_user.id, ApiKey.is_active == True))
        .all()
    )
    
    # Añadir versión truncada de las API keys
    api_keys_data = []
    for api_key in api_keys:
        # Mostrar solo los primeros 8 y últimos 4 caracteres, enmascarando el resto
        key_hash = api_key.key_hash
        key_preview = "et_••••••••••"
        if len(key_hash) > 12:  # Asegurarse de que hay suficientes caracteres
            # Los hash tienen 64 caracteres, así que podemos mostrar un formato fijo
            key_preview = f"et_••••••••••••{key_hash[-4:]}"
        
        # Crear diccionario con datos para la caché
        api_key_data = {
            "id": api_key.id,
            "name": api_key.name,
            "is_active": api_key.is_active,
            "created_at": api_key.created_at.isoformat(),
            "key_preview": key_preview
        }
        api_keys_data.append(api_key_data)
    
    # Almacenar en caché por 2 minutos (120 segundos)
    # Tiempo corto para que las nuevas claves sean visibles rápidamente
    cache.set(cache_key_hash, json.dumps(api_keys_data), 120)
    
    # Para la respuesta, configuramos los objetos para la serialización normal
    for api_key in api_keys:
        key_hash = api_key.key_hash
        if len(key_hash) > 12:
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

    # Determinar el company_id a utilizar
    company_id = current_user.company_id
    
    # Si el usuario es administrador y se proporciona un company_id, usar ese
    if current_user.is_admin and api_key_in.company_id is not None:
        company_id = api_key_in.company_id
        
        # Verificar que la empresa existe
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La empresa especificada no existe"
            )
    elif api_key_in.company_id is not None and not current_user.is_admin:
        # Si un usuario no-admin intenta especificar una company_id, ignorarlo
        logger.warning(f"Usuario no-admin (ID: {current_user.id}) intentó crear API key para otra empresa")

    # Generar API key with JWT
    key = create_api_key(current_user.id, company_id)
    key_hash = hash_api_key(key)

    # Crear registro en base de datos con todos los campos
    api_key = ApiKey(
        name=api_key_in.name,
        key_hash=key_hash,
        user_id=current_user.id,
        company_id=company_id,
        is_active=True,  # Explícitamente establecemos is_active
    )

    try:
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        # Invalida la caché de las API keys del usuario
        import hashlib
        cache_key = f"api_keys:{current_user.id}"
        cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()
        cache.delete(cache_key_hash)
        logger.debug(f"Caché invalidada para {cache_key} tras crear API key")
        
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
    
    # Invalidar la caché de las API keys del usuario
    import hashlib
    cache_key = f"api_keys:{current_user.id}"
    cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()
    cache.delete(cache_key_hash)
    logger.debug(f"Caché invalidada para {cache_key} tras desactivar API key")

    return {"status": "success", "message": "API key desactivada"}
