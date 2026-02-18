"""
MNO File Validator - Base validation classes
"""
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable
from datetime import datetime


class BaseValidator:
    """Base class for all validators"""
    
    def __init__(self, log_callback: Optional[Callable] = None):
        self.log_callback = log_callback
        self.batch_tracking = {}
    
    def set_log_callback(self, callback: Callable):
        """Set the logging callback"""
        self.log_callback = callback
    
    def log(self, message: str, level: str = "INFO"):
        """Log message using callback"""
        if self.log_callback:
            self.log_callback(message, level)
    
    def clear_tracking(self):
        """Clear batch tracking data"""
        self.batch_tracking.clear()


class ValidationResult:
    """Standardized validation result container"""
    
    def __init__(self, success: bool, message: str, errors: List[str] = None):
        self.success = success
        self.message = message
        self.errors = errors or []
    
    def to_tuple(self) -> Tuple[bool, str, List[str]]:
        return self.success, self.message, self.errors