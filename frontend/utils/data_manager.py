import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, date
import logging
from .api_client import get_cached_api_client, fetch_data, fetch_with_key
from .session import is_authenticated, get_cache_key, get_company_id

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("data_manager")

# Expense operations
@st.cache_data(ttl=300, max_entries=20, show_spinner=False)
def get_expenses(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 100,
    _cache_key: float = 0,  # Used to invalidate cache when needed
) -> Dict:
    """
    Get expenses with caching.
    
    Args:
        start_date: Start date filter
        end_date: End date filter
        category_id: Category ID filter
        page: Page number for pagination
        page_size: Items per page
        _cache_key: Cache invalidation key
        
    Returns:
        Dict: Expenses data
    """
    if not is_authenticated():
        return {"items": [], "total": 0, "page": 1, "page_size": page_size}
    
    # Convert dates to ISO format strings
    params = {"page": page, "page_size": page_size}
    if start_date:
        params["start_date"] = start_date.isoformat()
    if end_date:
        params["end_date"] = end_date.isoformat()
    if category_id and category_id != "all":
        params["category_id"] = category_id
    
    token = st.session_state.token
    try:
        response = fetch_data("expenses", params, token)
        
        # Handle error responses
        if "error" in response:
            logger.error(f"Error fetching expenses: {response.get('detail', response['error'])}")
            return {"items": [], "total": 0, "page": 1, "page_size": page_size, "error": response.get('detail', response['error'])}
        
        # If response doesn't contain page or page_size, add them
        if "page" not in response:
            response["page"] = page
        if "page_size" not in response:
            response["page_size"] = page_size
        
        return response
    except Exception as e:
        logger.error(f"Exception fetching expenses: {str(e)}")
        return {"items": [], "total": 0, "page": 1, "page_size": page_size, "error": str(e)}

@st.cache_data(ttl=3600, max_entries=10, show_spinner=False)
def get_expenses_dataframe(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 100,
    _cache_key: float = 0,  # Used to invalidate cache when needed
) -> Tuple[pd.DataFrame, Dict]:
    """
    Get expenses as a pandas DataFrame with caching.
    
    Args:
        start_date: Start date filter
        end_date: End date filter
        category_id: Category ID filter
        page: Page number for pagination
        page_size: Items per page
        _cache_key: Cache invalidation key
        
    Returns:
        Tuple[pd.DataFrame, Dict]: (DataFrame with expenses, metadata)
    """
    expenses_data = get_expenses(
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        page=page,
        page_size=page_size,
        _cache_key=_cache_key
    )
    
    if "error" in expenses_data:
        return pd.DataFrame(), expenses_data
    
    if not expenses_data or "items" not in expenses_data or not expenses_data["items"]:
        return pd.DataFrame(), expenses_data
    
    # Create DataFrame and apply transformations
    df = pd.DataFrame(expenses_data["items"])
    
    # Format dates
    if "date_incurred" in df.columns:
        df["date_incurred"] = pd.to_datetime(df["date_incurred"])
    
    # Get metadata for return
    metadata = {k: v for k, v in expenses_data.items() if k != "items"}
    
    return df, metadata

def create_expense(data: Dict) -> Tuple[bool, str, Optional[Dict]]:
    """
    Create a new expense.
    
    Args:
        data: Expense data
        
    Returns:
        Tuple[bool, str, Optional[Dict]]: (success, message, created expense data)
    """
    if not is_authenticated():
        return False, "Not authenticated", None
    
    token = st.session_state.token
    client = get_cached_api_client(token)
    
    # Format expense data for API
    expense_data = {
        "amount": float(data["amount"]),
        "date_incurred": data["date"].isoformat() if isinstance(data["date"], (date, datetime)) else data["date"],
        "category_id": data["category_id"],
        "description": data.get("description", "")
    }
    
    response = client.post("expenses", expense_data)
    
    if "error" in response:
        error_message = response.get("detail", response["error"])
        return False, f"Error: {error_message}", None
    
    # Invalidate expenses cache (by updating timestamp)
    st.session_state.cache_invalidation["expenses"] = datetime.now().timestamp()
    
    # Clear the cache for get_expenses
    get_expenses.clear()
    get_expenses_dataframe.clear()
    
    return True, "Expense created successfully", response

