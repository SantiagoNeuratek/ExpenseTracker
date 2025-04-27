import streamlit as st
import requests
import os
from typing import Dict, List, Optional, Any, Union, Callable
import time
import logging
from functools import lru_cache

# Environment variables
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_URL = f"{BACKEND_URL}/api/v1"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_client")

# Cache for API client instances to avoid recreation
@st.cache_resource
def get_cached_api_client(token: Optional[str] = None) -> 'ApiClient':
    """
    Get a cached API client instance based on the token.
    
    Args:
        token: Authentication token (optional)
        
    Returns:
        ApiClient: Cached API client instance
    """
    logger.info(f"Creating new cached API client instance")
    return ApiClient(token)

class ApiClient:
    """
    Client for interacting with the backend API with built-in caching.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the client with a token.
        
        Args:
            token: Authentication token (optional)
        """
        self.token = token
        self.session = requests.Session()
        
        # Set default timeout
        self.timeout = 10
        
        # Setup retry strategy with backoff
        self.max_retries = 3
        
    def get_headers(self) -> Dict[str, str]:
        """
        Get headers for authenticated requests.
        
        Returns:
            Dict[str, str]: Headers with authentication token
        """
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _handle_error_response(self, response) -> Dict:
        """
        Handle error responses and extract detailed messages.
        
        Args:
            response: Response object from requests
            
        Returns:
            Dict: Dictionary with error information
        """
        try:
            error_data = response.json()
            if "detail" in error_data:
                return {
                    "error": f"Error {response.status_code}",
                    "detail": error_data["detail"],
                }
            return {"error": f"Error {response.status_code}", "detail": str(error_data)}
        except ValueError:
            return {
                "error": f"Error {response.status_code}",
                "detail": response.text or str(response.reason),
            }
            
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests
            
        Returns:
            Dict: Response data or error information
        """
        url = f"{API_URL}/{endpoint}"
        headers = self.get_headers()
        
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
            
        kwargs["headers"] = headers
        kwargs["timeout"] = kwargs.get("timeout", self.timeout)
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, **kwargs)
                
                # Return early on success
                if response.status_code < 400:
                    try:
                        return response.json()
                    except ValueError:
                        # For non-JSON responses like 204 No Content
                        if response.status_code == 204:
                            return {"status": "success", "message": "Operation successful"}
                        return {"status": "success", "content": response.text}
                        
                # Handle errors but only retry on server errors (5xx)
                if response.status_code >= 500:
                    backoff_time = 0.1 * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Request failed with {response.status_code}, retrying in {backoff_time}s")
                    time.sleep(backoff_time)
                    continue
                else:
                    # For 4xx errors, return the error without retrying
                    return self._handle_error_response(response)
                    
            except requests.exceptions.RequestException as e:
                # Network errors, retry with backoff
                backoff_time = 0.1 * (2 ** attempt)
                logger.warning(f"Request error: {str(e)}, retrying in {backoff_time}s")
                time.sleep(backoff_time)
                
        # If we've exhausted retries
        return {"error": "Request failed after retries", "detail": "The server is not responding"}
        
    # Method-specific wrappers with caching where appropriate
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Perform a GET request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Dict: Response data
        """
        return self._make_request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict) -> Dict:
        """
        Perform a POST request. Never cached since it modifies data.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            
        Returns:
            Dict: Response data
        """
        return self._make_request("POST", endpoint, json=data)
    
    def put(self, endpoint: str, data: Dict) -> Dict:
        """
        Perform a PUT request. Never cached since it modifies data.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            
        Returns:
            Dict: Response data
        """
        return self._make_request("PUT", endpoint, json=data)
    
    def delete(self, endpoint: str) -> Dict:
        """
        Perform a DELETE request. Never cached since it modifies data.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Dict: Response data
        """
        return self._make_request("DELETE", endpoint)

# Helper functions with caching that use the API client
@st.cache_data(ttl=300)
def fetch_data(endpoint: str, params: Optional[Dict] = None, token: Optional[str] = None) -> Dict:
    """
    Fetch data from API with caching.
    
    Args:
        endpoint: API endpoint
        params: Query parameters
        token: Authentication token
        
    Returns:
        Dict: Response data
    """
    client = get_cached_api_client(token)
    return client.get(endpoint, params)

@st.cache_data(ttl=300)
def fetch_with_key(endpoint: str, key: str, params: Optional[Dict] = None, token: Optional[str] = None) -> Dict:
    """
    Fetch data with a cache key for when params are complex.
    
    Args:
        endpoint: API endpoint
        key: Cache key
        params: Query parameters
        token: Authentication token
        
    Returns:
        Dict: Response data
    """
    client = get_cached_api_client(token)
    return client.get(endpoint, params) 