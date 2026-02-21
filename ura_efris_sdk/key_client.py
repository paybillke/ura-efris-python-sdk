"""
EFRIS Key Client
Manages cryptographic keys (PFX, AES) for secure API communication.
Handles key retrieval, caching, and cryptographic operations.
"""
import os
import time
import json
import base64
import requests
import logging
from datetime import datetime
from typing import Optional, Any
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from .utils import build_unencrypted_request, sign_rsa_sha1
from .exceptions import AuthenticationException, ApiException, EncryptionException

logger = logging.getLogger(__name__)


class KeyClient:
    """
    Manages cryptographic keys for EFRIS API authentication.
    
    Responsibilities:
        - Load and cache PFX private key
        - Fetch and cache AES symmetric key from T104 endpoint
        - Handle key rotation (24-hour TTL)
        - Perform RSA signing operations
    
    Note: This implementation uses local PFX files rather than the
    T102 Whitebox key provisioning described in the API documentation.
    """
    
    # EFRIS API endpoints (FIXED: removed trailing spaces)
    T104_ENDPOINT_TEST = "https://efristest.ura.go.ug/efrisws/ws/taapp/getInformation"
    T104_ENDPOINT_PROD = "https://efrisws.ura.go.ug/ws/taapp/getInformation"
    
    def __init__(
        self,
        pfx_path: str,
        password: str,
        tin: str,
        device_no: str,
        brn: str = "",
        sandbox: bool = True,
        timeout: int = 30,
        taxpayer_id: str = "1"  # Default, updated from sign_in response
    ):
        """
        Initialize KeyClient with authentication credentials.
        
        Args:
            pfx_path: Path to PFX certificate file
            password: PFX file password
            tin: Taxpayer Identification Number
            device_no: Device serial number
            brn: Business Registration Number
            sandbox: Use sandbox environment
            timeout: HTTP request timeout in seconds
        """
        self.pfx_path = pfx_path
        self.password = password
        self.tin = tin
        self.device_no = device_no
        self.brn = brn
        self.sandbox = sandbox
        self.timeout = timeout
        self.taxpayer_id = taxpayer_id  # ← Make this configurable if needed
        
        # Cached cryptographic objects
        self._private_key: Optional[Any] = None
        self._aes_key: Optional[bytes] = None
        self._aes_key_fetched_at: Optional[float] = None
        self._aes_key_ttl_seconds = 23 * 60 * 60  # 23 hours (refresh before 24h expiry)
        self._aes_key_content_json: Optional[dict] = None
    
    def _get_endpoint(self) -> str:
        """Get the appropriate API endpoint based on environment."""
        return self.T104_ENDPOINT_TEST if self.sandbox else self.T104_ENDPOINT_PROD
    
    def _load_private_key(self) -> Any:
        """Load and cache the RSA private key from PFX file."""
        if self._private_key is None:
            if not os.path.exists(self.pfx_path):
                raise AuthenticationException(f"PFX file not found: {self.pfx_path}")
            
            with open(self.pfx_path, "rb") as f:
                pfx_data = f.read()
            
            try:
                private_key, _, _ = pkcs12.load_key_and_certificates(
                    pfx_data,
                    self.password.encode() if self.password else b"",
                    backend=default_backend()
                )
            except Exception as e:
                logger.error(f"Failed to load PFX: {e}")
                raise AuthenticationException(f"Failed to load PFX: {e}")
            
            if private_key is None:
                raise AuthenticationException("Private key extraction failed")
            
            # ✅ FIXED: Wrap fingerprint in try/except for compatibility
            try:
                from cryptography.hazmat.primitives import hashes
                fingerprint = private_key.public_key().fingerprint(hashes.SHA256())
                logger.info(f"Loaded private key with fingerprint: {fingerprint.hex()}")
            except AttributeError:
                # Fallback for older cryptography versions or Python 3.14 compatibility
                logger.info("Loaded private key (fingerprint logging skipped for compatibility)")
            except Exception as e:
                logger.debug(f"Could not log key fingerprint: {e}")
            
            self._private_key = private_key
        
        return self._private_key

    def fetch_aes_key(self, force: bool = False) -> Optional[bytes]:
        """
        Fetch AES symmetric key from T104 endpoint.
        Key is cached for 23 hours to reduce API calls.
        
        Process:
            1. Check if cached key is still valid
            2. Call T104 endpoint to get encrypted AES key
            3. Decrypt AES key using RSA private key
            4. Derive proper-length AES key from 8-byte seed if needed
            5. Cache the derived key
        
        Args:
            force: Force refresh even if cached key is valid
        
        Returns:
            bytes: AES symmetric key (16/24/32 bytes) or None if fetch fails
        
        Raises:
            ApiException: If T104 request fails
            EncryptionException: If key decryption fails
        """
        # Return cached key if still valid
        if not force and self._aes_key and self._aes_key_fetched_at:
            elapsed = time.time() - self._aes_key_fetched_at
            if elapsed < self._aes_key_ttl_seconds:
                logger.debug("Using cached AES key")
                return self._aes_key
        
        logger.info("Fetching AES symmetric key from T104 endpoint")
        
        # Load RSA private key for decryption
        private_key = self._load_private_key()
        
        # Build T104 request (unencrypted, but content must be base64-encoded)
        payload = build_unencrypted_request(
            content={},
            interface_code="T104",
            tin=self.tin,
            device_no=self.device_no,
            brn=self.brn,
            taxpayer_id=self.taxpayer_id
        )
        
        # Call T104 endpoint
        url = self._get_endpoint()
        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
        except requests.RequestException as e:
            logger.error(f"T104 connection error: {e}")
            raise ApiException(f"T104 connection error: {e}")
        
        if response.status_code != 200:
            logger.error(f"T104 HTTP {response.status_code}: {response.text}")
            raise ApiException(
                f"T104 HTTP {response.status_code}: {response.text}",
                status_code=response.status_code
            )
        
        try:
            resp_json = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in T104 response: {e}")
            raise ApiException(f"Invalid JSON in T104 response: {e}")
        
        return_state = resp_json.get("returnStateInfo", {})
        
        # Check for T104 errors
        if return_state.get("returnMessage") != "SUCCESS":
            error_msg = return_state.get("returnMessage", "Unknown error")
            error_code = return_state.get("returnCode", "99")
            logger.error(f"T104 failed: {error_msg} (code: {error_code})")
            raise ApiException(
                f"T104 failed: {error_msg}",
                error_code=error_code
            )
        
        # Extract and decrypt AES key
        try:
            content_b64 = resp_json.get("data", {}).get("content", "")
            if not content_b64:
                raise EncryptionException("Missing content in T104 response")
            
            content_json = json.loads(base64.b64decode(content_b64).decode())
            logger.debug(f"T104 response content keys: {list(content_json.keys())}")
            
            # Handle API typo: "passowrdDes" instead of "passwordDes"
            encrypted_aes_b64 = (
                content_json.get("passowrdDes") or
                content_json.get("passwordDes")
            )
            
            if not encrypted_aes_b64:
                logger.error(f"Missing AES key field. Available keys: {list(content_json.keys())}")
                raise EncryptionException("Missing AES key field in T104 response")
            
            encrypted_aes = base64.b64decode(encrypted_aes_b64)
            logger.debug(f"Encrypted AES key length: {len(encrypted_aes)} bytes")
            
            # Decrypt AES key using RSA-PKCS1v1.5 with cryptography library
            # This matches the utils.py sign_rsa_sha1 implementation
            aes_key_raw = private_key.decrypt(
                encrypted_aes,
                asym_padding.PKCS1v15()
            )
            
            logger.debug(f"Decrypted AES key raw length: {len(aes_key_raw)} bytes")
            
            # The decrypted result may be:
            # 1. Raw 8-byte key (per API spec)
            # 2. Base64-encoded key that needs decoding
            # 3. Already proper-length key
            
            # Try to decode as base64 first (common pattern)
            try:
                aes_key_candidate = base64.b64decode(aes_key_raw)
                logger.debug(f"After base64 decode: {len(aes_key_candidate)} bytes")
            except Exception:
                aes_key_candidate = aes_key_raw
            
            # Derive proper-length AES key if needed
            # EFRIS may return 8-byte seed; derive to 16/24/32 bytes
            if len(aes_key_candidate) == 8:
                # Derive 16-byte AES key from 8-byte seed using simple expansion
                # Note: In production, use proper KDF like HKDF
                seed = aes_key_candidate
                aes_key = (seed + seed)[:16]  # Simple expansion to 16 bytes
                logger.info("Derived 16-byte AES key from 8-byte seed")
            elif len(aes_key_candidate) in (16, 24, 32):
                aes_key = aes_key_candidate
                logger.info(f"Using AES key with valid length: {len(aes_key)} bytes")
            else:
                # Try to use first 16 bytes as fallback
                aes_key = aes_key_candidate[:16]
                logger.warning(f"Using truncated AES key: {len(aes_key)} bytes from {len(aes_key_candidate)}")
            
            # Final validation
            if len(aes_key) not in (16, 24, 32):
                raise EncryptionException(
                    f"Cannot use AES key of length {len(aes_key)} bytes"
                )
            
            # Cache the key
            self._aes_key = aes_key
            self._aes_key_fetched_at = time.time()
            self._aes_key_content_json = content_json
            
            logger.info("AES key fetched and cached successfully")
            return aes_key
        
        except EncryptionException:
            raise
        except Exception as e:
            logger.error(f"Failed to extract AES key: {e}", exc_info=True)
            raise EncryptionException(f"Failed to extract AES key: {e}")    
    def get_aes_key(self) -> Optional[bytes]:
        """Get the currently cached AES key without fetching."""
        return self._aes_key
    
    def forget_aes_key(self):
        """Clear cached AES key (forces refresh on next use)."""
        logger.debug("Clearing cached AES key")
        self._aes_key = None
        self._aes_key_fetched_at = None
        self._aes_key_content_json = None
    
    @property
    def aes_key_valid_until(self) -> Optional[str]:
        """
        Get the expiry timestamp of the cached AES key.
        
        Returns:
            str: Expiry timestamp or None if no key cached
        """
        if not self._aes_key_fetched_at:
            return None
        expiry = self._aes_key_fetched_at + self._aes_key_ttl_seconds
        return datetime.fromtimestamp(expiry).strftime("%Y-%m-%d %H:%M:%S")
    
    def is_aes_key_valid(self) -> bool:
        """Check if cached AES key is still valid."""
        if not self._aes_key or not self._aes_key_fetched_at:
            return False
        return time.time() - self._aes_key_fetched_at < self._aes_key_ttl_seconds