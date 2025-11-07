"""Error handling utilities for FSR Injector."""

import traceback
import sys
from functools import wraps
from typing import Callable, Optional, Any

class FSRError(Exception):
    """Base exception class for FSR Injector errors."""
    pass

# Alias for compatibility
FSRException = FSRError

class ConfigurationError(FSRError):
    """Raised when there is an error in configuration."""
    pass

class ModInstallationError(FSRError):
    """Raised when mod installation fails."""
    pass

class ModUninstallationError(FSRError):
    """Raised when mod uninstallation fails."""
    pass

class FileOperationError(FSRError):
    """Raised when a file operation fails."""
    pass

class PathNotFoundError(FSRError):
    """Raised when a required path is not found."""
    pass

def error_handler(logger: Optional[Callable] = None) -> Callable:
    """Decorator for handling errors in functions.
    
    Args:
        logger: Optional logging function to use for error messages
        
    Returns:
        Decorator function that handles errors
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except FSRError as e:
                # Handle known application errors
                error_msg = str(e)
                if logger:
                    logger('ERROR', error_msg)
                return None
            except Exception as e:
                # Handle unexpected errors
                error_msg = f"Unexpected error in {func.__name__}: {str(e)}"
                if logger:
                    logger('ERROR', error_msg)
                    logger('ERROR', f"Stack trace:\n{''.join(traceback.format_tb(e.__traceback__))}")
                return None
        return wrapper
    return decorator

def safe_file_operation(operation: Callable) -> Optional[Any]:
    """Execute a file operation safely with error handling.
    
    Args:
        operation: Function that performs the file operation
        
    Returns:
        Result of the operation if successful, None otherwise
        
    Raises:
        FileOperationError: If the operation fails
    """
    try:
        return operation()
    except PermissionError:
        raise FileOperationError("Permission denied. Ensure you have admin rights or the file is not in use.")
    except FileNotFoundError:
        raise FileOperationError("File not found. Please check the path and try again.")
    except OSError as e:
        raise FileOperationError(f"Operating system error: {e}")
    except Exception as e:
        raise FileOperationError(f"Unexpected error during file operation: {e}")

def validate_path(path: str) -> bool:
    """Validate if a path exists and is accessible.
    
    Args:
        path: Path to validate
        
    Returns:
        bool: True if path is valid, False otherwise
        
    Raises:
        PathNotFoundError: If the path is invalid or inaccessible
    """
    import os
    
    if not path:
        raise PathNotFoundError("Path cannot be empty")
    
    if not os.path.exists(path):
        raise PathNotFoundError(f"Path does not exist: {path}")
        
    try:
        # Test if we can list the directory
        if os.path.isdir(path):
            os.listdir(path)
        # Test if we can read the file
        elif os.path.isfile(path):
            with open(path, 'rb') as f:
                f.read(1)
        return True
    except PermissionError:
        raise PathNotFoundError(f"Permission denied accessing path: {path}")
    except Exception as e:
        raise PathNotFoundError(f"Error accessing path {path}: {e}")

def setup_global_error_handler(logger: Optional[Callable] = None) -> None:
    """Set up global exception handler for unhandled errors.
    
    Args:
        logger: Optional logging function to use for error messages
    """
    def global_handler(exc_type: type, exc_value: Exception, exc_traceback: traceback) -> None:
        # Skip KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        error_msg = f"Unhandled {exc_type.__name__}: {str(exc_value)}"
        trace_msg = ''.join(traceback.format_tb(exc_traceback))
        
        if logger:
            logger('ERROR', error_msg)
            logger('ERROR', f"Stack trace:\n{trace_msg}")
        else:
            print(error_msg, file=sys.stderr)
            print(trace_msg, file=sys.stderr)
            
    sys.excepthook = global_handler