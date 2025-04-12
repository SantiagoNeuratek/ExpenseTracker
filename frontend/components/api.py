import requests
import os
from typing import Dict, List, Optional, Any, Union

# Variables de entorno
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_URL = f"{BACKEND_URL}/api/v1"


class ApiClient:
    """
    Cliente para interactuar con la API del backend.
    """

    def __init__(self, token: str = None):
        """
        Inicializar el cliente con un token opcional.

        Args:
            token: Token de autenticación JWT
        """
        self.token = token

    def get_headers(self) -> Dict[str, str]:
        """
        Obtener los headers para las peticiones autenticadas.

        Returns:
            Dict[str, str]: Headers con el token de autenticación
        """
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _handle_error_response(self, response) -> Dict:
        """
        Maneja las respuestas de error y extrae el mensaje detallado.

        Args:
            response: Objeto de respuesta de requests

        Returns:
            Dict: Diccionario con información de error
        """
        try:
            # Intenta obtener el detalle del error desde el JSON de respuesta
            error_data = response.json()
            if "detail" in error_data:
                return {
                    "error": f"Error {response.status_code}",
                    "detail": error_data["detail"],
                }
            return {"error": f"Error {response.status_code}", "detail": str(error_data)}
        except ValueError:
            # Si no es JSON, devuelve el texto crudo como detalle
            return {
                "error": f"Error {response.status_code}",
                "detail": response.text or str(response.reason),
            }

    def get(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Realizar una petición GET.

        Args:
            endpoint: Endpoint de la API
            params: Parámetros de la petición

        Returns:
            Dict: Respuesta de la API
        """
        try:
            response = requests.get(
                f"{API_URL}/{endpoint}", headers=self.get_headers(), params=params
            )

            # Capturar errores HTTP sin lanzar excepción
            if response.status_code >= 400:
                return self._handle_error_response(response)

            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Error de conexión", "detail": str(e)}
        except Exception as e:
            return {"error": "Error inesperado", "detail": str(e)}

    def post(self, endpoint: str, data: Dict) -> Dict:
        """
        Realizar una petición POST.

        Args:
            endpoint: Endpoint de la API
            data: Datos para enviar en el cuerpo de la petición

        Returns:
            Dict: Respuesta de la API
        """
        try:
            headers = self.get_headers()
            headers["Content-Type"] = "application/json"

            response = requests.post(
                f"{API_URL}/{endpoint}", headers=headers, json=data
            )

            # Capturar errores HTTP sin lanzar excepción
            if response.status_code >= 400:
                return self._handle_error_response(response)

            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Error de conexión", "detail": str(e)}
        except Exception as e:
            return {"error": "Error inesperado", "detail": str(e)}

    def put(self, endpoint: str, data: Dict) -> Dict:
        """
        Realizar una petición PUT.

        Args:
            endpoint: Endpoint de la API
            data: Datos para enviar en el cuerpo de la petición

        Returns:
            Dict: Respuesta de la API
        """
        try:
            headers = self.get_headers()
            headers["Content-Type"] = "application/json"

            response = requests.put(f"{API_URL}/{endpoint}", headers=headers, json=data)

            # Capturar errores HTTP sin lanzar excepción
            if response.status_code >= 400:
                return self._handle_error_response(response)

            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Error de conexión", "detail": str(e)}
        except Exception as e:
            return {"error": "Error inesperado", "detail": str(e)}

    def delete(self, endpoint: str) -> Dict:
        """
        Realizar una petición DELETE.

        Args:
            endpoint: Endpoint de la API

        Returns:
            Dict: Respuesta de la API
        """
        try:
            response = requests.delete(
                f"{API_URL}/{endpoint}", headers=self.get_headers()
            )

            # Capturar errores HTTP sin lanzar excepción
            if response.status_code >= 400:
                return self._handle_error_response(response)

            # Para métodos DELETE que devuelven 204 No Content
            if response.status_code == 204:
                return {
                    "status": "success",
                    "message": "Operación completada con éxito",
                }

            try:
                return response.json()
            except ValueError:
                return {
                    "status": "success",
                    "message": "Operación completada con éxito",
                }

        except requests.exceptions.RequestException as e:
            return {"error": f"Error de conexión", "detail": str(e)}
        except Exception as e:
            return {"error": "Error inesperado", "detail": str(e)}
