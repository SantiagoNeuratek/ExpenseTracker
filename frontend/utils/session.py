import streamlit as st
from typing import Dict, Any, Optional, List, Tuple, Union
import time
from datetime import datetime, timedelta
import logging
from .api_client import get_cached_api_client, fetch_data, API_URL

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("session")

def initialize_session_state():
    """
    Initialize session state variables if they don't exist.
    Call this at the start of your app to ensure all required state is available.
    """
    # Authentication 
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "company_info" not in st.session_state:
        st.session_state.company_info = None
    if "token_expiry" not in st.session_state:
        st.session_state.token_expiry = None
        
    # Navigation
    if "current_page" not in st.session_state:
        st.session_state.current_page = "dashboard"
    if "previous_page" not in st.session_state:
        st.session_state.previous_page = None
    if "menu_structure" not in st.session_state:
        st.session_state.menu_structure = None
        
    # Notifications
    if "notifications" not in st.session_state:
        st.session_state.notifications = []
        
    # Filter state (prevents losing filters on page reload)
    if "filters" not in st.session_state:
        st.session_state.filters = {}
        
    # Pagination state (for tables)
    if "pagination" not in st.session_state:
        st.session_state.pagination = {}
        
    # Form data (prevents losing data on validation errors)
    if "form_data" not in st.session_state:
        st.session_state.form_data = {}
        
    # Cache invalidation flags
    if "cache_invalidation" not in st.session_state:
        st.session_state.cache_invalidation = {
            "expenses": 0,
            "categories": 0,
            "users": 0,
            "apikeys": 0
        }

