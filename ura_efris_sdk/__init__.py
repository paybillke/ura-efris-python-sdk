"""
Uganda EFRIS SDK - eTIMS Style Architecture
Compliant with URA Integration Requirements v1.5
"""
from .base_client import BaseClient
from .key_client import KeyClient
from .client import Client
from .validator import Validator
from .utils import (
    encrypt_aes_ecb,
    decrypt_aes_ecb,
    sign_rsa_sha1,
    load_private_key_from_pfx,
    get_uganda_timestamp,
    build_encrypted_request,
    unwrap_response
)
from .exceptions import (
    Exception,
    ApiException,
    ValidationException,
    EncryptionException,
    AuthenticationException
)
from .config import load_config_from_env, validate_config

__all__ = [
    # Clients
    "BaseClient",
    "KeyClient", 
    "OClient",
    "Validator",
    
    # Utilities
    "encrypt_aes_ecb",
    "decrypt_aes_ecb",
    "sign_rsa_sha1",
    "load_private_key_from_pfx",
    "get_uganda_timestamp",
    "build_encrypted_request",
    "unwrap_response",
    
    # Exceptions
    "Exception",
    "ApiException",
    "ValidationException",
    "EncryptionException",
    "AuthenticationException",
    
    # Config
    "load_config_from_env",
    "validate_config",
]

__version__ = "0.1.0"