def update_expense(expense_id: int, data: Dict) -> Tuple[bool, str, Optional[Dict]]:
    """
    Update an existing expense.
    
    Args:
        expense_id: ID of the expense to update
        data: Updated expense data
        
    Returns:
        Tuple[bool, str, Optional[Dict]]: (success, message, updated expense data)
    """
    if not is_authenticated():
        return False, "Not authenticated", None
    
    token = st.session_state.token
    client = get_cached_api_client(token)
    
    # Format expense data for API
    expense_data = {}
    if "amount" in data:
        expense_data["amount"] = float(data["amount"])
    if "date" in data:
        expense_data["date_incurred"] = data["date"].isoformat() if isinstance(data["date"], (date, datetime)) else data["date"]
    if "category_id" in data:
        expense_data["category_id"] = data["category_id"]
    if "description" in data:
        expense_data["description"] = data.get("description", "")
    
    response = client.put(f"expenses/{expense_id}", expense_data)
    
    if "error" in response:
        error_message = response.get("detail", response["error"])
        return False, f"Error: {error_message}", None
    
    # Invalidate expenses cache
    st.session_state.cache_invalidation["expenses"] = datetime.now().timestamp()
    
    # Clear the cache for get_expenses
    get_expenses.clear()
    get_expenses_dataframe.clear()
    
    return True, "Expense updated successfully", response

def delete_expense(expense_id: int) -> Tuple[bool, str]:
    """
    Delete an expense.
    
    Args:
        expense_id: ID of the expense to delete
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    if not is_authenticated():
        return False, "Not authenticated"
    
    token = st.session_state.token
    client = get_cached_api_client(token)
    
    response = client.delete(f"expenses/{expense_id}")
    
    if "error" in response:
        error_message = response.get("detail", response["error"])
        return False, f"Error: {error_message}"
    
    # Invalidate expenses cache
    st.session_state.cache_invalidation["expenses"] = datetime.now().timestamp()
    
    # Clear the cache for get_expenses
    get_expenses.clear()
    get_expenses_dataframe.clear()
    
    return True, "Expense deleted successfully"

# Category operations
@st.cache_data(ttl=600, show_spinner=False)
def get_categories(_cache_key: float = 0) -> List[Dict]:
    """
    Get categories with caching.
    
    Args:
        _cache_key: Cache invalidation key
        
    Returns:
        List[Dict]: List of categories
    """
    if not is_authenticated():
        return []
    
    token = st.session_state.token
    response = fetch_data("categories", None, token)
    
    if "error" in response:
        logger.error(f"Error fetching categories: {response.get('detail', response['error'])}")
        return []
    
    return response

def create_category(data: Dict) -> Tuple[bool, str, Optional[Dict]]:
    """
    Create a new category.
    
    Args:
        data: Category data
        
    Returns:
        Tuple[bool, str, Optional[Dict]]: (success, message, created category data)
    """
    if not is_authenticated():
        return False, "Not authenticated", None
    
    token = st.session_state.token
    client = get_cached_api_client(token)
    
    category_data = {
        "name": data["name"],
        "description": data.get("description", ""),
        "expense_limit": float(data["expense_limit"]) if data.get("expense_limit") else None
    }
    
    response = client.post("categories", category_data)
    
    if "error" in response:
        error_message = response.get("detail", response["error"])
        return False, f"Error: {error_message}", None
    
    # Invalidate categories cache
    st.session_state.cache_invalidation["categories"] = datetime.now().timestamp()
    
    # Clear the cache for get_categories
    get_categories.clear()
    
    return True, "Category created successfully", response

def update_category(category_id: int, data: Dict) -> Tuple[bool, str, Optional[Dict]]:
    """
    Update a category.
    
    Args:
        category_id: ID of the category to update
        data: Updated category data
        
    Returns:
        Tuple[bool, str, Optional[Dict]]: (success, message, updated category data)
    """
    if not is_authenticated():
        return False, "Not authenticated", None
    
    token = st.session_state.token
    client = get_cached_api_client(token)
    
    category_data = {}
    if "name" in data:
        category_data["name"] = data["name"]
    if "description" in data:
        category_data["description"] = data.get("description", "")
    if "expense_limit" in data:
        category_data["expense_limit"] = float(data["expense_limit"]) if data["expense_limit"] else None
    
    response = client.put(f"categories/{category_id}", category_data)
    
    if "error" in response:
        error_message = response.get("detail", response["error"])
        return False, f"Error: {error_message}", None
    
    # Invalidate categories cache
    st.session_state.cache_invalidation["categories"] = datetime.now().timestamp()
    
    # Clear the cache for get_categories
    get_categories.clear()
    
    return True, "Category updated successfully", response

def delete_category(category_id: int) -> Tuple[bool, str]:
    """
    Delete a category.
    
    Args:
        category_id: ID of the category to delete
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    if not is_authenticated():
        return False, "Not authenticated"
    
    token = st.session_state.token
    client = get_cached_api_client(token)
    
    response = client.delete(f"categories/{category_id}")
    
    if "error" in response:
        error_message = response.get("detail", response["error"])
        return False, f"Error: {error_message}"
    
    # Invalidate categories cache
    st.session_state.cache_invalidation["categories"] = datetime.now().timestamp()
    
    # Clear the cache for get_categories
    get_categories.clear()
    
    return True, "Category deleted successfully"

