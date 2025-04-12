import streamlit as st
import os
import time
from datetime import datetime

# Esta función asume que el módulo auth y api están en components/
from components.auth import is_authenticated
from components.api import ApiClient


def get_api_client():
    """Obtener una instancia del cliente API con el token actual."""
    token = st.session_state.token if is_authenticated() else None
    return ApiClient(token)


def get_current_user():
    """Obtiene información del usuario actual."""
    if not is_authenticated():
        return None

    # Suponemos que el usuario actual se almacena en la session_state
    return st.session_state.get("user_info", None)


def get_company_info(company_id):
    """Obtiene información de la empresa."""
    if not is_authenticated():
        return None

    client = get_api_client()
    response = client.get(f"companies/{company_id}")

    if "error" in response:
        st.error(f"Error al obtener información de la empresa: {response['error']}")
        return None

    return response


def get_categories():
    """Obtiene las categorías de gastos."""
    if not is_authenticated():
        return []

    client = get_api_client()
    response = client.get("categories")

    if "error" in response:
        st.error(f"Error al obtener categorías: {response['error']}")
        return []

    return response


def get_expenses(
    start_date=None, end_date=None, category_id=None, page=1, page_size=100
):
    """Obtiene los gastos según los filtros especificados."""
    if not is_authenticated():
        return {"items": [], "total": 0, "error": "No autenticado"}

    client = get_api_client()
    params = {"page": page, "page_size": page_size}

    if start_date:
        params["start_date"] = start_date.strftime("%Y-%m-%d")
    if end_date:
        params["end_date"] = end_date.strftime("%Y-%m-%d")
    if category_id:
        params["category_id"] = category_id

    try:
        response = client.get("expenses", params)

        if "error" in response:
            st.warning(
                f"Error al obtener gastos: {response.get('detail', response['error'])}"
            )
            return {"items": [], "total": 0, "error": response["error"]}

        return response
    except Exception as e:
        st.error(f"Error inesperado: {str(e)}")
        return {"items": [], "total": 0, "error": str(e)}
