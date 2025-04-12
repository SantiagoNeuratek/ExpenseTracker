import streamlit as st
import requests
import os
from typing import Tuple

# Variables de entorno
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_URL = f"{BACKEND_URL}/api/v1"


def login(email: str, password: str) -> Tuple[bool, str]:
    """
    Iniciar sesión con el backend.

    Args:
        email: Correo electrónico del usuario
        password: Contraseña del usuario

    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    try:
        response = requests.post(
            f"{API_URL}/auth/login", data={"username": email, "password": password}
        )

        if response.status_code == 200:
            token_data = response.json()
            st.session_state.token = token_data["access_token"]
            return True, "Inicio de sesión exitoso"
        else:
            return (
                False,
                f"Error: {response.json().get('detail', 'Credenciales inválidas')}",
            )
    except Exception as e:
        return False, f"Error de conexión: {str(e)}"


def logout():
    """
    Cerrar sesión eliminando todas las variables de sesión.
    """
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    return True, "Sesión cerrada exitosamente"


def is_authenticated() -> bool:
    """
    Verificar si el usuario está autenticado.

    Returns:
        bool: True si el usuario está autenticado, False en caso contrario
    """
    return "token" in st.session_state and st.session_state.token is not None


def get_current_user():
    """
    Obtener información del usuario actual.

    Returns:
        dict: Información del usuario o None si no está autenticado
    """
    if not is_authenticated():
        return None

    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    try:
        response = requests.get(f"{API_URL}/auth/me", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception:
        return None


def check_token_expiration():
    """
    Verificar si el token ha expirado y, en caso afirmativo, cerrar sesión.
    """
    if not is_authenticated():
        return

    # Intentar hacer una petición simple para verificar el token
    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    try:
        response = requests.get(f"{API_URL}/auth/me", headers=headers)
        if response.status_code == 401:  # Token expirado o inválido
            logout()
            st.warning("Tu sesión ha expirado. Por favor, inicia sesión nuevamente.")
            st.rerun()
    except Exception:
        pass  # No hacer nada si hay un error de conexión
