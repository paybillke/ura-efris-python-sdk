"""
EFRIS Client Exception Classes
Defines custom exceptions for handling various error scenarios in the EFRIS API client.
"""
from typing import Optional, Dict, Any


class EfrisException(Exception):
    """
    Base exception class for all EFRIS-related errors.
    Provides standardized error handling with status codes and error details.
    """
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
        """Format exception string with error code if available."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ApiException(EfrisException):
    """
    Raised when the EFRIS API returns an error response.
    Used for HTTP errors and API-level failures.
    """
    pass


class ValidationException(EfrisException):
    """
    Raised when payload validation fails against Pydantic schemas.
    Contains detailed field-level validation errors.
    """
    def __init__(
        self,
        message: str = "Validation failed",
        errors: Optional[Dict[str, str]] = None
    ):
        super().__init__(message, status_code=400)
        self.errors = errors or {}

    def __str__(self):
        """Format validation errors as field: message pairs."""
        if self.errors:
            error_msgs = "; ".join(
                f"{field}: {msg}" for field, msg in self.errors.items()
            )
            return f"{self.message}: {error_msgs}"
        return self.message


class EncryptionException(EfrisException):
    """
    Raised when encryption or decryption operations fail.
    Covers RSA, AES, and key management errors.
    """
    pass


class AuthenticationException(EfrisException):
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