def is_authenticated() -> bool:
    """
    Check if the user is authenticated.
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    return st.session_state.token is not None

def login(email: str, password: str) -> Tuple[bool, str]:
    """
    Authenticate user with the backend.
    
    Args:
        email: User email
        password: User password
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        client = get_cached_api_client()
        response = client.session.post(
            f"{API_URL}/auth/login",
            data={"username": email, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            token_data = response.json()
            st.session_state.token = token_data["access_token"]
            
            # Estimate token expiry (default to 7 days if not specified)
            expiry_minutes = token_data.get("expires_minutes", 10080)  # Default 7 days
            st.session_state.token_expiry = datetime.now() + timedelta(minutes=expiry_minutes)
            
            # Load user info immediately to cache it
            fetch_current_user()
            return True, "Login successful"
        else:
            error_message = "Invalid credentials"
            try:
                error_data = response.json()
                if "detail" in error_data:
                    error_message = error_data["detail"]
            except:
                pass
            return False, f"Error: {error_message}"
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return False, f"Connection error: {str(e)}"

def logout():
    """
    Clear session state to log out user.
    
    Returns:
        Tuple[bool, str]: (success, message)
    """
    # Preserve only notifications temporarily for feedback
    notifications = st.session_state.notifications
    
    # Clear all session state
    for key in list(st.session_state.keys()):
        if key != "notifications":
            del st.session_state[key]
    
    # Restore notifications so logout message displays
    st.session_state.notifications = notifications
    
    # Initialize fresh state
    initialize_session_state()
    
    return True, "Logged out successfully"

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_current_user() -> Optional[Dict]:
    """
    Get current user info with caching.
    
    Returns:
        Optional[Dict]: User information or None if not authenticated
    """
    if not is_authenticated():
        return None
    
    try:
        # Use token directly instead of from session state to work with caching
        token = st.session_state.token
        client = get_cached_api_client(token)
        user_data = client.get("auth/me")
        
        if "error" in user_data:
            logger.warning(f"Error fetching user info: {user_data['error']}")
            return None
        
        # Store in session state (cache works separately)
        st.session_state.user_info = user_data
        return user_data
    except Exception as e:
        logger.error(f"Error fetching user info: {str(e)}")
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_company_info(company_id: int) -> Optional[Dict]:
    """
    Get company info with caching.
    
    Args:
        company_id: ID of the company
        
    Returns:
        Optional[Dict]: Company information or None if error
    """
    if not is_authenticated() or not company_id:
        return None
    
    token = st.session_state.token
    client = get_cached_api_client(token)
    company_data = client.get(f"companies/{company_id}")
    
    if "error" in company_data:
        return None
    
    # Store in session state
    st.session_state.company_info = company_data
    return company_data

def check_token_expiration():
    """
    Check if the token has expired and redirect to login if needed.
    """
    if not is_authenticated():
        return
    
    # If we have an expiry time, check it
    if st.session_state.token_expiry:
        if datetime.now() > st.session_state.token_expiry:
            logout()
            st.info("Your session has expired. Please log in again.")
            return

    # Otherwise try a simple API call to verify token
    try:
        user_info = fetch_current_user()
        if not user_info or "error" in user_info:
            logout()
            st.info("Session invalid. Please log in again.")
    except:
        # If there's an error, session might be invalid
        pass  

def add_notification(message: str, notification_type: str = "info", duration: int = 5):
    """
    Add a notification to display to the user.
    
    Args:
        message: Notification message
        notification_type: Type of notification (info, success, warning, error)
        duration: Time in seconds to display (0 for persistent)
    """
    notification_id = time.time()
    expiry = None if duration == 0 else time.time() + duration
    
    st.session_state.notifications.append({
        "id": notification_id,
        "message": message,
        "type": notification_type,
        "expiry": expiry
    })

def display_notifications():
    """
    Display and manage notifications, removing expired ones.
    """
    if not st.session_state.notifications:
        return
    
    current_time = time.time()
    remaining_notifications = []
    
    for notification in st.session_state.notifications:
        # Check if notification should be removed due to expiry
        if notification["expiry"] and notification["expiry"] < current_time:
            continue
            
        # Display the notification with appropriate styling
        notification_type = notification["type"]
        message = notification["message"]
        
        if notification_type == "success":
            st.success(message)
        elif notification_type == "error":
            st.error(message)
        elif notification_type == "warning":
            st.warning(message)
        else:  # info is default
            st.info(message)
            
        # Keep non-expired notifications
        remaining_notifications.append(notification)
    
    # Update the list of notifications
    st.session_state.notifications = remaining_notifications

def invalidate_cache(cache_key: str):
    """
    Invalidate a specific cache by updating its timestamp.
    
    Args:
        cache_key: Key for the cache to invalidate (expenses, categories, etc.)
    """
    if cache_key in st.session_state.cache_invalidation:
        st.session_state.cache_invalidation[cache_key] = time.time()

def get_cache_key(base_key: str) -> float:
    """
    Get cache invalidation timestamp for a given key.
    
    Args:
        base_key: The base cache key name
        
    Returns:
        float: Timestamp of last invalidation
    """
    return st.session_state.cache_invalidation.get(base_key, 0)

def set_page(page_name: str):
    """
    Set the current page and update navigation state.
    
    Args:
        page_name: Name of the page to navigate to
    """
    st.session_state.previous_page = st.session_state.current_page
    st.session_state.current_page = page_name

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get the current user information.
    
    Returns:
        Optional[Dict[str, Any]]: User information
    """
    if not is_authenticated():
        return None
    
    # Use cached user info if available, otherwise fetch
    if st.session_state.user_info:
        return st.session_state.user_info
    
    return fetch_current_user()

def is_admin() -> bool:
    """
    Check if the current user is an admin.
    
    Returns:
        bool: True if the user is an admin
    """
    user_info = get_current_user()
    return user_info is not None and user_info.get("is_admin", False)

def get_company_id() -> Optional[int]:
    """
    Get the current user's company ID.
    
    Returns:
        Optional[int]: Company ID or None
    """
    user_info = get_current_user()
    return user_info.get("company_id") if user_info else None 