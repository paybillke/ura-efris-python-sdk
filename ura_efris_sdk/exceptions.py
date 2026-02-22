"""
EFRIS Custom Exceptions
"""
from typing import Dict, Optional, List


class EFRISException(Exception):
    """Base exception for EFRIS"""
    def __init__(self, message: str, error_type: str = "UNKNOWN"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


class ValidationException(EFRISException):
    """Validation error with field-level details"""
    def __init__(
        self, 
        message: str, 
        errors: Dict[str, str], 
        error_type: str = "VALIDATION_ERROR"
    ):
        self.errors = errors
        super().__init__(message, error_type)
    
    def __str__(self):
        return f"{self.message}: {self.errors}"
    
    def get_field_error(self, field_path: str) -> Optional[str]:
        """Get error message for specific field"""
        return self.errors.get(field_path)
    
    def has_errors(self) -> bool:
        """Check if there are any validation errors"""
        return len(self.errors) > 0


class APIException(EFRISException):
    """API communication error"""
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        return_code: Optional[str] = None,
        error_type: str = "API_ERROR"
    ):
        self.status_code = status_code
        self.return_code = return_code
        super().__init__(message, error_type)


class EncryptionException(EFRISException):
    """Encryption/decryption error"""
    def __init__(self, message: str, error_type: str = "ENCRYPTION_ERROR"):
        super().__init__(message, error_type)


class SchemaNotFoundException(EFRISException):
    """Schema not found in registry"""
    def __init__(self, schema_key: str):
        super().__init__(
            f"Schema '{schema_key}' not found in registry",
            "SCHEMA_NOT_FOUND"
        )

class AuthenticationException(EFRISException):
    """
    Raised when authentication fails (e.g., invalid PFX, wrong password).
    Uses HTTP 401 status code by default.
    """
    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: int = 401
    ):
        super().__init__(message, status_code=status_code)