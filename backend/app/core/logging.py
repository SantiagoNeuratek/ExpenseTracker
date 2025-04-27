import logging
import json
import sys
import time
import uuid
import os
from typing import Dict, Any, Optional
from contextvars import ContextVar

# Context variables to hold request information across the request lifecycle
request_id_context: ContextVar[str] = ContextVar('request_id', default='')
user_id_context: ContextVar[Optional[int]] = ContextVar('user_id', default=None)
company_id_context: ContextVar[Optional[int]] = ContextVar('company_id', default=None)

class RequestContextFilter(logging.Filter):
    """Logging filter that adds the current request context to log records"""
    
    def filter(self, record):
        record.request_id = request_id_context.get('')
        user_id = user_id_context.get(None)
        if user_id:
            record.user_id = user_id
            
        company_id = company_id_context.get(None)
        if company_id:
            record.company_id = company_id
        
        return True

class JsonFormatter(logging.Formatter):
    """Format logs as JSON for better machine parsing and integration with log aggregation tools"""
    
    def __init__(self, **kwargs):
        self.extras = kwargs
    
    def format(self, record):
        timestamp = time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(record.created))
        
        # Base log data
        log_data = {
            'timestamp': timestamp,
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add request context if available
        if hasattr(record, 'request_id') and record.request_id:
            log_data['request_id'] = record.request_id
            
        if hasattr(record, 'user_id') and record.user_id:
            log_data['user_id'] = record.user_id
            
        if hasattr(record, 'company_id') and record.company_id:
            log_data['company_id'] = record.company_id
            
        # Add extra data from record
        if hasattr(record, 'data') and record.data:
            log_data.update(record.data)
            
        # Add timing information if available
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms
            
        # Add performance metrics if available
        if hasattr(record, 'performance'):
            log_data['performance'] = record.performance
            
        # Add query details if available (for database operations)
        if hasattr(record, 'query'):
            log_data['query'] = record.query
            
        # Add any exception info
        if record.exc_info:
            # Format exception details in a structured way
            exc_type = record.exc_info[0]
            exc_value = record.exc_info[1]
            exc_tb = self.formatException(record.exc_info)
            
            log_data['exception'] = {
                'type': exc_type.__name__,
                'message': str(exc_value),
                'traceback': exc_tb
            }
            
            # Add status code for HTTP exceptions if available
            if hasattr(exc_value, 'status_code'):
                log_data['exception']['status_code'] = exc_value.status_code
                
            # Add error details if available
            if hasattr(exc_value, 'detail'):
                log_data['exception']['detail'] = exc_value.detail
            
        # Add extra fields passed to the formatter
        log_data.update(self.extras)
        
        # Ensure everything is JSON serializable
        return self._ensure_serializable(log_data)
    
    def _ensure_serializable(self, obj):
        """Ensure the object is JSON serializable"""
        try:
            return json.dumps(obj)
        except (TypeError, ValueError):
            # If there are non-serializable objects, convert them to strings
            if isinstance(obj, dict):
                return json.dumps({k: str(v) if not isinstance(v, (dict, list)) else self._ensure_serializable(v) 
                                  for k, v in obj.items()})
            elif isinstance(obj, list):
                return json.dumps([str(v) if not isinstance(v, (dict, list)) else self._ensure_serializable(v) 
                                  for v in obj])
            else:
                return json.dumps(str(obj))

def setup_logging(app_name: str = "expense-tracker", 
                  log_level: str = "INFO", 
                  is_json: bool = True):
    """
    Sets up structured logging for the application.
    
    Args:
        app_name: Application name to include in logs
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        is_json: Whether to format logs as JSON (True) or text (False)
    """
    # Convert string level to actual logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    # Add filter for request context
    context_filter = RequestContextFilter()
    console_handler.addFilter(context_filter)
    
    # Set formatter based on configuration
    if is_json:
        formatter = JsonFormatter(app=app_name, env=os.getenv('ENVIRONMENT', 'development'))
    else:
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Also set level for uvicorn and fastapi access logs
    for logger_name in ['uvicorn', 'uvicorn.access', 'fastapi']:
        logger = logging.getLogger(logger_name)
        logger.handlers = []  # Remove any existing handlers
        logger.propagate = True
        logger.setLevel(numeric_level)
    
    # Set SQLAlchemy logging to ERROR by default (very verbose otherwise)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
    
    return root_logger

def get_logger(name: str = None):
    """Get a logger with the given name that includes request context"""
    logger = logging.getLogger(name)
    return logger

def log_with_context(logger, level: str, msg: str, data: Dict[str, Any] = None, exc_info=None,
                    duration_ms: float = None, performance: Dict[str, Any] = None, query: str = None):
    """
    Log with additional context data as a dictionary
    
    Args:
        logger: The logger instance
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        msg: Log message
        data: Additional data to include in the log
        exc_info: Exception info tuple (type, value, traceback)
        duration_ms: Operation duration in milliseconds
        performance: Performance metrics
        query: Database query details
    """
    record = logging.LogRecord(
        name=logger.name,
        level=getattr(logging, level.upper()),
        pathname='',
        lineno=0,
        msg=msg,
        args=(),
        exc_info=exc_info
    )
    
    record.data = data or {}
    
    if duration_ms is not None:
        record.duration_ms = duration_ms
        
    if performance is not None:
        record.performance = performance
        
    if query is not None:
        record.query = query
        
    logger.handle(record)

def generate_request_id():
    """Generate a unique request ID"""
    return str(uuid.uuid4())

def set_request_id(request_id: str = None):
    """Set the request ID for the current context"""
    if not request_id:
        request_id = generate_request_id()
    request_id_context.set(request_id)
    return request_id

def get_request_id() -> str:
    """Get the request ID for the current context"""
    return request_id_context.get('')

def set_user_id(user_id: int):
    """Set the user ID for the current context"""
    user_id_context.set(user_id)
    
def get_user_id() -> Optional[int]:
    """Get the user ID for the current context"""
    return user_id_context.get(None)

def set_company_id(company_id: int):
    """Set the company ID for the current context"""
    company_id_context.set(company_id)
    
def get_company_id() -> Optional[int]:
    """Get the company ID for the current context"""
    return company_id_context.get(None)

# Add specialized logging functions for common patterns
def log_api_request(logger, endpoint: str, method: str, params: Dict = None, user_id: int = None):
    """Log an API request with standardized format"""
    log_with_context(
        logger, 
        "INFO", 
        f"API Request: {method} {endpoint}",
        data={
            "endpoint": endpoint,
            "method": method,
            "params": params or {},
            "user_id": user_id or get_user_id()
        }
    )

def log_api_response(logger, endpoint: str, method: str, status_code: int, duration_ms: float):
    """Log an API response with standardized format including performance data"""
    log_with_context(
        logger, 
        "INFO", 
        f"API Response: {method} {endpoint} - Status: {status_code}",
        data={
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code
        },
        duration_ms=duration_ms
    )

def log_database_operation(logger, operation: str, table: str, duration_ms: float, query: str = None):
    """Log a database operation with standardized format"""
    log_with_context(
        logger, 
        "DEBUG", 
        f"DB {operation}: {table}",
        data={
            "operation": operation,
            "table": table,
        },
        duration_ms=duration_ms,
        query=query
    )

def log_security_event(logger, event_type: str, user_id: int = None, message: str = None, data: Dict = None):
    """Log a security-related event (login, logout, access denied, etc.)"""
    log_with_context(
        logger, 
        "INFO" if event_type in ["login", "logout"] else "WARNING", 
        f"Security: {event_type}" + (f" - {message}" if message else ""),
        data={
            "security_event": event_type,
            "user_id": user_id or get_user_id(),
            **(data or {})
        }
    )

def log_business_event(logger, event_type: str, details: Dict = None):
    """Log a business event (expense created, category updated, etc.)"""
    log_with_context(
        logger, 
        "INFO", 
        f"Business Event: {event_type}",
        data={
            "event_type": event_type,
            "user_id": get_user_id(),
            "company_id": get_company_id(),
            **(details or {})
        }
    ) 