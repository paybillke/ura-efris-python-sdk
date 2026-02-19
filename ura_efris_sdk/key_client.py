import os
import time
import json
import base64
import requests
from datetime import datetime
from typing import Optional, Any
from .utils import (
    load_private_key_from_pfx,
    decrypt_rsa_pkcs1,
    build_unencrypted_request,
    unwrap_response,
    get_uganda_timestamp
)
from .exceptions import AuthenticationException, ApiException, EncryptionException


class KeyClient:
    """
    Manages RSA private key + AES key lifecycle per URA v1.5 spec.
    - Loads .pfx certificate with password (page 21, Offline Guide)
    - Fetches AES key via T104 (valid 24h, page 8)
    - Provides signing + decryption utilities
    """
    
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
        timeout: int = 30
    ):
        self.pfx_path = pfx_path
        self.password = password
        self.tin = tin
        self.device_no = device_no
        self.brn = brn
        self.sandbox = sandbox
        self.timeout = timeout
        
        self._private_key: Optional[Any] = None
        self._aes_key: Optional[bytes] = None
        self._aes_key_fetched_at: Optional[float] = None
        self._aes_key_ttl_seconds = 24 * 60 * 60  # 24 hours per URA v1.5 (page 8)
        
    def _get_endpoint(self) -> str:
        return self.T104_ENDPOINT_TEST if self.sandbox else self.T104_ENDPOINT_PROD
    
    def _load_private_key(self) -> Any:
        """Load RSA private key from .pfx (cached)"""
        if self._private_key is None:
            if not os.path.exists(self.pfx_path):
                raise AuthenticationException(f"PFX file not found: {self.pfx_path}")
            with open(self.pfx_path, "rb") as f:
                pfx_data = f.read()
            self._private_key = load_private_key_from_pfx(pfx_data, self.password)
        return self._private_key
    
    def fetch_aes_key(self, force: bool = False) -> bytes:
        """
        Fetch AES key via T104 interface (URA v1.5, page 8).
        Key is cached for 24h. Use force=True to refresh.
        """
        # Return cached key if valid
        if not force and self._aes_key and self._aes_key_fetched_at:
            if time.time() - self._aes_key_fetched_at < self._aes_key_ttl_seconds:
                return self._aes_key
        
        # Fetch new key via T104
        private_key = self._load_private_key()
        
        # Build T104 request (unencrypted for initial key fetch)
        payload = build_unencrypted_request(
            content={},
            interface_code="T104",
            tin=self.tin,
            device_no=self.device_no,
            brn=self.brn
        )
        
        # Send request
        url = self._get_endpoint()
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise ApiException(
                f"T104 HTTP {response.status_code}: {response.text}",
                status_code=response.status_code
            )
        
        resp_json = response.json()
        
        # Validate response
        return_state = resp_json.get("returnStateInfo", {})
        if return_state.get("returnMessage") != "SUCCESS":
            raise ApiException(
                f"T104 failed: {return_state.get('returnMessage')}",
                error_code=return_state.get("returnCode")
            )
        
        # Extract and decrypt AES key (URA v1.5, page 8)
        try:
            content_b64 = resp_json["data"]["content"]
            content_json = json.loads(base64.b64decode(content_b64).decode())
            encrypted_aes_b64 = content_json["passowrdDes"]  # Note: URA typo "passowrdDes"
            encrypted_aes = base64.b64decode(encrypted_aes_b64)
            
            aes_key = decrypt_rsa_pkcs1(encrypted_aes, private_key)
            
            # Cache the key
            self._aes_key = aes_key
            self._aes_key_fetched_at = time.time()
            
            return aes_key
            
        except Exception as e:
            raise AuthenticationException(f"Failed to extract AES key from T104: {e}")
    
    def sign_payload(self, data: bytes) -> str:
        """Sign data with RSA-SHA1 (URA requirement)"""
        private_key = self._load_private_key()
        from .utils import sign_rsa_sha1
        return sign_rsa_sha1(data, private_key)
    
    def forget_aes_key(self):
        """Force re-fetch of AES key on next call"""
        self._aes_key = None
        self._aes_key_fetched_at = None
    
    @property
    def aes_key_valid_until(self) -> Optional[str]:
        """Get human-readable expiry time for cached AES key"""
        if not self._aes_key_fetched_at:
            return None
        expiry = self._aes_key_fetched_at + self._aes_key_ttl_seconds
        return datetime.fromtimestamp(expiry).strftime("%Y-%m-%d %H:%M:%S")