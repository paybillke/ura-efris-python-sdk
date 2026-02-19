from typing import Optional, Dict, Any


class EfrisException(Exception):
    """Base exception for EFRIS SDK"""
    
    def __init__(
        self,
        message: str = "EFRIS error",
        status_code: int = 400,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ApiException(EfrisException):
    """Raised for API-level errors (HTTP status, returnStateInfo)"""
    pass


class ValidationException(EfrisException):
    """Raised for payload validation errors (Pydantic)"""
    
    def __init__(self, message: str = "Validation failed", errors: Optional[Dict[str, str]] = None):
        super().__init__(message, status_code=400)
        self.errors = errors or {}
    
    def __str__(self):
        if self.errors:
            error_msgs = "; ".join(f"{field}: {msg}" for field, msg in self.errors.items())
            return f"{self.message}: {error_msgs}"
        return self.message


class EncryptionException(EfrisException):
    """Raised for encryption/decryption/signing errors"""
    pass


class AuthenticationException(EfrisException):
    """Raised for certificate/key authentication failures"""
    
    def __init__(self, message: str = "Authentication failed", status_code: int = 401):
        super().__init__(message, status_code=status_code)