# API key operations
@st.cache_data(ttl=300, show_spinner=False)
def get_api_keys(_cache_key: float = 0) -> List[Dict]:
    """
    Get API keys with caching.
    
    Args:
        _cache_key: Cache invalidation key
        
    Returns:
        List[Dict]: List of API keys
    """
    if not is_authenticated():
        return []
    
    token = st.session_state.token
    response = fetch_data("apikeys", None, token)
    
    if "error" in response:
        logger.error(f"Error fetching API keys: {response.get('detail', response['error'])}")
        return []
    
    return response

def create_api_key(name: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Create a new API key.
    
    Args:
        name: Name for the API key
        
    Returns:
        Tuple[bool, str, Optional[Dict]]: (success, message, created API key data)
    """
    if not is_authenticated():
        return False, "Not authenticated", None
    
    token = st.session_state.token
    client = get_cached_api_client(token)
    
    response = client.post("apikeys", {"name": name})
    
    if "error" in response:
        error_message = response.get("detail", response["error"])
        return False, f"Error: {error_message}", None
    
    # Invalidate API keys cache
    st.session_state.cache_invalidation["apikeys"] = datetime.now().timestamp()
    
    # Clear the cache for get_api_keys
    get_api_keys.clear()
    
    return True, "API key created successfully", response

def delete_api_key(key_id: int) -> Tuple[bool, str]:
    """
    Delete an API key.
    
    Args:
        key_id: ID of the API key to delete
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    if not is_authenticated():
        return False, "Not authenticated"
    
    token = st.session_state.token
    client = get_cached_api_client(token)
    
    response = client.delete(f"apikeys/{key_id}")
    
    if "error" in response:
        error_message = response.get("detail", response["error"])
        return False, f"Error: {error_message}"
    
    # Invalidate API keys cache
    st.session_state.cache_invalidation["apikeys"] = datetime.now().timestamp()
    
    # Clear the cache for get_api_keys
    get_api_keys.clear()
    
    return True, "API key deleted successfully"

# User operations for admin
@st.cache_data(ttl=600, show_spinner=False)
def get_users(_cache_key: float = 0) -> List[Dict]:
    """
    Get users with caching (admin only).
    
    Args:
        _cache_key: Cache invalidation key
        
    Returns:
        List[Dict]: List of users
    """
    if not is_authenticated():
        return []
    
    token = st.session_state.token
    response = fetch_data("users", None, token)
    
    if "error" in response:
        logger.error(f"Error fetching users: {response.get('detail', response['error'])}")
        return []
    
    return response

def invite_user(email: str) -> Tuple[bool, str]:
    """
    Invite a user to join.
    
    Args:
        email: Email of the user to invite
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    if not is_authenticated():
        return False, "Not authenticated"
    
    token = st.session_state.token
    client = get_cached_api_client(token)
    
    response = client.post("auth/invite", {"email": email})
    
    if "error" in response:
        error_message = response.get("detail", response["error"])
        return False, f"Error: {error_message}"
    
    # Invalidate users cache
    st.session_state.cache_invalidation["users"] = datetime.now().timestamp()
    
    # Clear the cache for get_users
    get_users.clear()
    
    return True, "User invited successfully"

# Dashboard analytics
@st.cache_data(ttl=600, show_spinner=False)
def get_top_categories(_cache_key: float = 0) -> List[Dict]:
    """
    Get top spending categories.
    
    Args:
        _cache_key: Cache invalidation key
        
    Returns:
        List[Dict]: List of top categories
    """
    if not is_authenticated():
        return []
    
    token = st.session_state.token
    response = fetch_data("expenses/top-categories", None, token)
    
    if "error" in response:
        logger.error(f"Error fetching top categories: {response.get('detail', response['error'])}")
        return []
    
    return response 